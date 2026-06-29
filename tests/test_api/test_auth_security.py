import pytest
from fastapi import FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import MemoryTokenAdapter, MemoryUserAdapter
from fastauth.config import FastAuthConfig, JWTConfig, PasswordConfig
from fastauth.email_transports.console import ConsoleTransport
from fastauth.providers.credentials import CredentialsProvider
from httpx import ASGITransport, AsyncClient

_STRICT = PasswordConfig(
    min_length=12,
    require_uppercase=True,
    require_lowercase=True,
    require_digit=True,
    require_special=True,
)


def _build_app(password: PasswordConfig | None = None):
    user_adapter = MemoryUserAdapter()
    token_adapter = MemoryTokenAdapter()
    config = FastAuthConfig(
        secret="this-is-a-test-secret-32-bytes!!",
        providers=[CredentialsProvider()],
        adapter=user_adapter,
        token_adapter=token_adapter,
        jwt=JWTConfig(algorithm="HS256"),
        password=password or PasswordConfig(),
        email_transport=ConsoleTransport(),
        base_url="http://localhost:8000",
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    return app, user_adapter, token_adapter


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _extract_token(capsys) -> str:
    out = capsys.readouterr().out
    for line in out.splitlines():
        if "token=" in line:
            tail = line.split("token=", 1)[1]
            raw = ""
            for ch in tail:
                if ch.isalnum() or ch in "-_.":
                    raw += ch
                else:
                    break
            if raw:
                return raw
    raise AssertionError(f"Could not find token= in console output:\n{out}")


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


async def test_weak_password_on_change_rejected():
    app, _, _ = _build_app(password=_STRICT)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={
                "email": "wk@example.com",
                "password": "InitialPass123!@#",
                "name": "T",
            },
        )
        assert resp.status_code == 201
        access = resp.json()["access_token"]

        resp = await c.post(
            "/auth/account/change-password",
            json={
                "current_password": "InitialPass123!@#",
                "new_password": "short",
            },
            headers=_auth(access),
        )
        assert resp.status_code == 400


async def test_strong_password_on_change_succeeds():
    app, _, _ = _build_app(password=_STRICT)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={
                "email": "ok@example.com",
                "password": "InitialPass123!@#",
                "name": "T",
            },
        )
        assert resp.status_code == 201
        access = resp.json()["access_token"]

        resp = await c.post(
            "/auth/account/change-password",
            json={
                "current_password": "InitialPass123!@#",
                "new_password": "SuperSafe123!@#",
            },
            headers=_auth(access),
        )
        assert resp.status_code == 200


async def test_weak_password_on_reset_rejected(capsys):
    app, _, _ = _build_app(password=_STRICT)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post(
            "/auth/register",
            json={
                "email": "rst@example.com",
                "password": "InitialPass123!@#",
                "name": "T",
            },
        )
        await c.post("/auth/forgot-password", json={"email": "rst@example.com"})

        token = _extract_token(capsys)

        resp = await c.post(
            "/auth/reset-password",
            json={"token": token, "new_password": "short"},
        )
        assert resp.status_code == 400


async def test_strong_password_on_reset_succeeds(capsys):
    app, _, _ = _build_app(password=_STRICT)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post(
            "/auth/register",
            json={
                "email": "rstok@example.com",
                "password": "InitialPass123!@#",
                "name": "T",
            },
        )
        await c.post("/auth/forgot-password", json={"email": "rstok@example.com"})

        token = _extract_token(capsys)

        resp = await c.post(
            "/auth/reset-password",
            json={"token": token, "new_password": "SuperSafe123!@#"},
        )
        assert resp.status_code == 200

