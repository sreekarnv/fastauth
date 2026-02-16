import json

import pytest
from fastauth.adapters.memory import MemoryUserAdapter
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.core.sessions import DatabaseSessionStrategy, JWTSessionStrategy
from fastauth.providers.credentials import CredentialsProvider
from fastauth.session_backends.memory import MemorySessionBackend
from fastauth.types import UserData

_TEST_USER: UserData = {
    "id": "u1",
    "email": "test@example.com",
    "name": "Test",
    "image": None,
    "email_verified": True,
    "is_active": True,
}


@pytest.fixture
def adapter():
    a = MemoryUserAdapter()
    a._users["u1"] = _TEST_USER
    a._email_index["test@example.com"] = "u1"
    return a


@pytest.fixture
def config():
    return FastAuthConfig(
        secret="test-secret-key-for-sessions",
        providers=[CredentialsProvider()],
        adapter=MemoryUserAdapter(),
        jwt=JWTConfig(algorithm="HS256"),
    )


class TestJWTSessionStrategy:
    async def test_create_returns_json(self, config, adapter):
        strategy = JWTSessionStrategy(config, adapter)
        result = await strategy.create(_TEST_USER)
        data = json.loads(result)
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_validate_access_token(self, config, adapter):
        strategy = JWTSessionStrategy(config, adapter)
        result = json.loads(await strategy.create(_TEST_USER))
        user = await strategy.validate(result["access_token"])
        assert user is not None
        assert user["id"] == "u1"

    async def test_validate_refresh_token_fails(self, config, adapter):
        strategy = JWTSessionStrategy(config, adapter)
        result = json.loads(await strategy.create(_TEST_USER))
        user = await strategy.validate(result["refresh_token"])
        assert user is None

    async def test_validate_invalid_token(self, config, adapter):
        strategy = JWTSessionStrategy(config, adapter)
        user = await strategy.validate("invalid-token")
        assert user is None

    async def test_refresh_with_refresh_token(self, config, adapter):
        strategy = JWTSessionStrategy(config, adapter)
        result = json.loads(await strategy.create(_TEST_USER))
        new_result = await strategy.refresh(result["refresh_token"])
        assert new_result is not None
        data = json.loads(new_result)
        assert "access_token" in data

    async def test_refresh_with_access_token_fails(self, config, adapter):
        strategy = JWTSessionStrategy(config, adapter)
        result = json.loads(await strategy.create(_TEST_USER))
        new_result = await strategy.refresh(result["access_token"])
        assert new_result is None


class TestDatabaseSessionStrategy:
    async def test_create_returns_session_id(self, adapter):
        backend = MemorySessionBackend()
        strategy = DatabaseSessionStrategy(backend, adapter)
        session_id = await strategy.create(_TEST_USER)
        assert isinstance(session_id, str)
        assert len(session_id) > 0

    async def test_validate(self, adapter):
        backend = MemorySessionBackend()
        strategy = DatabaseSessionStrategy(backend, adapter)
        session_id = await strategy.create(_TEST_USER)
        user = await strategy.validate(session_id)
        assert user is not None
        assert user["id"] == "u1"

    async def test_validate_invalid(self, adapter):
        backend = MemorySessionBackend()
        strategy = DatabaseSessionStrategy(backend, adapter)
        user = await strategy.validate("nonexistent")
        assert user is None

    async def test_invalidate(self, adapter):
        backend = MemorySessionBackend()
        strategy = DatabaseSessionStrategy(backend, adapter)
        session_id = await strategy.create(_TEST_USER)
        await strategy.invalidate(session_id)
        user = await strategy.validate(session_id)
        assert user is None

    async def test_refresh(self, adapter):
        backend = MemorySessionBackend()
        strategy = DatabaseSessionStrategy(backend, adapter)
        session_id = await strategy.create(_TEST_USER)
        refreshed = await strategy.refresh(session_id)
        assert refreshed == session_id

    async def test_refresh_invalid(self, adapter):
        backend = MemorySessionBackend()
        strategy = DatabaseSessionStrategy(backend, adapter)
        result = await strategy.refresh("nonexistent")
        assert result is None
