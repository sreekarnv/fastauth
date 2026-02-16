from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Callable

from cuid2 import cuid_wrapper
from joserfc import jwt
from joserfc.jwk import OctKey

from fastauth.config import FastAuthConfig
from fastauth.types import TokenPair, UserData

if TYPE_CHECKING:
    from fastauth.core.jwks import JWKSManager

cuid_generator: Callable[[], str] = cuid_wrapper()


def _get_signing_key_and_header(
    config: FastAuthConfig,
    jwks_manager: JWKSManager | None = None,
) -> tuple[Any, dict[str, str]]:
    if config.jwt.algorithm.startswith("RS") and jwks_manager:
        key = jwks_manager.get_signing_key()
        header = {
            "alg": config.jwt.algorithm,
            "kid": jwks_manager.get_signing_kid(),
        }
        return key, header
    key = OctKey.import_key(config.secret)
    header = {"alg": config.jwt.algorithm}
    return key, header


def _get_decode_key(
    config: FastAuthConfig,
    jwks_manager: JWKSManager | None = None,
) -> Any:
    if config.jwt.algorithm.startswith("RS") and jwks_manager:
        keys = jwks_manager.get_verification_keys()
        if len(keys) == 1:
            return keys[0]
        # For multiple keys, try each one
        return keys
    return OctKey.import_key(config.secret)


def create_access_token(
    user: UserData,
    config: FastAuthConfig,
    jwks_manager: JWKSManager | None = None,
) -> str:
    key, header = _get_signing_key_and_header(config, jwks_manager)
    now = datetime.now(timezone.utc)
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
        header=header,
        claims=claims,
        key=key,
        algorithms=[config.jwt.algorithm],
    )


def create_refresh_token(
    user: UserData,
    config: FastAuthConfig,
    jwks_manager: JWKSManager | None = None,
) -> str:
    key, header = _get_signing_key_and_header(config, jwks_manager)
    now = datetime.now(timezone.utc)
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
        header=header,
        claims=claims,
        key=key,
        algorithms=[config.jwt.algorithm],
    )


def create_token_pair(
    user: UserData,
    config: FastAuthConfig,
    jwks_manager: JWKSManager | None = None,
) -> TokenPair:
    access = create_access_token(user, config, jwks_manager)
    refresh = create_refresh_token(user, config, jwks_manager)

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": config.jwt.access_token_ttl,
    }


def decode_token(
    token: str,
    config: FastAuthConfig,
    jwks_manager: JWKSManager | None = None,
) -> dict[str, Any]:
    decode_key = _get_decode_key(config, jwks_manager)

    # For RS* with multiple keys, try each one
    if isinstance(decode_key, list):
        last_err: Exception | None = None
        for key in decode_key:
            try:
                data = jwt.decode(token, key, algorithms=[config.jwt.algorithm])
                claims_requests = jwt.JWTClaimsRegistry(
                    exp={"essential": True},
                    sub={"essential": True},
                )
                claims_requests.validate(data.claims)
                return data.claims
            except Exception as e:
                last_err = e
        if last_err:
            raise last_err
        raise ValueError("No verification keys available")

    data = jwt.decode(token, decode_key, algorithms=[config.jwt.algorithm])
    claims_requests = jwt.JWTClaimsRegistry(
        exp={"essential": True},
        sub={"essential": True},
    )
    claims_requests.validate(data.claims)
    return data.claims
