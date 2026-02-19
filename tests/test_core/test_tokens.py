import pytest
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.core.tokens import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
)
from fastauth.types import UserData
from joserfc import jwt as jwt_lib
from joserfc.errors import DecodeError, ExpiredTokenError


@pytest.fixture
def user() -> UserData:
    return {
        "id": "test_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "email_verified": True,
        "is_active": True,
        "image": None,
    }


@pytest.fixture
async def rs256_config():
    from fastauth.adapters.memory import MemoryUserAdapter
    from fastauth.providers.credentials import CredentialsProvider

    return FastAuthConfig(
        secret="unused",
        providers=[CredentialsProvider()],
        adapter=MemoryUserAdapter(),
        jwt=JWTConfig(algorithm="RS256", jwks_enabled=True),
    )


@pytest.fixture
async def jwks_manager(rs256_config):
    from fastauth.core.jwks import JWKSManager

    manager = JWKSManager(rs256_config.jwt)
    await manager.initialize()
    return manager


def test_create_access_token(user, config):
    access_token = create_access_token(user, config)
    claims = decode_token(access_token, config)

    assert claims["type"] == "access"
    assert claims["sub"] == user["id"]
    assert claims["email"] == user["email"]


def test_create_refresh_token(user, config):
    refresh_token = create_refresh_token(user, config)
    claims = decode_token(refresh_token, config)

    assert claims["type"] == "refresh"
    assert claims["sub"] == user["id"]


def test_create_token_pair(user, config):
    token = create_token_pair(user, config)

    assert token["access_token"] is not None
    assert token["refresh_token"] is not None
    assert token["token_type"] == "bearer"
    assert token["expires_in"] == config.jwt.access_token_ttl

    access_claims = decode_token(token["access_token"], config)
    refresh_claims = decode_token(token["refresh_token"], config)

    assert access_claims["type"] == "access"
    assert refresh_claims["type"] == "refresh"


def test_decode_expired_token(user, config):
    expired_config = FastAuthConfig(
        secret=config.secret,
        adapter=config.adapter,
        providers=config.providers,
        jwt=JWTConfig(access_token_ttl=-1),
    )

    access_token = create_access_token(user, expired_config)

    with pytest.raises(ExpiredTokenError):
        decode_token(access_token, expired_config)


def test_decode_invalid_token(config):
    with pytest.raises(DecodeError):
        decode_token("not-a-valid-jwt-token", config)


def test_token_has_cuid2_jti(user, config):
    access_token = create_access_token(user, config)
    claims = decode_token(access_token, config)

    assert "jti" in claims
    assert isinstance(claims["jti"], str)
    assert len(claims["jti"]) > 10
    assert "-" not in claims["jti"]


async def test_rs256_create_and_decode(user, rs256_config, jwks_manager):
    token = create_access_token(user, rs256_config, jwks_manager)
    claims = decode_token(token, rs256_config, jwks_manager)

    assert claims["sub"] == user["id"]
    assert claims["type"] == "access"


async def test_rs256_token_has_kid(user, rs256_config, jwks_manager):

    token = create_access_token(user, rs256_config, jwks_manager)
    key = jwks_manager.get_signing_key()
    data = jwt_lib.decode(token, key, algorithms=["RS256"])
    assert "kid" in data.header
    assert data.header["kid"] == jwks_manager.get_signing_kid()


async def test_rs256_token_pair(user, rs256_config, jwks_manager):
    pair = create_token_pair(user, rs256_config, jwks_manager)
    assert pair["token_type"] == "bearer"

    access_claims = decode_token(pair["access_token"], rs256_config, jwks_manager)
    refresh_claims = decode_token(pair["refresh_token"], rs256_config, jwks_manager)
    assert access_claims["type"] == "access"
    assert refresh_claims["type"] == "refresh"


async def test_rs256_decode_after_rotation(user, rs256_config, jwks_manager):
    token = create_access_token(user, rs256_config, jwks_manager)
    await jwks_manager.rotate()

    claims = decode_token(token, rs256_config, jwks_manager)
    assert claims["sub"] == user["id"]
