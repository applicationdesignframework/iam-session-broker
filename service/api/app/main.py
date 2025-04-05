import os
from http import HTTPStatus
from typing import Any, Callable

import boto3
import jwt
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools.event_handler import exceptions
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_sts import STSClient
from mypy_boto3_sts.type_defs import AssumeRoleResponseTypeDef

import helpers

app = APIGatewayHttpResolver()


@lambda_handler_decorator
def account_authorizer(
    handler: Callable[..., dict[str, Any]],
    event: dict[str, Any],
    context: LambdaContext,
) -> dict[str, Any]:
    """Authorizes application service principals from the same account.

    Related documentation:
    https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-mapping-template-reference.html#context-variable-reference
    """
    application_account = event["requestContext"]["authorizer"]["iam"]["accountId"]
    current_account = event["requestContext"]["accountId"]

    if application_account != current_account:
        raise exceptions.UnauthorizedError("Cross-account access is not allowed")
    response = handler(event, context)
    return response


@account_authorizer
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    return app.resolve(event, context)


@app.post("/applications")
def register_application() -> Response:  # type: ignore
    application_name = _get_application_name()

    access_repository = helpers.init_access_repository()
    if access_repository.get_access_metadata(application_name) is not None:
        raise exceptions.BadRequestError(
            f"Application {application_name} already exists"
        )
    access_repository.register_application(
        application_name,
        app.current_event.json_body["AccessPrincipalRoleName"],
        app.current_event.json_body["SessionTagKey"],
        app.current_event.json_body["JWTClaimName"],
        app.current_event.json_body["JWKSetURL"],
    )

    return Response(status_code=HTTPStatus.CREATED)


@app.delete("/applications")
def delete_application() -> Response:  # type: ignore
    application_name = _get_application_name()

    access_repository = helpers.init_access_repository()
    if access_repository.get_access_metadata(application_name) is None:
        raise exceptions.NotFoundError(f"Application {application_name} does not exist")
    access_repository.delete_application(application_name)

    return Response(status_code=HTTPStatus.OK)


@app.get("/credentials")
def get_credentials() -> dict[str, Any]:
    """Returns scoped temporary security credentials.

    Assumes the access principal role registered for the application.
    Tags the session using the registered session tag key and JWT claim name value.
    """
    account = app.current_event.request_context.account_id
    application_name = _get_application_name()
    access_metadata = _get_access_metadata(application_name)

    isb_service_principal_sts_client = _get_isb_service_principal_sts_client(account)
    response = _assume_app_access_principal_role(
        isb_service_principal_sts_client, account, access_metadata
    )
    # We don't need to return "Expiration" and it also not JSON serializable.
    credentials = {
        key: value
        for key, value in response["Credentials"].items()
        if key != "Expiration"
    }

    return credentials


def _get_application_name() -> str:
    unauthorized_error_message = "Cannot authenticate the application"

    authorizer = app.current_event.request_context.authorizer
    if authorizer is None:
        raise exceptions.UnauthorizedError(unauthorized_error_message)
    iam_authorizer = authorizer.iam
    if iam_authorizer is None:
        raise exceptions.UnauthorizedError(unauthorized_error_message)
    user_arn = iam_authorizer.user_arn
    if user_arn is None:
        raise exceptions.UnauthorizedError(unauthorized_error_message)

    # Use service principal role name as application name.
    # arn:aws:sts::111111111111:assumed-role/<service principal role name>/<session name>
    application_name = user_arn.split("/")[1]

    return application_name


def _get_access_metadata(application_name: str) -> dict[str, Any]:
    access_repository = helpers.init_access_repository()
    access_metadata = access_repository.get_access_metadata(application_name)
    if access_metadata is None:
        raise exceptions.NotFoundError(f"Application {application_name} does not exist")
    return access_metadata


def _get_isb_service_principal_sts_client(account: str) -> STSClient:
    sts_client = boto3.client("sts")

    isb_service_principal_iam_role_name = os.environ[
        "ISB_SERVICE_PRINCIPAL_IAM_ROLE_NAME"
    ]
    isb_service_principal_iam_role_arn = (
        f"arn:aws:iam::{account}:role/{isb_service_principal_iam_role_name}"
    )
    response = sts_client.assume_role(
        RoleArn=isb_service_principal_iam_role_arn,
        RoleSessionName="API",
    )
    credentials = response["Credentials"]

    isb_service_principal_sts_client = boto3.client(
        "sts",
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )

    return isb_service_principal_sts_client


def _assume_app_access_principal_role(
    isb_service_principal_sts_client: STSClient,
    account: str,
    access_metadata: dict[str, Any],
) -> AssumeRoleResponseTypeDef:
    jwt_ = app.current_event.get_query_string_value(name="jwt")
    if jwt_ is None:
        raise exceptions.BadRequestError("Missing jwt parameter")
    jwt_claims = _verify_jwt(jwt_, access_metadata["JWKSetURL"])

    access_principal_role_name = access_metadata["AccessPrincipalRoleName"]
    access_role_arn = f"arn:aws:iam::{account}:role/{access_principal_role_name}"
    session_tag_key = access_metadata["SessionTagKey"]
    session_tag_value = jwt_claims[access_metadata["JWTClaimName"]]

    response = isb_service_principal_sts_client.assume_role(
        RoleArn=access_role_arn,
        RoleSessionName="IAMSessionBroker",
        Tags=[
            {
                "Key": session_tag_key,
                "Value": session_tag_value,
            }
        ],
    )

    return response


def _verify_jwt(jwt_: str, jwk_set_url: str) -> Any:
    try:
        jwt_claims = helpers.verify_jwt(jwt_, jwk_set_url)
    except jwt.PyJWTError as error:
        raise exceptions.UnauthorizedError(f"Could not verify JWT: {error}")

    return jwt_claims
