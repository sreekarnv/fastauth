from datetime import datetime, timedelta, timezone

import pytest
from fastapi import Depends, FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import (
    MemorySessionAdapter,
    MemoryTokenAdapter,
    MemoryUserAdapter,
)
from fastauth.api.deps import require_auth
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.email_transports.console import ConsoleTransport
from fastauth.providers.credentials import CredentialsProvider
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def memory_user_adapter():
    return MemoryUserAdapter()


@pytest.fixture
def memory_token_adapter():
    return MemoryTokenAdapter()


@pytest.fixture
def config(memory_user_adapter, memory_token_adapter):
    return FastAuthConfig(
        secret="super-secret-key-only-for-testing",
        providers=[CredentialsProvider()],
        adapter=memory_user_adapter,
        jwt=JWTConfig(algorithm="HS256"),
        token_adapter=memory_token_adapter,
        email_transport=ConsoleTransport(),
        base_url="http://localhost:8000",
    )


@pytest.fixture
def auth(config):
    return FastAuth(config)


@pytest.fixture
def app(auth):
    _app = FastAPI()
    auth.mount(_app)

    @_app.get("/protected")
    async def protected_route(user=Depends(require_auth)):
        return {"user": user}

    return _app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _register_and_get_token(client):
    resp = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "Pass123#", "name": "Test"},
    )
    data = resp.json()
    return data["access_token"]


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def _extract_token_from_output(out: str) -> str:
    raw_token = ""
    for line in out.splitlines():
        if "token=" in line:
            tail = line.split("token=", 1)[1]
            for ch in tail:
                if ch.isalnum() or ch in "-_.":
                    raw_token += ch
                else:
                    break
            if raw_token:
                break
    assert raw_token, f"Could not find token= in console output:\n{out}"
    return raw_token


async def test_change_password_success(client):
    token = await _register_and_get_token(client)
    resp = await client.post(
        "/auth/account/change-password",
        json={"current_password": "Pass123#", "new_password": "NewPass456#"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200

    # Verify login with new password
    login_resp = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "NewPass456#"},
    )
    assert login_resp.status_code == 200


