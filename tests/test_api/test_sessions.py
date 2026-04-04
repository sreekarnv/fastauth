import pytest
from fastapi import FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import (
    MemorySessionAdapter,
    MemoryUserAdapter,
)
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.providers.credentials import CredentialsProvider
from httpx import ASGITransport, AsyncClient


def _make_app_without_session_adapter():
    adapter = MemoryUserAdapter()
    config = FastAuthConfig(
        secret="test-secret-for-sessions",
        providers=[CredentialsProvider()],
        adapter=adapter,
        jwt=JWTConfig(algorithm="HS256"),
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    return app, auth


@pytest.fixture
def session_app():
    adapter = MemoryUserAdapter()
    session_adapter = MemorySessionAdapter()
    config = FastAuthConfig(
        secret="test-secret-for-sessions",
        providers=[CredentialsProvider()],
        adapter=adapter,
        jwt=JWTConfig(algorithm="HS256"),
    )
    auth = FastAuth(config)
    auth.session_adapter = session_adapter

    app = FastAPI()
    auth.mount(app)
    return app


@pytest.fixture
async def session_client(session_app):
    transport = ASGITransport(app=session_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _register_and_login(client: AsyncClient) -> str:
    await client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "Password123!",
            "name": "Test User",
        },
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "Password123!"},
    )
    return resp.json()["access_token"]


async def test_list_sessions(session_client):
    token = await _register_and_login(session_client)
    resp = await session_client.get(
        "/auth/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_sessions_unauthenticated(session_client):
    resp = await session_client.get("/auth/sessions")
    assert resp.status_code == 401


async def test_revoke_session(session_client):
    token = await _register_and_login(session_client)
    resp = await session_client.delete(
        "/auth/sessions/some-session-id",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Session revoked"


async def test_revoke_session_unauthenticated(session_client):
    resp = await session_client.delete("/auth/sessions/some-session-id")
    assert resp.status_code == 401


async def test_revoke_all_sessions(session_client):
    token = await _register_and_login(session_client)
    resp = await session_client.delete(
        "/auth/sessions/all",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "All sessions revoked"


async def test_revoke_all_sessions_unauthenticated(session_client):
    resp = await session_client.delete("/auth/sessions/all")
    assert resp.status_code == 401


async def test_list_sessions_no_adapter():
    app, auth = _make_app_without_session_adapter()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await _register_and_login(c)
        resp = await c.get(
            "/auth/sessions", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 400


async def test_revoke_session_no_adapter():
    app, auth = _make_app_without_session_adapter()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await _register_and_login(c)
        resp = await c.delete(
            "/auth/sessions/abc", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 400


async def test_revoke_all_sessions_no_adapter():
    app, auth = _make_app_without_session_adapter()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await _register_and_login(c)
        resp = await c.delete(
            "/auth/sessions/all", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 400
