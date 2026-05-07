import pytest
from fastapi import FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import MemoryTokenAdapter, MemoryUserAdapter
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.providers.credentials import CredentialsProvider
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def token_app():
    user_adapter = MemoryUserAdapter()
    token_adapter = MemoryTokenAdapter()
    config = FastAuthConfig(
        secret="test-secret-for-tokens",
        providers=[CredentialsProvider()],
        adapter=user_adapter,
        token_adapter=token_adapter,
        jwt=JWTConfig(algorithm="HS256"),
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    return app, user_adapter, token_adapter


@pytest.fixture
def no_token_adapter_app():
    config = FastAuthConfig(
        secret="test-secret-for-tokens",
        providers=[CredentialsProvider()],
        adapter=MemoryUserAdapter(),
        jwt=JWTConfig(algorithm="HS256"),
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    return app


@pytest.fixture
async def client(token_app):
    app, _, _ = token_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def no_adapter_client(no_token_adapter_app):
    transport = ASGITransport(app=no_token_adapter_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _register_and_login(client, remember=False) -> dict:
    await client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "Pass123#"},
    )
    resp = await client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "Pass123#",
            "remember": remember,
        },
    )
    return resp.json()


async def _auth_header(client) -> dict:
    tokens = await _register_and_login(client)
    return {"Authorization": f"Bearer {tokens['access_token']}"}, tokens


async def test_introspect_valid_access_token(client):
    headers, tokens = await _auth_header(client)
    resp = await client.post(
        "/auth/token/introspect",
        json={"token": tokens["access_token"]},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["active"] is True
    assert data["token_type"] == "access"
    assert data["email"] == "user@example.com"


async def test_introspect_valid_refresh_token(client):
    headers, tokens = await _auth_header(client)
    resp = await client.post(
        "/auth/token/introspect",
        json={"token": tokens["refresh_token"]},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["active"] is True
    assert data["token_type"] == "refresh"


async def test_introspect_invalid_token(client):
    headers, _ = await _auth_header(client)
    resp = await client.post(
        "/auth/token/introspect",
        json={"token": "not.a.valid.token"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["active"] is False


async def test_introspect_revoked_refresh_token(client, token_app):
    app, _, __ = token_app
    headers, tokens = await _auth_header(client)

    await client.post(
        "/auth/token/revoke",
        json={"token": tokens["refresh_token"]},
        headers=headers,
    )

    # Introspect should now return active=false
    resp = await client.post(
        "/auth/token/introspect",
        json={"token": tokens["refresh_token"]},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["active"] is False


async def test_introspect_unauthenticated(client):
    resp = await client.post("/auth/token/introspect", json={"token": "anything"})
    assert resp.status_code == 401


async def test_revoke_refresh_token(client):
    headers, tokens = await _auth_header(client)
    resp = await client.post(
        "/auth/token/revoke",
        json={"token": tokens["refresh_token"]},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Token revoked"


async def test_revoke_access_token_rejected(client):
    headers, tokens = await _auth_header(client)
    resp = await client.post(
        "/auth/token/revoke",
        json={"token": tokens["access_token"]},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "refresh" in resp.json()["detail"]


async def test_revoke_invalid_token(client):
    headers, _ = await _auth_header(client)
    resp = await client.post(
        "/auth/token/revoke",
        json={"token": "garbage"},
        headers=headers,
    )
    assert resp.status_code == 400


async def test_revoke_no_token_adapter(no_adapter_client):
    await no_adapter_client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "Pass123#"},
    )
    login = await no_adapter_client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "Pass123#"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await no_adapter_client.post(
        "/auth/token/revoke",
        json={"token": login.json()["refresh_token"]},
        headers=headers,
    )
    assert resp.status_code == 400


async def test_revoke_unauthenticated(client):
    resp = await client.post("/auth/token/revoke", json={"token": "anything"})
    assert resp.status_code == 401


async def test_revoke_another_users_token(token_app):
    app, _, _ = token_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post(
            "/auth/register", json={"email": "a@example.com", "password": "Pass123#"}
        )
        await c.post(
            "/auth/register", json={"email": "b@example.com", "password": "Pass123#"}
        )

        tokens_a = (
            await c.post(
                "/auth/login", json={"email": "a@example.com", "password": "Pass123#"}
            )
        ).json()
        tokens_b = (
            await c.post(
                "/auth/login", json={"email": "b@example.com", "password": "Pass123#"}
            )
        ).json()

        resp = await c.post(
            "/auth/token/revoke",
            json={"token": tokens_b["refresh_token"]},
            headers={"Authorization": f"Bearer {tokens_a['access_token']}"},
        )
        assert resp.status_code == 403
