import pytest
from fastauth.adapters.memory import MemoryPasskeyAdapter


@pytest.fixture
def adapter():
    return MemoryPasskeyAdapter()


async def test_create_passkey(adapter):
    pk = await adapter.create_passkey(
        user_id="user1",
        credential_id="cred1",
        public_key=b"pubkey",
        sign_count=0,
        aaguid="aaguid-1",
        name="Touch ID",
    )
    assert pk["id"] == "cred1"
    assert pk["user_id"] == "user1"
    assert pk["public_key"] == b"pubkey"
    assert pk["sign_count"] == 0
    assert pk["aaguid"] == "aaguid-1"
    assert pk["name"] == "Touch ID"
    assert pk["last_used_at"] is None
    assert "created_at" in pk


async def test_get_passkey(adapter):
    await adapter.create_passkey("u1", "c1", b"pk", 0, "", "Key 1")
    pk = await adapter.get_passkey("c1")
    assert pk is not None
    assert pk["id"] == "c1"


async def test_get_passkey_not_found(adapter):
    result = await adapter.get_passkey("nonexistent")
    assert result is None


async def test_get_passkeys_by_user(adapter):
    await adapter.create_passkey("u1", "c1", b"pk1", 0, "", "Key 1")
    await adapter.create_passkey("u1", "c2", b"pk2", 0, "", "Key 2")
    await adapter.create_passkey("u2", "c3", b"pk3", 0, "", "Key 3")

    user1_keys = await adapter.get_passkeys_by_user("u1")
    assert len(user1_keys) == 2

    user2_keys = await adapter.get_passkeys_by_user("u2")
    assert len(user2_keys) == 1


async def test_get_passkeys_by_user_empty(adapter):
    result = await adapter.get_passkeys_by_user("nobody")
    assert result == []


async def test_update_sign_count(adapter):
    await adapter.create_passkey("u1", "c1", b"pk", 0, "", "Key")
    await adapter.update_sign_count("c1", 5, "2024-01-01T00:00:00")
    pk = await adapter.get_passkey("c1")
    assert pk["sign_count"] == 5
    assert pk["last_used_at"] == "2024-01-01T00:00:00"


async def test_update_sign_count_nonexistent(adapter):
    await adapter.update_sign_count("nonexistent", 5, "2024-01-01T00:00:00")


async def test_delete_passkey(adapter):
    await adapter.create_passkey("u1", "c1", b"pk", 0, "", "Key")
    await adapter.delete_passkey("c1")
    assert await adapter.get_passkey("c1") is None
    assert await adapter.get_passkeys_by_user("u1") == []


async def test_delete_passkey_nonexistent(adapter):
    await adapter.delete_passkey("nonexistent")


async def test_delete_passkey_removes_from_user_index(adapter):
    await adapter.create_passkey("u1", "c1", b"pk1", 0, "", "Key 1")
    await adapter.create_passkey("u1", "c2", b"pk2", 0, "", "Key 2")
    await adapter.delete_passkey("c1")
    remaining = await adapter.get_passkeys_by_user("u1")
    assert len(remaining) == 1
    assert remaining[0]["id"] == "c2"
