import pytest
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter


@pytest.fixture
async def adapter():
    a = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///:memory:")
    await a.create_tables()
    yield a
    await a.drop_tables()


@pytest.fixture
async def user(adapter):
    return await adapter.user.create_user("pk@example.com", hashed_password="hash")


async def test_create_passkey(adapter, user):
    pk = await adapter.passkey.create_passkey(
        user_id=user["id"],
        credential_id="cred-1",
        public_key=b"pubkey-bytes",
        sign_count=0,
        aaguid="aaguid-abc",
        name="Touch ID",
    )
    assert pk["id"] == "cred-1"
    assert pk["user_id"] == user["id"]
    assert pk["public_key"] == b"pubkey-bytes"
    assert pk["sign_count"] == 0
    assert pk["aaguid"] == "aaguid-abc"
    assert pk["name"] == "Touch ID"
    assert pk["last_used_at"] is None
    assert "created_at" in pk


async def test_get_passkey(adapter, user):
    await adapter.passkey.create_passkey(user["id"], "cred-1", b"pk", 0, "", "Key")
    result = await adapter.passkey.get_passkey("cred-1")
    assert result is not None
    assert result["id"] == "cred-1"


async def test_get_passkey_not_found(adapter):
    result = await adapter.passkey.get_passkey("nonexistent")
    assert result is None


async def test_get_passkeys_by_user(adapter, user):
    await adapter.passkey.create_passkey(user["id"], "cred-1", b"pk1", 0, "", "Key 1")
    await adapter.passkey.create_passkey(user["id"], "cred-2", b"pk2", 0, "", "Key 2")

    other = await adapter.user.create_user("other@example.com")
    await adapter.passkey.create_passkey(other["id"], "cred-3", b"pk3", 0, "", "Key 3")

    user_keys = await adapter.passkey.get_passkeys_by_user(user["id"])
    assert len(user_keys) == 2

    other_keys = await adapter.passkey.get_passkeys_by_user(other["id"])
    assert len(other_keys) == 1


async def test_get_passkeys_by_user_empty(adapter):
    result = await adapter.passkey.get_passkeys_by_user("nobody")
    assert result == []


async def test_update_sign_count(adapter, user):
    await adapter.passkey.create_passkey(user["id"], "cred-1", b"pk", 0, "", "Key")
    await adapter.passkey.update_sign_count("cred-1", 42, "2024-06-01T12:00:00")
    pk = await adapter.passkey.get_passkey("cred-1")
    assert pk["sign_count"] == 42
    assert pk["last_used_at"] is not None


async def test_delete_passkey(adapter, user):
    await adapter.passkey.create_passkey(user["id"], "cred-1", b"pk", 0, "", "Key")
    await adapter.passkey.delete_passkey("cred-1")
    result = await adapter.passkey.get_passkey("cred-1")
    assert result is None


async def test_delete_passkey_nonexistent(adapter):
    await adapter.passkey.delete_passkey("nonexistent")
