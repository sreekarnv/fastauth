from datetime import datetime, timedelta, timezone

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
        secret="this-is-a-test-secret-32-bytes!!",
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
        secret="this-is-a-test-secret-32-bytes!!",
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


async def test_revoke_session(session_client, session_app):
    token = await _register_and_login(session_client)
    user = await _user_id_from_token(session_app, token)
    await session_app.state.fastauth.session_adapter.create_session(
        {
            "id": "owned-session",
            "user_id": user,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "ip_address": None,
            "user_agent": None,
        }
    )
    resp = await session_client.delete(
        "/auth/sessions/owned-session",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Session revoked"


async def test_revoke_session_not_owned_returns_404(session_client, session_app):
    token = await _register_and_login(session_client)
    user = await _user_id_from_token(session_app, token)
    await session_app.state.fastauth.session_adapter.create_session(
        {
            "id": "other-session",
            "user_id": f"not-{user}",
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "ip_address": None,
            "user_agent": None,
        }
    )
    resp = await session_client.delete(
        "/auth/sessions/other-session",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_revoke_session_missing_returns_404(session_client):
    token = await _register_and_login(session_client)
    resp = await session_client.delete(
        "/auth/sessions/does-not-exist",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def _user_id_from_token(app, token: str) -> str:
    from fastauth.core.tokens import decode_token

    claims = decode_token(
        token, app.state.fastauth.config, app.state.fastauth.jwks_manager
    )
    return claims["sub"]


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
