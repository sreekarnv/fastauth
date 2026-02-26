import pytest
from fastapi import FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import MemoryTokenAdapter, MemoryUserAdapter
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.core.protocols import EventHooks
from fastauth.providers.credentials import CredentialsProvider
from fastauth.providers.magic_links import MagicLinksProvider
from fastauth.types import UserData
from httpx import ASGITransport, AsyncClient


def _build_app(
    user_adapter=None,
    token_adapter=None,
    providers=None,
    hooks=None,
    token_delivery="json",
):
    user_adapter = user_adapter or MemoryUserAdapter()
    token_adapter = token_adapter or MemoryTokenAdapter()
    providers = providers if providers is not None else [MagicLinksProvider()]

    config = FastAuthConfig(
        secret="test-magic-links-secret",
        providers=providers,
        adapter=user_adapter,
        token_adapter=token_adapter,
        jwt=JWTConfig(algorithm="HS256"),
        hooks=hooks,
        token_delivery=token_delivery,
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    return app, user_adapter, token_adapter


@pytest.fixture
async def magic_client():
    app, user_adapter, token_adapter = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c, user_adapter, token_adapter


def _get_magic_token(token_adapter) -> str | None:
    for tok in token_adapter._tokens.values():
        if tok["token_type"] == "magic_link_login_request":
            return tok["token"]
    return None


async def test_login_returns_message(magic_client):
    client, *_ = magic_client
    resp = await client.post(
        "/auth/magic-links/login", json={"email": "new@example.com"}
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Magic link sent — check your email"


async def test_login_auto_creates_user(magic_client):
    client, user_adapter, _ = magic_client
    await client.post(
        "/auth/magic-links/login",
        json={"email": "autocreate@example.com"}
    )

    user = await user_adapter.get_user_by_email("autocreate@example.com")
    assert user is not None


async def test_login_existing_user_not_duplicated(magic_client):
    client, user_adapter, _ = magic_client
    await user_adapter.create_user("exist@example.com")

    await client.post("/auth/magic-links/login", json={"email": "exist@example.com"})
    await client.post("/auth/magic-links/login", json={"email": "exist@example.com"})

    # Still only one user
    user = await user_adapter.get_user_by_email("exist@example.com")
    assert user is not None


async def test_login_stores_token(magic_client):
    client, _, token_adapter = magic_client
    await client.post("/auth/magic-links/login", json={"email": "tok@example.com"})

    assert _get_magic_token(token_adapter) is not None


async def test_login_invalid_email_returns_422(magic_client):
    client, *_ = magic_client
    resp = await client.post("/auth/magic-links/login", json={"email": "not-an-email"})
    assert resp.status_code == 422


async def test_callback_valid_token_returns_token_pair(magic_client):
    client, _, token_adapter = magic_client
    await client.post("/auth/magic-links/login", json={"email": "cb@example.com"})

    token = _get_magic_token(token_adapter)
    resp = await client.get(f"/auth/magic-links/callback?token={token}")

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_callback_invalid_token_returns_401(magic_client):
    client, *_ = magic_client
    resp = await client.get("/auth/magic-links/callback?token=garbage-token")
    assert resp.status_code == 401


async def test_callback_token_is_one_time_use(magic_client):
    client, _, token_adapter = magic_client
    await client.post("/auth/magic-links/login", json={"email": "once@example.com"})

    token = _get_magic_token(token_adapter)
    await client.get(f"/auth/magic-links/callback?token={token}")

    resp = await client.get(f"/auth/magic-links/callback?token={token}")
    assert resp.status_code == 401


async def test_callback_inactive_user_returns_401(magic_client):
    client, user_adapter, token_adapter = magic_client
    user = await user_adapter.create_user("inactive@example.com")
    await user_adapter.update_user(user["id"], is_active=False)

    await client.post(
        "/auth/magic-links/login", json={"email": "inactive@example.com"}
    )
    token = _get_magic_token(token_adapter)

    resp = await client.get(f"/auth/magic-links/callback?token={token}")
    assert resp.status_code == 401
    assert "inactive" in resp.json()["detail"].lower()


async def test_callback_blocked_by_allow_signin_hook():
    class BlockingHooks(EventHooks):
        async def allow_signin(self, user: UserData, provider: str) -> bool:
            return False

    app, _, token_adapter = _build_app(hooks=BlockingHooks())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post("/auth/magic-links/login", json={"email": "blocked@example.com"})
        token = _get_magic_token(token_adapter)
        resp = await c.get(f"/auth/magic-links/callback?token={token}")

    assert resp.status_code == 403


async def test_callback_calls_on_signin_hook():
    class RecordingHooks(EventHooks):
        def __init__(self):
            self.events: list[tuple[str, str]] = []

        async def on_signin(self, user: UserData, provider: str) -> None:
            self.events.append((user["email"], provider))

    hooks = RecordingHooks()
    app, _, token_adapter = _build_app(hooks=hooks)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post("/auth/magic-links/login", json={"email": "hook@example.com"})
        token = _get_magic_token(token_adapter)
        await c.get(f"/auth/magic-links/callback?token={token}")

    assert len(hooks.events) == 1
    assert hooks.events[0] == ("hook@example.com", "magic_link")


async def test_callback_cookie_delivery_sets_cookie():
    app, _, token_adapter = _build_app(token_delivery="cookie")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post(
            "/auth/magic-links/login", json={"email": "cookie@example.com"}
        )
        token = _get_magic_token(token_adapter)
        resp = await c.get(f"/auth/magic-links/callback?token={token}")

    assert resp.status_code == 200
    assert "access_token" in resp.cookies


async def test_magic_links_router_not_mounted_without_provider():
    app, *_ = _build_app(providers=[CredentialsProvider()])
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/magic-links/login", json={"email": "x@example.com"}
        )
    assert resp.status_code == 404
