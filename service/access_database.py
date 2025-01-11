import aws_cdk as cdk
import aws_cdk.aws_dynamodb as dynamodb
from constructs import Construct


class AccessDatabase(Construct):
    def __init__(self, scope: Construct, id_: str):
        super().__init__(scope, id_)

        self.dynamodb_table = dynamodb.Table(
            self,
            "DynamoDBTable",
            partition_key=dynamodb.Attribute(
                name="ApplicationName", type=dynamodb.AttributeType.STRING
            ),
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
