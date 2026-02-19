import pytest
from fastapi import Depends, FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import MemoryTokenAdapter, MemoryUserAdapter
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


async def test_confirm_email_change(client, memory_token_adapter):
    token = await _register_and_get_token(client)
    await client.post(
        "/auth/account/change-email",
        json={"new_email": "new@example.com", "password": "Pass123#"},
        headers=_auth_header(token),
    )

    stored_tokens = list(memory_token_adapter._tokens.values())
    change_token = [t for t in stored_tokens if t["token_type"] == "email_change"][0]

    resp = await client.get(
        f"/auth/account/confirm-email-change?token={change_token['token']}",
    )
    assert resp.status_code == 200


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
