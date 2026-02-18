from datetime import datetime, timedelta, timezone

import pytest
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.exceptions import UserAlreadyExistsError, UserNotFoundError


@pytest.fixture
async def adapter():
    a = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///:memory:")
    await a.create_tables()
    yield a
    await a.drop_tables()


async def test_create_user(adapter):
    user = await adapter.user.create_user("alice@example.com", hashed_password="hashed")
    assert user["email"] == "alice@example.com"
    assert user["is_active"] is True
    assert user["email_verified"] is False
    assert "id" in user


async def test_create_user_with_name(adapter):
    user = await adapter.user.create_user("bob@example.com", name="Bob")
    assert user["name"] == "Bob"


async def test_create_duplicate_user_raises(adapter):
    await adapter.user.create_user("alice@example.com")
    with pytest.raises(UserAlreadyExistsError):
        await adapter.user.create_user("alice@example.com")


async def test_get_user_by_id(adapter):
    created = await adapter.user.create_user("alice@example.com")
    found = await adapter.user.get_user_by_id(created["id"])
    assert found is not None
    assert found["email"] == "alice@example.com"


async def test_get_user_by_id_not_found(adapter):
    result = await adapter.user.get_user_by_id("nonexistent")
    assert result is None


async def test_get_user_by_email(adapter):
    await adapter.user.create_user("alice@example.com")
    found = await adapter.user.get_user_by_email("alice@example.com")
    assert found is not None
    assert found["email"] == "alice@example.com"


async def test_get_user_by_email_not_found(adapter):
    result = await adapter.user.get_user_by_email("nobody@example.com")
    assert result is None


async def test_update_user(adapter):
    user = await adapter.user.create_user("alice@example.com")
    updated = await adapter.user.update_user(
        user["id"], name="Alice", email_verified=True
    )
    assert updated["name"] == "Alice"
    assert updated["email_verified"] is True


async def test_update_user_not_found_raises(adapter):
    with pytest.raises(UserNotFoundError):
        await adapter.user.update_user("nonexistent", name="X")


