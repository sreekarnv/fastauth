from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from cuid2 import cuid_wrapper
from joserfc import jwt
from joserfc.jwk import OctKey

from fastauth.config import FastAuthConfig
from fastauth.types import TokenPair, UserData

cuid_generator: Callable[[], str] = cuid_wrapper()


# TODO: Need to support RSA at a later time.
def create_access_token(user: UserData, config: FastAuthConfig) -> str:
    key = OctKey.import_key(config.secret)
    now = datetime.now(timezone.utc)
    header = {"alg": config.jwt.algorithm}
    claims: jwt.Claims = {
        "sub": user["id"],
        "jti": cuid_generator(),
        "iss": config.jwt.issuer,
        "aud": config.jwt.audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=config.jwt.access_token_ttl)).timestamp()),
        "type": "access",
        "email": user["email"],
        "name": user["name"],
        "email_verified": user["email_verified"],
    }
    return jwt.encode(
        header=header, claims=claims, key=key, algorithms=[config.jwt.algorithm]
    )


def create_refresh_token(user: UserData, config: FastAuthConfig) -> str:
    key = OctKey.import_key(config.secret)
    now = datetime.now(timezone.utc)
    header = {"alg": config.jwt.algorithm}
    claims: jwt.Claims = {
        "sub": user["id"],
        "jti": cuid_generator(),
        "iss": config.jwt.issuer,
        "aud": config.jwt.audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=config.jwt.refresh_token_ttl)).timestamp()),
        "type": "refresh",
        "email": user["email"],
        "name": user["name"],
        "email_verified": user["email_verified"],
    }
    return jwt.encode(
        header=header, claims=claims, key=key, algorithms=[config.jwt.algorithm]
    )


def create_token_pair(user: UserData, config: FastAuthConfig) -> TokenPair:
    access = create_access_token(user, config)
    refresh = create_refresh_token(user, config)

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": config.jwt.access_token_ttl,
    }


def decode_token(token: str, config: FastAuthConfig) -> dict[str, Any]:
    key = OctKey.import_key(config.secret)
    data = jwt.decode(token, key, algorithms=[config.jwt.algorithm])

    claims_requests = jwt.JWTClaimsRegistry(
        exp={"essential": True},
        sub={"essential": True},
    )
    claims_requests.validate(data.claims)

    return data.claims
