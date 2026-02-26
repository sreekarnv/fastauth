import types
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from fastauth.adapters.memory import MemoryTokenAdapter, MemoryUserAdapter
from fastauth.exceptions import AuthenticationError
from fastauth.providers.magic_links import MagicLinksProvider


def _make_fa(user_adapter, token_adapter, email_dispatcher=None):
    config = types.SimpleNamespace(
        adapter=user_adapter,
        token_adapter=token_adapter,
    )
    return types.SimpleNamespace(config=config, email_dispatcher=email_dispatcher)


@pytest.fixture
def user_adapter():
    return MemoryUserAdapter()


@pytest.fixture
def token_adapter():
    return MemoryTokenAdapter()


@pytest.fixture
def provider():
    return MagicLinksProvider()


def test_default_max_age():
    assert MagicLinksProvider().max_age == 15 * 60


def test_custom_max_age():
    assert MagicLinksProvider(max_age=300).max_age == 300


def test_provider_metadata():
    p = MagicLinksProvider()
    assert p.id == "magic_links"
    assert p.name == "Magic Links"
    assert p.auth_type == "magic_links"


async def test_send_login_request_creates_token(provider, user_adapter, token_adapter):
    user = await user_adapter.create_user("ml@example.com")
    fa = _make_fa(user_adapter, token_adapter)

    await provider.send_login_request(fa, user)

    tokens = list(token_adapter._tokens.values())
    assert len(tokens) == 1
    assert tokens[0]["token_type"] == "magic_link_login_request"
    assert tokens[0]["user_id"] == user["id"]


async def test_send_login_request_expiry_is_within_max_age(
    provider, user_adapter, token_adapter
):
    user = await user_adapter.create_user("expiry@example.com")
    fa = _make_fa(user_adapter, token_adapter)
    before = datetime.now(timezone.utc)

    await provider.send_login_request(fa, user)

    token_data = list(token_adapter._tokens.values())[0]
    expected_min = before + timedelta(seconds=provider.max_age - 2)
    expected_max = before + timedelta(seconds=provider.max_age + 2)
    assert expected_min <= token_data["expires_at"] <= expected_max


async def test_send_login_request_calls_email_dispatcher(
    provider, user_adapter, token_adapter
):
    user = await user_adapter.create_user("dispatch@example.com")
    dispatcher = AsyncMock()
    fa = _make_fa(user_adapter, token_adapter, email_dispatcher=dispatcher)

    await provider.send_login_request(fa, user)

    dispatcher.send_magic_link_login_request.assert_called_once()
    call_kwargs = dispatcher.send_magic_link_login_request.call_args.kwargs
    assert call_kwargs["user"] == user
    assert isinstance(call_kwargs["token"], str)


async def test_send_login_request_skips_email_when_no_dispatcher(
    provider, user_adapter, token_adapter
):
    user = await user_adapter.create_user("nodisp@example.com")
    fa = _make_fa(user_adapter, token_adapter, email_dispatcher=None)

    await provider.send_login_request(fa, user)

    assert len(token_adapter._tokens) == 1


async def test_authenticate_returns_user(provider, user_adapter, token_adapter):
    user = await user_adapter.create_user("valid@example.com")
    fa = _make_fa(user_adapter, token_adapter)
    await provider.send_login_request(fa, user)

    raw_token = next(iter(token_adapter._tokens))
    result = await provider.authenticate(fa, raw_token)

    assert result["id"] == user["id"]
    assert result["email"] == user["email"]


async def test_authenticate_deletes_token_after_use(
    provider, user_adapter, token_adapter
):
    user = await user_adapter.create_user("oneuse@example.com")
    fa = _make_fa(user_adapter, token_adapter)
    await provider.send_login_request(fa, user)

    raw_token = next(iter(token_adapter._tokens))
    await provider.authenticate(fa, raw_token)

    assert raw_token not in token_adapter._tokens


async def test_authenticate_token_is_one_time_use(
    provider, user_adapter, token_adapter
):
    user = await user_adapter.create_user("otp@example.com")
    fa = _make_fa(user_adapter, token_adapter)
    await provider.send_login_request(fa, user)

    raw_token = next(iter(token_adapter._tokens))
    await provider.authenticate(fa, raw_token)

    with pytest.raises(AuthenticationError):
        await provider.authenticate(fa, raw_token)


async def test_authenticate_invalid_token_raises(provider, user_adapter, token_adapter):
    fa = _make_fa(user_adapter, token_adapter)

    with pytest.raises(AuthenticationError, match="Invalid or expired"):
        await provider.authenticate(fa, "nonexistent-token")


async def test_authenticate_expired_token_raises(provider, user_adapter, token_adapter):
    user = await user_adapter.create_user("exp@example.com")
    fa = _make_fa(user_adapter, token_adapter)

    await token_adapter.create_token(
        {
            "token": "expired-tok",
            "token_type": "magic_link_login_request",
            "user_id": user["id"],
            "expires_at": datetime.now(timezone.utc) - timedelta(seconds=1),
            "raw_data": None,
        }
    )

    with pytest.raises(AuthenticationError):
        await provider.authenticate(fa, "expired-tok")


async def test_authenticate_wrong_token_type_raises(
    provider, user_adapter, token_adapter
):
    user = await user_adapter.create_user("wrongtype@example.com")
    fa = _make_fa(user_adapter, token_adapter)

    await token_adapter.create_token(
        {
            "token": "wrong-type-tok",
            "token_type": "email_verification",
            "user_id": user["id"],
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "raw_data": None,
        }
    )

    with pytest.raises(AuthenticationError):
        await provider.authenticate(fa, "wrong-type-tok")
