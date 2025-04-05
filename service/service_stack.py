from typing import Any, cast

import aws_cdk as cdk
import aws_cdk.aws_iam as iam
from constructs import Construct

from service.access_database import AccessDatabase
from service.api.compute import Compute as APICompute
from service.api_gateway import APIGateway
from service.service_principal import ServicePrincipal


class ServiceStack(cdk.Stack):
    def __init__(self, scope: Construct, id_: str, **kwargs: Any):
        super().__init__(scope, id_, **kwargs)

        access_database = AccessDatabase(self, "AccessDatabase")
        api_compute = APICompute(
            self,
            "APICompute",
            access_database_dynamodb_table_name=access_database.dynamodb_table.table_name,
        )
        api_gateway = APIGateway(
            self, "APIGateway", lambda_function=api_compute.lambda_function
        )
        service_principal = ServicePrincipal(
            self,
            "ServicePrincipal",
            api_compute_lambda_function_role=cast(
                iam.IRole, api_compute.lambda_function.role
            ),
        )

        access_database.dynamodb_table.grant_read_write_data(
            api_compute.lambda_function
        )

        # API Gateway HTTP API create_default_stage configuration is enabled,
        # hence `url` attribute will have a defined value.
        api_endpoint = api_gateway.api_gateway_http_api.url
        service_principal_role_name = service_principal.iam_role.role_name

        cdk.CfnOutput(self, "APIEndpoint", value=cast(str, api_endpoint))
        cdk.CfnOutput(
            self, "ServicePrincipalRoleName", value=service_principal_role_name
        )
