import os

import aws_cdk as cdk

import constants
from service.service_stack import ServiceStack

app = cdk.App()

ServiceStack(
    app,
    f"{constants.APP_NAME}-Service-Sandbox",
    env=cdk.Environment(
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
        region=os.environ["CDK_DEFAULT_REGION"],
    ),
)

app.synth()
