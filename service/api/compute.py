import pathlib

import aws_cdk as cdk
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_lambda_python_alpha as lambda_python_alpha
from constructs import Construct

import constants


class Compute(Construct):
    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        access_database_dynamodb_table_name: str,
    ):
        super().__init__(scope, id_)

        self.lambda_function = lambda_python_alpha.PythonFunction(
            self,
            "LambdaFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            environment={
                # Passing role name because the role is created after the function.
                "ISB_SERVICE_PRINCIPAL_IAM_ROLE_NAME": constants.APP_NAME,
                "ISB_ACCESS_DATABASE_DYNAMODB_TABLE_NAME": access_database_dynamodb_table_name,
            },
            entry=str(pathlib.Path(__file__).parent.joinpath("app").resolve()),
            index="main.py",
            handler="lambda_handler",
            timeout=cdk.Duration.seconds(10),
        )
