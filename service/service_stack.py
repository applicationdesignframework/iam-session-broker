from typing import Any

import aws_cdk as cdk
from constructs import Construct

from iam_session_broker import IAMSessionBroker


class ServiceStack(cdk.Stack):
    def __init__(self, scope: Construct, id_: str, **kwargs: Any):
        super().__init__(scope, id_, **kwargs)

        iam_session_broker = IAMSessionBroker(self, "IAMSessionBroker")

        # API Gateway HTTP API create_default_stage is enabled, URL will be defined
        cdk.CfnOutput(self, "IAMSessionBroker-Endpoint", value=iam_session_broker.endpoint)  # type: ignore
        cdk.CfnOutput(
            self, "IAMSessionBroker-IAMRoleName", value=iam_session_broker.iam_role_name
        )
