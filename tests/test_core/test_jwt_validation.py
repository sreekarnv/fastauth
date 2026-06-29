import pytest
from fastauth.adapters.memory import MemoryUserAdapter
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.core.tokens import (
    create_access_token,
    decode_token,
)
from fastauth.providers.credentials import CredentialsProvider
from fastauth.types import UserData


@pytest.fixture
def user() -> UserData:
    return {
        "id": "u1",
        "email": "a@b.com",
        "name": "T",
        "email_verified": True,
        "is_active": True,
        "image": None,
    }


def _config(secret: str = "this-is-a-test-secret-32-bytes!!", **jwt_kwargs):
    return FastAuthConfig(
        secret=secret,
        providers=[CredentialsProvider()],
        adapter=MemoryUserAdapter(),
        jwt=JWTConfig(**jwt_kwargs),
    )


def test_decode_with_issuer_configured_wrong_issuer_raises(user):
    config = _config(issuer="my-issuer")
    config_no_iss = _config()

    token = create_access_token(user, config_no_iss)
    with pytest.raises(Exception):
        decode_token(token, config)


def test_decode_with_issuer_configured_correct_issuer_passes(user):
    config = _config(issuer="my-issuer")

    token = create_access_token(user, config)
    claims = decode_token(token, config)
    assert claims["iss"] == "my-issuer"


def test_decode_with_audience_configured_wrong_audience_raises(user):
    config = _config(audience=["expected-aud"])
    config_no_aud = _config()

    token = create_access_token(user, config_no_aud)
    with pytest.raises(Exception):
        decode_token(token, config)


def test_decode_with_audience_configured_correct_audience_passes(user):
    config = _config(audience=["expected-aud"])

    token = create_access_token(user, config)
    claims = decode_token(token, config)
    assert claims["aud"] == ["expected-aud"]


def test_decode_with_no_issuer_config_passes_regardless_of_iss(user):
    config = _config()

    token = create_access_token(user, config)
    claims = decode_token(token, config)
    assert claims["sub"] == "u1"


async def test_modify_jwt_hook_adds_custom_claim(user):
    from fastauth.core.tokens import async_create_token_pair

    custom_claims: list[dict] = []

    async def hook(claims, _user):
        custom_claims.append(claims)
        claims["plan"] = "pro"
        return claims

    config = _config()
    pair = await async_create_token_pair(user, config, modify_jwt=hook)
    claims = decode_token(pair["access_token"], config)
    assert claims["plan"] == "pro"
    assert custom_claims  # hook was invoked at least once


async def test_modify_jwt_hook_noop_does_not_break_creation(user):
    from fastauth.core.tokens import async_create_token_pair

    async def hook(claims, _user):
        return claims

    config = _config()
    pair = await async_create_token_pair(user, config, modify_jwt=hook)
    assert "access_token" in pair
    assert "refresh_token" in pair
