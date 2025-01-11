import aws_cdk.aws_apigatewayv2_alpha as apigatewayv2_alpha
import aws_cdk.aws_apigatewayv2_authorizers_alpha as apigatewayv2_authorizers_alpha
import aws_cdk.aws_apigatewayv2_integrations_alpha as apigatewayv2_integrations_alpha
import aws_cdk.aws_lambda as lambda_
from constructs import Construct


class APIGateway(Construct):
    def __init__(
        self, scope: Construct, id_: str, *, lambda_function: lambda_.IFunction
    ):
        super().__init__(scope, id_)

        api_gateway_integration = apigatewayv2_integrations_alpha.HttpLambdaIntegration(
            "APIGatewayIntegration", handler=lambda_function
        )
        self.api_gateway_http_api = apigatewayv2_alpha.HttpApi(
            self,
            "APIGatewayHTTPAPI",
            default_authorizer=apigatewayv2_authorizers_alpha.HttpIamAuthorizer(),
            default_integration=api_gateway_integration,
        )