async def test_delete_user_soft(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.user.delete_user(user["id"], soft=True)
    found = await adapter.user.get_user_by_id(user["id"])
    assert found is not None
    assert found["is_active"] is False


async def test_delete_user_hard(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.user.delete_user(user["id"], soft=False)
    found = await adapter.user.get_user_by_id(user["id"])
    assert found is None


async def test_delete_user_not_found_raises(adapter):
    with pytest.raises(UserNotFoundError):
        await adapter.user.delete_user("nonexistent")


async def test_get_hashed_password(adapter):
    user = await adapter.user.create_user("alice@example.com", hashed_password="myhash")
    pw = await adapter.user.get_hashed_password(user["id"])
    assert pw == "myhash"


async def test_get_hashed_password_none(adapter):
    user = await adapter.user.create_user("alice@example.com")
    pw = await adapter.user.get_hashed_password(user["id"])
    assert pw is None


async def test_set_hashed_password(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.user.set_hashed_password(user["id"], "newhash")
    pw = await adapter.user.get_hashed_password(user["id"])
    assert pw == "newhash"


async def test_set_hashed_password_not_found_raises(adapter):
    with pytest.raises(UserNotFoundError):
        await adapter.user.set_hashed_password("nonexistent", "hash")


def _token_data(user_id: str, token_type: str = "verification", token: str = "tok1"):
    return {
        "token": token,
        "user_id": user_id,
        "token_type": token_type,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
    }


async def test_create_and_get_token(adapter):
    user = await adapter.user.create_user("alice@example.com")
    data = _token_data(user["id"])
    await adapter.token.create_token(data)
    found = await adapter.token.get_token("tok1", "verification")
    assert found is not None
    assert found["user_id"] == user["id"]


async def test_get_token_wrong_type(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.token.create_token(_token_data(user["id"], "verification", "tok2"))
    result = await adapter.token.get_token("tok2", "password_reset")
    assert result is None


async def test_get_token_expired(adapter):
    user = await adapter.user.create_user("alice@example.com")
    expired = {
        "token": "expired_tok",
        "user_id": user["id"],
        "token_type": "verification",
        "expires_at": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    await adapter.token.create_token(expired)
    result = await adapter.token.get_token("expired_tok", "verification")
    assert result is None


async def test_delete_token(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.token.create_token(_token_data(user["id"]))
    await adapter.token.delete_token("tok1")
    assert await adapter.token.get_token("tok1", "verification") is None


async def test_delete_user_tokens(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.token.create_token(_token_data(user["id"], token="t1"))
    await adapter.token.create_token(
        _token_data(user["id"], token_type="password_reset", token="t2")
    )
    await adapter.token.delete_user_tokens(user["id"])
    assert await adapter.token.get_token("t1", "verification") is None
    assert await adapter.token.get_token("t2", "password_reset") is None


async def test_delete_user_tokens_by_type(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.token.create_token(_token_data(user["id"], token="t1"))
    await adapter.token.create_token(
        _token_data(user["id"], token_type="password_reset", token="t2")
    )
    await adapter.token.delete_user_tokens(user["id"], token_type="verification")
    assert await adapter.token.get_token("t1", "verification") is None
    assert await adapter.token.get_token("t2", "password_reset") is not None


def _session_data(user_id: str, session_id: str = "sess1"):
    return {
        "id": session_id,
        "user_id": user_id,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "ip_address": "127.0.0.1",
        "user_agent": "pytest",
    }


async def test_create_and_get_session(adapter):
    user = await adapter.user.create_user("alice@example.com")
    data = _session_data(user["id"])
    await adapter.session.create_session(data)
    found = await adapter.session.get_session("sess1")
    assert found is not None
    assert found["user_id"] == user["id"]


async def test_get_session_not_found(adapter):
    result = await adapter.session.get_session("nonexistent")
    assert result is None


async def test_delete_session(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.session.create_session(_session_data(user["id"]))
    await adapter.session.delete_session("sess1")
    assert await adapter.session.get_session("sess1") is None


async def test_delete_user_sessions(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.session.create_session(_session_data(user["id"], "s1"))
    await adapter.session.create_session(_session_data(user["id"], "s2"))
    await adapter.session.delete_user_sessions(user["id"])
    assert await adapter.session.get_session("s1") is None
    assert await adapter.session.get_session("s2") is None


async def test_create_and_get_role(adapter):
    role = await adapter.role.create_role("admin", ["read", "write"])
    assert role["name"] == "admin"
    assert "read" in role["permissions"]


async def test_get_role_not_found(adapter):
    result = await adapter.role.get_role("nonexistent")
    assert result is None


async def test_list_roles(adapter):
    await adapter.role.create_role("admin")
    await adapter.role.create_role("user")
    roles = await adapter.role.list_roles()
    names = [r["name"] for r in roles]
    assert "admin" in names
    assert "user" in names


async def test_delete_role(adapter):
    await adapter.role.create_role("temp")
    await adapter.role.delete_role("temp")
    assert await adapter.role.get_role("temp") is None


async def test_add_permissions(adapter):
    await adapter.role.create_role("editor", ["read"])
    await adapter.role.add_permissions("editor", ["write", "publish"])
    role = await adapter.role.get_role("editor")
    assert role is not None
    assert "write" in role["permissions"]
    assert "publish" in role["permissions"]


async def test_remove_permissions(adapter):
    await adapter.role.create_role("editor", ["read", "write"])
    await adapter.role.remove_permissions("editor", ["write"])
    role = await adapter.role.get_role("editor")
    assert role is not None
    assert "write" not in role["permissions"]
    assert "read" in role["permissions"]


async def test_assign_and_get_user_roles(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.role.create_role("admin")
    await adapter.role.assign_role(user["id"], "admin")
    roles = await adapter.role.get_user_roles(user["id"])
    assert "admin" in roles


async def test_revoke_role(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.role.create_role("admin")
    await adapter.role.assign_role(user["id"], "admin")
    await adapter.role.revoke_role(user["id"], "admin")
    roles = await adapter.role.get_user_roles(user["id"])
    assert "admin" not in roles


async def test_get_user_permissions(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.role.create_role("editor", ["posts:read", "posts:write"])
    await adapter.role.assign_role(user["id"], "editor")
    perms = await adapter.role.get_user_permissions(user["id"])
    assert "posts:read" in perms
    assert "posts:write" in perms


def _oauth_data(user_id: str, provider: str = "google", pid: str = "goog123"):
    return {
        "provider": provider,
        "provider_account_id": pid,
        "user_id": user_id,
        "access_token": "at",
        "refresh_token": "rt",
        "expires_at": None,
    }


async def test_create_and_get_oauth_account(adapter):
    user = await adapter.user.create_user("alice@example.com")
    data = _oauth_data(user["id"])
    await adapter.oauth.create_oauth_account(data)
    found = await adapter.oauth.get_oauth_account("google", "goog123")
    assert found is not None
    assert found["user_id"] == user["id"]


async def test_get_oauth_account_not_found(adapter):
    result = await adapter.oauth.get_oauth_account("github", "nonexistent")
    assert result is None


async def test_get_user_oauth_accounts(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.oauth.create_oauth_account(_oauth_data(user["id"], "google", "g1"))
    await adapter.oauth.create_oauth_account(_oauth_data(user["id"], "github", "gh1"))
    accounts = await adapter.oauth.get_user_oauth_accounts(user["id"])
    providers = [a["provider"] for a in accounts]
    assert "google" in providers
    assert "github" in providers


async def test_delete_oauth_account(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.oauth.create_oauth_account(_oauth_data(user["id"]))
    await adapter.oauth.delete_oauth_account("google", "goog123")
    result = await adapter.oauth.get_oauth_account("google", "goog123")
    assert result is None


async def test_cleanup_expired_sessions(adapter):
    user = await adapter.user.create_user("alice@example.com")
    expired = {
        "id": "expired_s",
        "user_id": user["id"],
        "expires_at": datetime.now(timezone.utc) - timedelta(hours=1),
        "ip_address": "127.0.0.1",
        "user_agent": "pytest",
    }
    await adapter.session.create_session(expired)
    count = await adapter.session.cleanup_expired()
    assert count >= 1
    assert await adapter.session.get_session("expired_s") is None


async def test_cleanup_expired_sessions_none_expired(adapter):
    user = await adapter.user.create_user("alice@example.com")
    await adapter.session.create_session(_session_data(user["id"], "active_s"))
    count = await adapter.session.cleanup_expired()
    assert count == 0


async def test_create_tables_idempotent():
    a = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///:memory:")
    await a.create_tables()
    await a.create_tables()
    await a.drop_tables()
