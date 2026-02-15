from datetime import datetime, timedelta, timezone

import pytest
from fastauth.core.tokens import cuid_generator
from fastauth.exceptions import UserAlreadyExistsError


async def test_create_user(memory_user_adapter):
    user = await memory_user_adapter.create_user(
        email="a@b.com", name="Abc", hashed_password="hash123#"
    )
    assert "id" in user
    assert user["email"] == "a@b.com"
    assert user["name"] == "Abc"
    assert user["is_active"] is True
    assert user["email_verified"] is False


async def test_create_user_duplicate_email(memory_user_adapter):
    await memory_user_adapter.create_user(
        email="a@b.com", name="ABC", hashed_password="hash123#"
    )
    with pytest.raises(UserAlreadyExistsError):
        await memory_user_adapter.create_user(
            email="a@b.com", name="EFG", hashed_password="another123#"
        )


async def test_get_user_by_id(memory_user_adapter):
    user = await memory_user_adapter.create_user(
        email="a@b.com", name="ABC", hashed_password="hash123#"
    )
    _user = await memory_user_adapter.get_user_by_id(user["id"])
    assert user == _user


async def test_get_user_by_id_not_found(memory_user_adapter):
    id = cuid_generator()
    _user = await memory_user_adapter.get_user_by_id(id)
    assert _user is None


async def test_get_user_by_email(memory_user_adapter):
    email = "a@b.com"
    user = await memory_user_adapter.create_user(
        email=email, name="ABC", hashed_password="hash123#"
    )
    _user = await memory_user_adapter.get_user_by_email(email)
    assert _user == user


async def test_get_user_by_email_not_found(memory_user_adapter):
    email = "nobody@example.com"
    _user = await memory_user_adapter.get_user_by_email(email)
    assert _user is None


async def test_update_user(memory_user_adapter):
    user = await memory_user_adapter.create_user(
        email="a@b.com", name="ABC", hashed_password="hash123#"
    )
    updated_user = await memory_user_adapter.update_user(
        user["id"], name="Bob", email_verified=True
    )
    assert updated_user["name"] == "Bob"
    assert updated_user["email_verified"] is True


async def test_delete_user_hard(memory_user_adapter):
    user = await memory_user_adapter.create_user(
        email="a@b.com", name="ABC", hashed_password="hash123#"
    )
    await memory_user_adapter.delete_user(user["id"], soft=False)
    _user = await memory_user_adapter.get_user_by_id(user["id"])
    assert _user is None


async def test_delete_user_soft(memory_user_adapter):
    user = await memory_user_adapter.create_user(
        email="a@b.com", name="ABC", hashed_password="hash123#"
    )
    await memory_user_adapter.delete_user(user["id"], soft=True)
    _user = await memory_user_adapter.get_user_by_id(user["id"])
    assert _user is not None
    assert _user["is_active"] is False


async def test_password_storage(memory_user_adapter):
    pwd = "hash123#"
    user = await memory_user_adapter.create_user(
        email="a@b.com", name="ABC", hashed_password=pwd
    )
    hashed_password = await memory_user_adapter.get_hashed_password(user["id"])
    assert hashed_password == pwd

    pwd = "newhash123#"
    await memory_user_adapter.set_hashed_password(user["id"], pwd)
    hashed_password = await memory_user_adapter.get_hashed_password(user["id"])
    assert hashed_password == pwd


async def test_token_crud(memory_token_adapter):
    refresh_token = await memory_token_adapter.create_token(
        {
            "token": "tok_abc",
            "user_id": "u1",
            "token_type": "refresh",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }
    )
    _refresh_token = await memory_token_adapter.get_token(
        refresh_token["token"], "refresh"
    )
    assert _refresh_token is not None

    _ver_token = await memory_token_adapter.get_token(
        refresh_token["token"], "verification"
    )
    assert _ver_token is None

    await memory_token_adapter.delete_token(refresh_token["token"])

    _refresh_token = await memory_token_adapter.get_token(
        refresh_token["token"], "refresh"
    )
    assert _refresh_token is None


async def test_token_expired(memory_token_adapter):
    refresh_token = await memory_token_adapter.create_token(
        {
            "token": "tok_abc",
            "user_id": "u1",
            "token_type": "refresh",
            "expires_at": datetime.now(timezone.utc) - timedelta(hours=1),
        }
    )
    _refresh_token = await memory_token_adapter.get_token(
        refresh_token["token"], "refresh"
    )
    assert _refresh_token is None


async def test_delete_user_tokens(memory_token_adapter):
    await memory_token_adapter.create_token(
        {
            "token": "tok_abc",
            "user_id": "u1",
            "token_type": "refresh",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }
    )
    await memory_token_adapter.create_token(
        {
            "token": "tok_efg",
            "user_id": "u1",
            "token_type": "refresh",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }
    )
    await memory_token_adapter.create_token(
        {
            "token": "tok_xyz",
            "user_id": "u1",
            "token_type": "verification",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        }
    )

    await memory_token_adapter.delete_user_tokens("u1", token_type="refresh")

    assert (await memory_token_adapter.get_token("tok_abc", "refresh")) is None
    assert (await memory_token_adapter.get_token("tok_efg", "refresh")) is None
    assert (await memory_token_adapter.get_token("tok_xyz", "verification")) is not None

    await memory_token_adapter.delete_user_tokens("u1")

    assert (await memory_token_adapter.get_token("tok_abc", "refresh")) is None
    assert (await memory_token_adapter.get_token("tok_efg", "refresh")) is None
    assert (await memory_token_adapter.get_token("tok_xyz", "verification")) is None
