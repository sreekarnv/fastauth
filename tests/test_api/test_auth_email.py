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


async def _register(client):
    resp = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "Pass123#", "name": "Test"},
    )
    return resp.json()


async def test_request_verify_email(client):
    tokens = await _register(client)
    resp = await client.post(
        "/auth/request-verify-email",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Verification email sent"


async def test_request_verify_email_unauthenticated(client):
    resp = await client.post("/auth/request-verify-email")
    assert resp.status_code == 401


async def test_verify_email_post(client, memory_token_adapter):
    tokens = await _register(client)
    await client.post(
        "/auth/request-verify-email",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    # Get the token from the adapter
    stored_tokens = list(memory_token_adapter._tokens.values())
    verify_token = [t for t in stored_tokens if t["token_type"] == "verification"][0]

    resp = await client.post(
        "/auth/verify-email", json={"token": verify_token["token"]}
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Email verified successfully"


async def test_verify_email_get(client, memory_token_adapter):
    tokens = await _register(client)
    await client.post(
        "/auth/request-verify-email",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    stored_tokens = list(memory_token_adapter._tokens.values())
    verify_token = [t for t in stored_tokens if t["token_type"] == "verification"][0]

    resp = await client.get(f"/auth/verify-email?token={verify_token['token']}")
    assert resp.status_code == 200


async def test_verify_email_invalid_token(client):
    resp = await client.post("/auth/verify-email", json={"token": "invalid-token"})
    assert resp.status_code == 400


async def test_forgot_password(client):
    await _register(client)
    resp = await client.post(
        "/auth/forgot-password", json={"email": "test@example.com"}
    )
    assert resp.status_code == 200
    assert (
        "reset link" in resp.json()["message"].lower()
        or "sent" in resp.json()["message"].lower()
    )


async def test_forgot_password_nonexistent_email(client):
    resp = await client.post(
        "/auth/forgot-password", json={"email": "nobody@example.com"}
    )
    # Should still return 200 to prevent user enumeration
    assert resp.status_code == 200


async def test_reset_password(client, memory_token_adapter):
    await _register(client)
    await client.post("/auth/forgot-password", json={"email": "test@example.com"})

    stored_tokens = list(memory_token_adapter._tokens.values())
    reset_token = [t for t in stored_tokens if t["token_type"] == "password_reset"][0]

    resp = await client.post(
        "/auth/reset-password",
        json={"token": reset_token["token"], "new_password": "NewPass456#"},
    )
    assert resp.status_code == 200

    # Verify login with new password works
    login_resp = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "NewPass456#"},
    )
    assert login_resp.status_code == 200


async def test_reset_password_invalid_token(client):
    resp = await client.post(
        "/auth/reset-password",
        json={"token": "invalid-token", "new_password": "NewPass456#"},
    )
    assert resp.status_code == 400
