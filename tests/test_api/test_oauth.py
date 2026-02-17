import pytest
from fastapi import FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import (
    MemoryOAuthAccountAdapter,
    MemoryUserAdapter,
)
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.providers.credentials import CredentialsProvider
from fastauth.session_backends.memory import MemorySessionBackend
from fastauth.types import UserData
from httpx import ASGITransport, AsyncClient


class FakeOAuthProvider:
    id = "fake"
    name = "Fake"
    auth_type = "oauth"

    async def get_authorization_url(
        self, state: str, redirect_uri: str, **kwargs
    ) -> str:
        return f"https://fake.com/auth?state={state}"

    async def exchange_code(self, code: str, redirect_uri: str, **kwargs):
        return {"access_token": "fake-tok"}

    async def get_user_info(self, access_token: str) -> UserData:
        return {
            "id": "fake-uid-1",
            "email": "oauth@example.com",
            "name": "OAuth User",
            "image": None,
            "email_verified": True,
            "is_active": True,
        }

    async def refresh_access_token(self, refresh_token: str):
        return None


@pytest.fixture
def oauth_app():
    user_adapter = MemoryUserAdapter()
    oauth_adapter = MemoryOAuthAccountAdapter()
    state_store = MemorySessionBackend()

    config = FastAuthConfig(
        secret="test-secret-for-oauth",
        providers=[CredentialsProvider(), FakeOAuthProvider()],
        adapter=user_adapter,
        jwt=JWTConfig(algorithm="HS256"),
        oauth_adapter=oauth_adapter,
        oauth_state_store=state_store,
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    return app, oauth_adapter, user_adapter, state_store


@pytest.fixture
def oauth_redirect_app():
    config = FastAuthConfig(
        secret="test-secret-for-oauth",
        providers=[CredentialsProvider(), FakeOAuthProvider()],
        adapter=MemoryUserAdapter(),
        jwt=JWTConfig(algorithm="HS256"),
        oauth_adapter=MemoryOAuthAccountAdapter(),
        oauth_state_store=MemorySessionBackend(),
        oauth_redirect_url="http://frontend.com/callback",
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    return app


@pytest.fixture
async def client(oauth_app):
    app, _, _, _ = oauth_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def redirect_client(oauth_redirect_app):
    transport = ASGITransport(app=oauth_redirect_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        follow_redirects=False,
    ) as c:
        yield c


async def test_authorize(client):
    resp = await client.get(
        "/auth/oauth/fake/authorize",
        params={"redirect_uri": "http://localhost/callback"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    assert "https://fake.com/auth" in data["url"]


async def test_authorize_unknown_provider(client):
    resp = await client.get(
        "/auth/oauth/unknown/authorize",
        params={"redirect_uri": "http://localhost/callback"},
    )
    assert resp.status_code == 404


async def test_callback_json_mode(client, oauth_app):
    _, _, _, state_store = oauth_app

    # Manually store state (simulating initiate flow)
    await state_store.write(
        "oauth_state:test-state",
        {"code_verifier": "verifier", "provider": "fake"},
        ttl=600,
    )

    resp = await client.get(
        "/auth/oauth/fake/callback",
        params={"code": "auth-code", "state": "test-state"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_callback_creates_user(client, oauth_app):
    _, _, user_adapter, state_store = oauth_app

    await state_store.write(
        "oauth_state:test-state",
        {"code_verifier": "verifier", "provider": "fake"},
        ttl=600,
    )

    await client.get(
        "/auth/oauth/fake/callback",
        params={"code": "auth-code", "state": "test-state"},
    )

    user = await user_adapter.get_user_by_email("oauth@example.com")
    assert user is not None


async def test_callback_redirect_mode(redirect_client, oauth_redirect_app):
    state_store = oauth_redirect_app.state.fastauth.config.oauth_state_store

    await state_store.write(
        "oauth_state:test-state",
        {"code_verifier": "verifier", "provider": "fake"},
        ttl=600,
    )

    resp = await redirect_client.get(
        "/auth/oauth/fake/callback",
        params={"code": "auth-code", "state": "test-state"},
    )
    assert resp.status_code == 302
    location = resp.headers["location"]
    assert location.startswith("http://frontend.com/callback?")
    assert "access_token=" in location


async def test_callback_invalid_state(client):
    resp = await client.get(
        "/auth/oauth/fake/callback",
        params={"code": "auth-code", "state": "bad-state"},
    )
    assert resp.status_code == 400


async def test_list_accounts_empty(client):
    await client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "Password123!",
            "name": "Test",
        },
    )
    resp = await client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "Password123!",
        },
    )
    token = resp.json()["access_token"]

    resp = await client.get(
        "/auth/oauth/accounts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_accounts_with_linked(client, oauth_app):
    _, oauth_adapter, _, state_store = oauth_app

    await state_store.write(
        "oauth_state:s1",
        {"code_verifier": "v", "provider": "fake"},
        ttl=600,
    )
    resp = await client.get(
        "/auth/oauth/fake/callback",
        params={"code": "c", "state": "s1"},
    )
    token = resp.json()["access_token"]

    resp = await client.get(
        "/auth/oauth/accounts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    accounts = resp.json()
    assert len(accounts) == 1
    assert accounts[0]["provider"] == "fake"


async def test_unlink_account(client, oauth_app):
    _, oauth_adapter, _, state_store = oauth_app

    await state_store.write(
        "oauth_state:s1",
        {"code_verifier": "v", "provider": "fake"},
        ttl=600,
    )
    resp = await client.get(
        "/auth/oauth/fake/callback",
        params={"code": "c", "state": "s1"},
    )
    token = resp.json()["access_token"]

    resp = await client.delete(
        "/auth/oauth/accounts/fake",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Account unlinked"

    resp = await client.get(
        "/auth/oauth/accounts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.json() == []


async def test_unlink_nonexistent(client):
    await client.post(
        "/auth/register",
        json={
            "email": "user2@example.com",
            "password": "Password123!",
            "name": "Test",
        },
    )
    resp = await client.post(
        "/auth/login",
        json={
            "email": "user2@example.com",
            "password": "Password123!",
        },
    )
    token = resp.json()["access_token"]

    resp = await client.delete(
        "/auth/oauth/accounts/fake",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_unauthenticated_accounts(client):
    resp = await client.get("/auth/oauth/accounts")
    assert resp.status_code == 401
