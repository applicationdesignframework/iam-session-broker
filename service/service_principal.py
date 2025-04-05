import aws_cdk.aws_iam as iam
from constructs import Construct

import constants


class ServicePrincipal(Construct):
    def __init__(
        self, scope: Construct, id_: str, *, api_compute_lambda_function_role: iam.IRole
    ):
        super().__init__(scope, id_)

        self.iam_role = iam.Role(
            self,
            "IAMRole",
            role_name=constants.APP_NAME,
            assumed_by=api_compute_lambda_function_role,
        )
