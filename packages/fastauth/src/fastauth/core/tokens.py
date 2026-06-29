from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Callable

from cuid2 import cuid_wrapper
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import OctKey

from fastauth.config import FastAuthConfig
from fastauth.exceptions import InvalidTokenError
from fastauth.types import TokenPair, UserData

if TYPE_CHECKING:
    from collections.abc import Awaitable

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
    refresh_ttl_override: int | None = None,
) -> str:
    key, header = _get_signing_key_and_header(config, jwks_manager)
    now = datetime.now(timezone.utc)
    ttl = (
        refresh_ttl_override
        if refresh_ttl_override is not None
        else config.jwt.refresh_token_ttl
    )
    claims: jwt.Claims = {
        "sub": user["id"],
        "jti": cuid_generator(),
        "iss": config.jwt.issuer,
        "aud": config.jwt.audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
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
    refresh_ttl_override: int | None = None,
) -> TokenPair:
    access = create_access_token(user, config, jwks_manager)
    refresh = create_refresh_token(user, config, jwks_manager, refresh_ttl_override)

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": config.jwt.access_token_ttl,
    }


def _build_access_claims(user: UserData, config: FastAuthConfig) -> jwt.Claims:
    now = datetime.now(timezone.utc)
    return {
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


def _build_refresh_claims(
    user: UserData,
    config: FastAuthConfig,
    refresh_ttl_override: int | None = None,
) -> jwt.Claims:
    now = datetime.now(timezone.utc)
    ttl = (
        refresh_ttl_override
        if refresh_ttl_override is not None
        else config.jwt.refresh_token_ttl
    )
    return {
        "sub": user["id"],
        "jti": cuid_generator(),
        "iss": config.jwt.issuer,
        "aud": config.jwt.audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
        "type": "refresh",
        "email": user["email"],
        "name": user["name"],
        "email_verified": user["email_verified"],
    }


async def async_create_access_token(
    user: UserData,
    config: FastAuthConfig,
    jwks_manager: "JWKSManager | None" = None,
    modify_jwt: Callable[[dict[str, Any], UserData], Awaitable[dict[str, Any]]]
    | None = None,
) -> str:
    key, header = _get_signing_key_and_header(config, jwks_manager)
    claims = _build_access_claims(user, config)
    if modify_jwt is not None:
        claims = await modify_jwt(claims, user)
    return jwt.encode(
        header=header,
        claims=claims,
        key=key,
        algorithms=[config.jwt.algorithm],
    )


async def async_create_refresh_token(
    user: UserData,
    config: FastAuthConfig,
    jwks_manager: "JWKSManager | None" = None,
    refresh_ttl_override: int | None = None,
    modify_jwt: Callable[[dict[str, Any], UserData], Awaitable[dict[str, Any]]]
    | None = None,
) -> str:
    key, header = _get_signing_key_and_header(config, jwks_manager)
    claims = _build_refresh_claims(user, config, refresh_ttl_override)
    if modify_jwt is not None:
        claims = await modify_jwt(claims, user)
    return jwt.encode(
        header=header,
        claims=claims,
        key=key,
        algorithms=[config.jwt.algorithm],
    )


async def async_create_token_pair(
    user: UserData,
    config: FastAuthConfig,
    jwks_manager: "JWKSManager | None" = None,
    refresh_ttl_override: int | None = None,
    modify_jwt: Callable[[dict[str, Any], UserData], Awaitable[dict[str, Any]]]
    | None = None,
) -> TokenPair:
    access = await async_create_access_token(user, config, jwks_manager, modify_jwt)
    refresh = await async_create_refresh_token(
        user, config, jwks_manager, refresh_ttl_override, modify_jwt
    )
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": config.jwt.access_token_ttl,
    }


def _build_claims_registry(config: FastAuthConfig) -> jwt.JWTClaimsRegistry:
    options: dict[str, Any] = {
        "exp": {"essential": True},
        "sub": {"essential": True},
    }
    if config.jwt.issuer is not None:
        options["iss"] = {"essential": True, "value": config.jwt.issuer}
    if config.jwt.audience is not None:
        options["aud"] = {"essential": True}
    return jwt.JWTClaimsRegistry(**options)


def _validate_iss_aud(claims: dict[str, Any], config: FastAuthConfig) -> None:
    from joserfc.errors import InvalidClaimError, MissingClaimError

    if config.jwt.issuer is not None:
        if claims.get("iss") != config.jwt.issuer:
            if claims.get("iss") is None:
                raise MissingClaimError("iss")
            raise InvalidClaimError("iss")
    if config.jwt.audience is not None:
        actual = claims.get("aud")
        if actual is None:
            raise MissingClaimError("aud")
        expected = config.jwt.audience
        actual_list = actual if isinstance(actual, list) else [actual]
        if not any(v in actual_list for v in expected):
            raise InvalidClaimError("aud")


def decode_token(
    token: str,
    config: FastAuthConfig,
    jwks_manager: JWKSManager | None = None,
) -> dict[str, Any]:
    decode_key = _get_decode_key(config, jwks_manager)

    # For RS* with multiple keys, try each one
    if isinstance(decode_key, list):
        last_err: JoseError | None = None
        for key in decode_key:
            try:
                data = jwt.decode(token, key, algorithms=[config.jwt.algorithm])
                _build_claims_registry(config).validate(data.claims)
                _validate_iss_aud(data.claims, config)
                return data.claims
            except JoseError as e:
                last_err = e
        if last_err:
            raise InvalidTokenError("Invalid token") from last_err
        raise InvalidTokenError("No verification keys available")

    try:
        data = jwt.decode(token, decode_key, algorithms=[config.jwt.algorithm])
        _build_claims_registry(config).validate(data.claims)
        _validate_iss_aud(data.claims, config)
        return data.claims
    except JoseError as e:
        raise InvalidTokenError("Invalid token") from e
