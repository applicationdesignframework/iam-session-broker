import pathlib

import aws_cdk as cdk
import aws_cdk.aws_apigatewayv2_alpha as apigatewayv2_alpha
import aws_cdk.aws_apigatewayv2_authorizers_alpha as apigatewayv2_authorizers_alpha
import aws_cdk.aws_apigatewayv2_integrations_alpha as apigatewayv2_integrations_alpha
import aws_cdk.aws_dynamodb as dynamodb
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_lambda_python_alpha as lambda_python_alpha
from constructs import Construct

import constants


class IAMSessionBroker(Construct):
    _IAM_ROLE_NAME = constants.APP_NAME

    def __init__(self, scope: Construct, id_: str):
        super().__init__(scope, id_)

        dynamodb_table = self._create_dynamodb_table()
        lambda_function = self._create_lambda_function(dynamodb_table)
        api_gateway_http_api = self._create_api_gateway_http_api(lambda_function)
        # Lambda function creates a default execution role.
        iam_role = self._create_iam_role(lambda_function.role)  # type: ignore

        dynamodb_table.grant_read_write_data(lambda_function)

        self.endpoint = api_gateway_http_api.url
        self.iam_role_name = iam_role.role_name

    def _create_dynamodb_table(self) -> dynamodb.Table:
        dynamodb_table = dynamodb.Table(
            self,
            "DynamoDBTable",
            partition_key=dynamodb.Attribute(
                name="ApplicationName", type=dynamodb.AttributeType.STRING
            ),
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        return dynamodb_table

    def _create_lambda_function(
        self, dynamodb_table: dynamodb.Table
    ) -> lambda_.Function:
        lambda_function = lambda_python_alpha.PythonFunction(
            self,
            "LambdaFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            environment={
                # Passing role name because the role is created after the function.
                "ISB_IAM_ROLE_NAME": IAMSessionBroker._IAM_ROLE_NAME,
                "ISB_DYNAMODB_TABLE_NAME": dynamodb_table.table_name,
            },
            entry=str(pathlib.Path(__file__).parent.joinpath("runtime").resolve()),
            index="lambda_function.py",
            handler="lambda_handler",
            timeout=cdk.Duration.seconds(10),
        )
        return lambda_function

    def _create_api_gateway_http_api(
        self, lambda_function: lambda_.Function
    ) -> apigatewayv2_alpha.HttpApi:
        api_gateway_integration = apigatewayv2_integrations_alpha.HttpLambdaIntegration(
            "APIGatewayIntegration", handler=lambda_function
        )
        api_gateway_http_api = apigatewayv2_alpha.HttpApi(
            self,
            "APIGatewayHTTPAPI",
            default_authorizer=apigatewayv2_authorizers_alpha.HttpIamAuthorizer(),
            default_integration=api_gateway_integration,
        )
        return api_gateway_http_api

    def _create_iam_role(self, lambda_function_role: iam.Role) -> iam.Role:
        iam_role = iam.Role(
            self,
            "IAMRole",
            role_name=IAMSessionBroker._IAM_ROLE_NAME,
            assumed_by=lambda_function_role,
        )
        return iam_role
