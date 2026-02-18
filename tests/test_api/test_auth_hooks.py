import pytest
from fastapi import FastAPI
from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.memory import MemoryTokenAdapter, MemoryUserAdapter
from fastauth.core.protocols import EventHooks
from fastauth.providers.credentials import CredentialsProvider
from httpx import ASGITransport, AsyncClient

_EMAIL = "hooks@example.com"
_PASSWORD = "Pass123#"
_REGISTER = {"email": _EMAIL, "password": _PASSWORD, "name": "H"}


class RecordingHooks(EventHooks):
    def __init__(self):
        self.calls: list[str] = []

    async def on_signup(self, user):
        self.calls.append("on_signup")

    async def on_signin(self, user, provider):
        self.calls.append(f"on_signin:{provider}")

    async def on_signout(self, user):
        self.calls.append("on_signout")

    async def on_token_refresh(self, user):
        self.calls.append("on_token_refresh")

    async def on_email_verify(self, user):
        self.calls.append("on_email_verify")

    async def on_password_reset(self, user):
        self.calls.append("on_password_reset")


@pytest.fixture
def hooks():
    return RecordingHooks()


@pytest.fixture
def hooks_app(hooks):
    adapter = MemoryUserAdapter()
    config = FastAuthConfig(
        secret="super-secret-key-only-for-testing",
        providers=[CredentialsProvider()],
        adapter=adapter,
        hooks=hooks,
    )
    auth = FastAuth(config)
    _app = FastAPI()
    auth.mount(_app)
    return _app


@pytest.fixture
async def hooks_client(hooks_app):
    transport = ASGITransport(app=hooks_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_register_calls_on_signup(hooks_client, hooks):
    resp = await hooks_client.post("/auth/register", json=_REGISTER)
    assert resp.status_code == 201
    assert "on_signup" in hooks.calls


async def test_login_calls_on_signin(hooks_client, hooks):
    await hooks_client.post("/auth/register", json=_REGISTER)
    hooks.calls.clear()
    resp = await hooks_client.post(
        "/auth/login", json={"email": _EMAIL, "password": _PASSWORD}
    )
    assert resp.status_code == 200
    assert "on_signin:credentials" in hooks.calls


async def test_logout_calls_on_signout(hooks_client, hooks):
    resp = await hooks_client.post("/auth/register", json=_REGISTER)
    token = resp.json()["access_token"]
    hooks.calls.clear()
    resp = await hooks_client.post(
        "/auth/logout", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert "on_signout" in hooks.calls


async def test_refresh_calls_on_token_refresh(hooks_client, hooks):
    resp = await hooks_client.post("/auth/register", json=_REGISTER)
    refresh_token = resp.json()["refresh_token"]
    hooks.calls.clear()
    resp = await hooks_client.post(
        "/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 200
    assert "on_token_refresh" in hooks.calls


async def test_refresh_inactive_user_returns_401(hooks_client):
    resp = await hooks_client.post("/auth/register", json=_REGISTER)
    tokens = resp.json()
    refresh_token = tokens["refresh_token"]

    app = hooks_client._transport.app
    fa = app.state.fastauth
    user = await fa.config.adapter.get_user_by_email(_EMAIL)
    await fa.config.adapter.delete_user(user["id"], soft=True)

    resp = await hooks_client.post(
        "/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 401


async def test_refresh_with_access_token_returns_401(hooks_client):
    resp = await hooks_client.post("/auth/register", json=_REGISTER)
    access_token = resp.json()["access_token"]
    resp = await hooks_client.post(
        "/auth/refresh", json={"refresh_token": access_token}
    )
    assert resp.status_code == 401


async def test_register_no_credentials_provider():

    class DummyProvider:
        id = "dummy"
        name = "Dummy"
        auth_type = "credentials"

        async def authenticate(self, **kwargs):
            return None

    adapter = MemoryUserAdapter()
    config = FastAuthConfig(
        secret="super-secret-key-only-for-testing",
        providers=[DummyProvider()],
        adapter=adapter,
    )
    auth = FastAuth(config)
    _app = FastAPI()
    auth.mount(_app)

    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post("/auth/register", json=_REGISTER)
        assert resp.status_code == 400
        resp = await c.post(
            "/auth/login", json={"email": _EMAIL, "password": _PASSWORD}
        )
        assert resp.status_code == 400


async def test_get_current_user_non_access_token_returns_none(hooks_client):
    resp = await hooks_client.post("/auth/register", json=_REGISTER)
    refresh_token = resp.json()["refresh_token"]

    resp = await hooks_client.get(
        "/auth/me", headers={"Authorization": f"Bearer {refresh_token}"}
    )
    assert resp.status_code == 401


@pytest.fixture
def hooks_with_email_app(hooks):
    adapter = MemoryUserAdapter()
    token_adapter = MemoryTokenAdapter()
    config = FastAuthConfig(
        secret="super-secret-key-only-for-testing",
        providers=[CredentialsProvider()],
        adapter=adapter,
        token_adapter=token_adapter,
        hooks=hooks,
    )
    auth = FastAuth(config)
    _app = FastAPI()
    auth.mount(_app)
    return _app, token_adapter


@pytest.fixture
async def hooks_email_client(hooks_with_email_app):
    _app, _ = hooks_with_email_app
    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_verify_email_calls_hook(hooks_email_client, hooks_with_email_app, hooks):
    _, token_adapter = hooks_with_email_app
    resp = await hooks_email_client.post("/auth/register", json=_REGISTER)
    token = resp.json()["access_token"]
    await hooks_email_client.post(
        "/auth/request-verify-email",
        headers={"Authorization": f"Bearer {token}"},
    )
    hooks.calls.clear()
    stored = list(token_adapter._tokens.values())
    verify_token = next(t for t in stored if t["token_type"] == "verification")
    resp = await hooks_email_client.post(
        "/auth/verify-email", json={"token": verify_token["token"]}
    )
    assert resp.status_code == 200
    assert "on_email_verify" in hooks.calls


async def test_reset_password_calls_hook(
    hooks_email_client, hooks_with_email_app, hooks
):
    _, token_adapter = hooks_with_email_app
    await hooks_email_client.post("/auth/register", json=_REGISTER)
    await hooks_email_client.post("/auth/forgot-password", json={"email": _EMAIL})
    hooks.calls.clear()
    stored = list(token_adapter._tokens.values())
    reset_token = next(t for t in stored if t["token_type"] == "password_reset")
    resp = await hooks_email_client.post(
        "/auth/reset-password",
        json={"token": reset_token["token"], "new_password": "NewPass456#"},
    )
    assert resp.status_code == 200
    assert "on_password_reset" in hooks.calls