async def test_change_password_wrong_current(client):
    token = await _register_and_get_token(client)
    resp = await client.post(
        "/auth/account/change-password",
        json={"current_password": "wrong", "new_password": "NewPass456#"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 400


async def test_change_password_unauthenticated(client):
    resp = await client.post(
        "/auth/account/change-password",
        json={"current_password": "Pass123#", "new_password": "NewPass456#"},
    )
    assert resp.status_code == 401


async def test_change_email_success(client):
    token = await _register_and_get_token(client)
    resp = await client.post(
        "/auth/account/change-email",
        json={"new_email": "new@example.com", "password": "Pass123#"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    assert "Confirmation" in resp.json()["message"]


async def test_change_email_wrong_password(client):
    token = await _register_and_get_token(client)
    resp = await client.post(
        "/auth/account/change-email",
        json={"new_email": "new@example.com", "password": "wrong"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 400


async def test_change_email_already_taken(client):
    token = await _register_and_get_token(client)
    # Register another user
    await client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "Pass123#", "name": "Other"},
    )

    resp = await client.post(
        "/auth/account/change-email",
        json={"new_email": "other@example.com", "password": "Pass123#"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 409


async def test_confirm_email_change(client, capsys):
    token = await _register_and_get_token(client)
    await client.post(
        "/auth/account/change-email",
        json={"new_email": "new@example.com", "password": "Pass123#"},
        headers=_auth_header(token),
    )

    raw_token = _extract_token_from_output(capsys.readouterr().out)

    resp = await client.get(
        f"/auth/account/confirm-email-change?token={raw_token}",
    )
    assert resp.status_code == 200

    replay = await client.get(
        f"/auth/account/confirm-email-change?token={raw_token}",
    )
    assert replay.status_code == 400


async def test_confirm_email_change_verifies_revokes_and_clears_pending(
    client, memory_user_adapter, memory_token_adapter, capsys
):
    token = await _register_and_get_token(client)
    user = await memory_user_adapter.get_user_by_email("test@example.com")
    assert user is not None

    await memory_token_adapter.create_token(
        {
            "token": "refresh-jti",
            "user_id": user["id"],
            "token_type": "refresh_jti",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "raw_data": None,
        }
    )
    await client.post(
        "/auth/account/change-email",
        json={"new_email": "new@example.com", "password": "Pass123#"},
        headers=_auth_header(token),
    )
    first_token = _extract_token_from_output(capsys.readouterr().out)
    await client.post(
        "/auth/account/change-email",
        json={"new_email": "newer@example.com", "password": "Pass123#"},
        headers=_auth_header(token),
    )
    _ = _extract_token_from_output(capsys.readouterr().out)

    resp = await client.get(f"/auth/account/confirm-email-change?token={first_token}")
    assert resp.status_code == 200

    updated = await memory_user_adapter.get_user_by_email("new@example.com")
    assert updated is not None
    assert updated["email_verified"] is True
    assert await memory_token_adapter.get_token("refresh-jti", "refresh_jti") is None
    assert await memory_token_adapter.get_token("refresh-jti", "email_change") is None
    pending = [
        token
        for token in memory_token_adapter._tokens.values()
        if token["user_id"] == user["id"] and token["token_type"] == "email_change"
    ]
    assert pending == []


async def test_confirm_email_change_invalid_token(client):
    token = await _register_and_get_token(client)
    await client.post(
        "/auth/account/change-email",
        json={"new_email": "", "password": "Pass123#"},
        headers=_auth_header(token),
    )

    resp = await client.get(
        f"/auth/account/confirm-email-change?token={token}",
    )
    assert resp.status_code == 400


async def test_confirm_email_change_missing_email(client):
    resp = await client.get(
        "/auth/account/confirm-email-change?token=invalid_token",
    )
    assert resp.status_code == 400


async def test_delete_account(client):
    token = await _register_and_get_token(client)
    resp = await client.request(
        "DELETE",
        "/auth/account",
        json={"password": "Pass123#"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200

    # Verify login fails after deletion
    login_resp = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "Pass123#"},
    )
    assert login_resp.status_code == 401


async def test_delete_account_and_fetch_user(client):
    token = await _register_and_get_token(client)
    resp = await client.request(
        "DELETE",
        "/auth/account",
        json={"password": "Pass123#"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200

    # Get User should fail
    get_user = await client.get("/auth/me", headers=_auth_header(token))
    assert get_user.status_code == 401


async def test_delete_account_revokes_tokens_and_sessions(
    client, app, memory_user_adapter, memory_token_adapter
):
    session_adapter = MemorySessionAdapter()
    app.state.fastauth.session_adapter = session_adapter
    access_token = await _register_and_get_token(client)
    user = await memory_user_adapter.get_user_by_email("test@example.com")
    assert user is not None
    await memory_token_adapter.create_token(
        {
            "token": "delete-refresh-jti",
            "user_id": user["id"],
            "token_type": "refresh_jti",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "raw_data": None,
        }
    )
    await session_adapter.create_session(
        {
            "id": "delete-session",
            "user_id": user["id"],
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "ip_address": None,
            "user_agent": None,
        }
    )

    resp = await client.request(
        "DELETE",
        "/auth/account",
        json={"password": "Pass123#"},
        headers=_auth_header(access_token),
    )
    assert resp.status_code == 200
    assert (
        await memory_token_adapter.get_token("delete-refresh-jti", "refresh_jti")
        is None
    )
    assert await session_adapter.get_session("delete-session") is None


async def test_delete_account_cookie_mode_clears_auth_cookies(memory_user_adapter):
    token_adapter = MemoryTokenAdapter()
    config = FastAuthConfig(
        secret="super-secret-key-only-for-testing",
        providers=[CredentialsProvider()],
        adapter=memory_user_adapter,
        jwt=JWTConfig(algorithm="HS256"),
        token_adapter=token_adapter,
        token_delivery="cookie",
        cookie_secure=False,
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        register = await c.post(
            "/auth/register",
            json={"email": "cookie@example.com", "password": "Pass123#"},
        )
        assert register.status_code == 201
        csrf_token = c.cookies.get("csrf_token")
        assert csrf_token is not None
        resp = await c.request(
            "DELETE",
            "/auth/account",
            json={"password": "Pass123#"},
            headers={"X-CSRF-Token": csrf_token},
        )

    assert resp.status_code == 200
    set_cookie = resp.headers.get_list("set-cookie")
    assert any(
        "access_token=" in header and "Max-Age=0" in header for header in set_cookie
    )
    assert any(
        "refresh_token=" in header and "Max-Age=0" in header for header in set_cookie
    )
    assert any(
        "csrf_token=" in header and "Max-Age=0" in header for header in set_cookie
    )


async def test_delete_account_wrong_password(client):
    token = await _register_and_get_token(client)
    resp = await client.request(
        "DELETE",
        "/auth/account",
        json={"password": "wrong"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 400


async def test_delete_account_unauthenticated(client):
    resp = await client.request(
        "DELETE",
        "/auth/account",
        json={"password": "Pass123#"},
    )
    assert resp.status_code == 401


async def test_get_profile(client):
    token = await _register_and_get_token(client)
    resp = await client.get("/auth/account/profile", headers=_auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test"
    assert "id" in data


async def test_get_profile_unauthenticated(client):
    resp = await client.get("/auth/account/profile")
    assert resp.status_code == 401


async def test_update_profile_name(client):
    token = await _register_and_get_token(client)
    resp = await client.put(
        "/auth/account/profile",
        json={"name": "Updated Name"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


async def test_update_profile_image(client):
    token = await _register_and_get_token(client)
    resp = await client.put(
        "/auth/account/profile",
        json={"image": "https://example.com/avatar.png"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    assert resp.json()["image"] == "https://example.com/avatar.png"


async def test_update_profile_no_fields(client):
    token = await _register_and_get_token(client)
    resp = await client.put(
        "/auth/account/profile",
        json={},
        headers=_auth_header(token),
    )
    assert resp.status_code == 400


async def test_update_profile_unauthenticated(client):
    resp = await client.put("/auth/account/profile", json={"name": "X"})
    assert resp.status_code == 401
