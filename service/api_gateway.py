import aws_cdk.aws_apigatewayv2 as apigatewayv2
import aws_cdk.aws_apigatewayv2_authorizers as apigatewayv2_authorizers
import aws_cdk.aws_apigatewayv2_integrations as apigatewayv2_integrations
import aws_cdk.aws_lambda as lambda_
from constructs import Construct


class APIGateway(Construct):
    def __init__(
        self, scope: Construct, id_: str, *, lambda_function: lambda_.IFunction
    ):
        super().__init__(scope, id_)

        api_gateway_integration = apigatewayv2_integrations.HttpLambdaIntegration(
            "APIGatewayIntegration", handler=lambda_function
        )
        self.api_gateway_http_api = apigatewayv2.HttpApi(
            self,
            "APIGatewayHTTPAPI",
            default_authorizer=apigatewayv2_authorizers.HttpIamAuthorizer(),
            default_integration=api_gateway_integration,
        )
