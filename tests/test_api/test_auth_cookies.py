import pytest
from fastapi import FastAPI
from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.memory import MemoryTokenAdapter, MemoryUserAdapter
from fastauth.providers.credentials import CredentialsProvider
from httpx import ASGITransport, AsyncClient

_EMAIL = "test@example.com"
_PASSWORD = "Pass123#"
_REGISTER = {"email": _EMAIL, "password": _PASSWORD, "name": "Test"}


@pytest.fixture
def user_adapter():
    return MemoryUserAdapter()


@pytest.fixture
def token_adapter():
    return MemoryTokenAdapter()


@pytest.fixture
def cookie_app(user_adapter, token_adapter):
    config = FastAuthConfig(
        secret="super-secret-key-only-for-testing",
        providers=[CredentialsProvider()],
        adapter=user_adapter,
        token_adapter=token_adapter,
        token_delivery="cookie",
        debug=True,
    )
    auth = FastAuth(config)
    _app = FastAPI()
    auth.mount(_app)
    return _app


@pytest.fixture
async def cookie_client(cookie_app):
    transport = ASGITransport(app=cookie_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def json_app(user_adapter):
    config = FastAuthConfig(
        secret="super-secret-key-only-for-testing",
        providers=[CredentialsProvider()],
        adapter=user_adapter,
    )
    auth = FastAuth(config)
    _app = FastAPI()
    auth.mount(_app)
    return _app


@pytest.fixture
async def json_client(json_app):
    transport = ASGITransport(app=json_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_register_sets_cookies(cookie_client):
    resp = await cookie_client.post("/auth/register", json=_REGISTER)
    assert resp.status_code == 201
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies


async def test_login_sets_cookies(cookie_client):
    await cookie_client.post("/auth/register", json=_REGISTER)
    resp = await cookie_client.post(
        "/auth/login", json={"email": _EMAIL, "password": _PASSWORD}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies


async def test_logout_clears_cookies(cookie_client):
    await cookie_client.post("/auth/register", json=_REGISTER)
    resp = await cookie_client.post("/auth/logout")
    assert resp.status_code == 200
    assert resp.cookies.get("access_token", "") == ""


async def test_refresh_reads_from_cookie(cookie_client):
    await cookie_client.post("/auth/register", json=_REGISTER)
    resp = await cookie_client.post("/auth/refresh")
    assert resp.status_code == 200
    assert "access_token" in resp.cookies


async def test_refresh_no_token_returns_401(cookie_client):
    resp = await cookie_client.post("/auth/refresh")
    assert resp.status_code == 401


async def test_me_authenticated(json_client):
    resp = await json_client.post("/auth/register", json=_REGISTER)
    access_token = resp.json()["access_token"]

    me = await json_client.get(
        "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me.status_code == 200
    data = me.json()
    assert data["email"] == _EMAIL
    assert data["name"] == "Test"
    assert "id" in data
    assert "email_verified" in data
    assert "is_active" in data


async def test_me_unauthenticated(json_client):
    resp = await json_client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_via_cookie(cookie_client):
    await cookie_client.post("/auth/register", json=_REGISTER)
    me = await cookie_client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == _EMAIL


async def test_me_invalid_token(json_client):
    resp = await json_client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert resp.status_code == 401
