import abc
from typing import Any, Optional

import boto3


class DatabaseInterface(abc.ABC):
    @abc.abstractmethod
    def register_application(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        application_name: str,
        access_principal_role_name: str,
        session_tag_key: str,
        jwt_claim_name: str,
        jwk_set_url: str,
    ) -> None:
        pass

    @abc.abstractmethod
    def delete_application(self, application_name: str) -> None:
        pass

    @abc.abstractmethod
    def get_access_metadata(self, application_name: str) -> Optional[dict[str, Any]]:
        pass


class AccessRepository:
    def __init__(self, *, database: DatabaseInterface):
        self._database = database

    def register_application(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        application_name: str,
        access_principal_role_name: str,
        session_tag_key: str,
        jwt_claim_name: str,
        jwk_set_url: str,
    ) -> None:
        self._database.register_application(
            application_name,
            access_principal_role_name,
            session_tag_key,
            jwt_claim_name,
            jwk_set_url,
        )

    def delete_application(self, application_name: str) -> None:
        self._database.delete_application(application_name)

    def get_access_metadata(self, application_name: str) -> Optional[dict[str, Any]]:
        return self._database.get_access_metadata(application_name)


class DynamoDBDatabase(DatabaseInterface):
    _dynamodb = boto3.resource("dynamodb")

    def __init__(self, table_name: str):
        super().__init__()
        self._table = DynamoDBDatabase._dynamodb.Table(table_name)

    def register_application(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        application_name: str,
        access_principal_role_name: str,
        session_tag_key: str,
        jwt_claim_name: str,
        jwk_set_url: str,
    ) -> None:
        access_metadata = {
            "ApplicationName": application_name,
            "AccessPrincipalRoleName": access_principal_role_name,
            "SessionTagKey": session_tag_key,
            "JWTClaimName": jwt_claim_name,
            "JWKSetURL": jwk_set_url,
        }
        self._table.put_item(Item=access_metadata)

    def delete_application(self, application_name: str) -> None:
        self._table.delete_item(Key={"ApplicationName": application_name})

    def get_access_metadata(self, application_name: str) -> Optional[dict[str, Any]]:
        response = self._table.get_item(Key={"ApplicationName": application_name})
        return response["Item"] if "Item" in response else None
