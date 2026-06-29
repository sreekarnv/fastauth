import pytest
from fastapi import FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import MemoryTokenAdapter, MemoryUserAdapter
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.providers.credentials import CredentialsProvider
from httpx import ASGITransport, AsyncClient


def _build_app():
    user_adapter = MemoryUserAdapter()
    token_adapter = MemoryTokenAdapter()
    config = FastAuthConfig(
        secret="this-is-a-test-secret-32-bytes!!",
        providers=[CredentialsProvider()],
        adapter=user_adapter,
        token_adapter=token_adapter,
        jwt=JWTConfig(algorithm="HS256"),
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    return app, user_adapter, token_adapter


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_change_password_revokes_old_refresh_jti():
    app, _, _ = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={"email": "sec@example.com", "password": "Pass123#", "name": "T"},
        )
        assert resp.status_code == 201
        access = resp.json()["access_token"]
        refresh = resp.json()["refresh_token"]

        resp = await c.post(
            "/auth/account/change-password",
            json={"current_password": "Pass123#", "new_password": "NewPass456#"},
            headers=_auth(access),
        )
        assert resp.status_code == 200

        resp = await c.post(
            "/auth/refresh", json={"refresh_token": refresh}
        )
        assert resp.status_code == 401
