import os
from typing import Any

import jwt

import access_database


def init_access_repository() -> access_database.AccessRepository:
    dynamodb_database = access_database.DynamoDBDatabase(
        os.environ["ISB_ACCESS_DATABASE_DYNAMODB_TABLE_NAME"]
    )
    access_repository = access_database.AccessRepository(database=dynamodb_database)
    return access_repository


def verify_jwt(jwt_: str, jwk_set_url: str) -> Any:
    jwk_client = jwt.PyJWKClient(jwk_set_url)
    signing_key = jwk_client.get_signing_key_from_jwt(jwt_)
    claims = jwt.decode(
        jwt_, signing_key.key, options={"verify_aud": False}, algorithms=["RS256"]
    )
    return claims
