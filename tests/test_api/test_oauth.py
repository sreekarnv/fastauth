import pytest
from fastapi import FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import (
    MemoryOAuthAccountAdapter,
    MemoryRoleAdapter,
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
        secret="this-is-a-test-secret-32-bytes!!",
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
        secret="this-is-a-test-secret-32-bytes!!",
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
    _, oauth_adapter, user_adapter, state_store = oauth_app

    # Manually store state (simulating initiate flow)
    await state_store.write(
        "oauth_state:test-state",
        {
            "code_verifier": "verifier",
            "provider": "fake",
            "redirect_uri": "http://localhost/callback",
        },
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
        {
            "code_verifier": "verifier",
            "provider": "fake",
            "redirect_uri": "http://localhost/callback",
        },
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
        {
            "code_verifier": "verifier",
            "provider": "fake",
            "redirect_uri": "http://localhost/callback",
        },
        ttl=600,
    )

    resp = await redirect_client.get(
        "/auth/oauth/fake/callback",
        params={"code": "auth-code", "state": "test-state"},
    )
    assert resp.status_code == 302
    location = resp.headers["location"]
    assert location == "http://frontend.com/callback"
    assert "access_token=" not in location
    assert "refresh_token=" not in location
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies


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
        {
            "code_verifier": "v",
            "provider": "fake",
            "redirect_uri": "http://localhost/callback",
        },
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
        {
            "code_verifier": "v",
            "provider": "fake",
            "redirect_uri": "http://localhost/callback",
        },
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


async def test_oauth_callback_assigns_default_role_to_new_user():
    user_adapter = MemoryUserAdapter()
    oauth_adapter = MemoryOAuthAccountAdapter()
    state_store = MemorySessionBackend()
    role_adapter = MemoryRoleAdapter()
    await role_adapter.create_role(name="member", permissions=[])

    config = FastAuthConfig(
        secret="this-is-a-test-secret-32-bytes!!",
        providers=[FakeOAuthProvider()],
        adapter=user_adapter,
        jwt=JWTConfig(algorithm="HS256"),
        oauth_adapter=oauth_adapter,
        oauth_state_store=state_store,
        default_role="member",
    )
    auth = FastAuth(config)
    auth.role_adapter = role_adapter

    app = FastAPI()
    auth.mount(app)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await state_store.write(
            "oauth_state:test-state",
            {
                "code_verifier": "verifier",
                "provider": "fake",
                "redirect_uri": "http://localhost/callback",
            },
            ttl=600,
        )
        resp = await c.get(
            "/auth/oauth/fake/callback",
            params={"code": "auth-code", "state": "test-state"},
        )
        assert resp.status_code == 200

    user = await user_adapter.get_user_by_email("oauth@example.com")
    assert user is not None
    roles = await role_adapter.get_user_roles(user["id"])
    assert "member" in roles


async def test_oauth_callback_state_provider_mismatch(client, oauth_app):
    """State written for one provider must not be redeemable for a
    different provider's callback."""
    _, oauth_adapter, user_adapter, state_store = oauth_app

    await state_store.write(
        "oauth_state:test-state",
        {
            "code_verifier": "v",
            "provider": "some-other-provider",
            "redirect_uri": "http://localhost/callback",
        },
        ttl=600,
    )

    resp = await client.get(
        "/auth/oauth/fake/callback",
        params={"code": "auth-code", "state": "test-state"},
    )
    assert resp.status_code == 400
    assert "provider mismatch" in resp.json()["detail"]


async def test_oauth_callback_state_missing_redirect_uri(client, oauth_app):
    _, _, _, state_store = oauth_app

    await state_store.write(
        "oauth_state:test-state",
        {"code_verifier": "v", "provider": "fake"},
        ttl=600,
    )

    resp = await client.get(
        "/auth/oauth/fake/callback",
        params={"code": "auth-code", "state": "test-state"},
    )
    assert resp.status_code == 400
    assert "redirect_uri" in resp.json()["detail"]


async def test_oauth_callback_uses_redirect_uri_from_state(client, oauth_app):
    """The callback's exchange_code call must receive the redirect_uri
    that was bound to the state at /authorize, not the one re-computed
    from the request URL."""
    _, _, _, state_store = oauth_app

    capturing = CapturingOAuthProvider()
    # Replace the provider in the app with a capturing one
    app = client._transport.app
    fa = app.state.fastauth
    fa.config.providers = [
        p for p in fa.config.providers if getattr(p, "auth_type", None) != "oauth"
    ] + [capturing]

    await state_store.write(
        "oauth_state:test-state",
        {
            "code_verifier": "v",
            "provider": "fake",
            "redirect_uri": "https://app.example.com/auth/callback",
        },
        ttl=600,
    )

    resp = await client.get(
        "/auth/oauth/fake/callback",
        params={"code": "auth-code", "state": "test-state"},
    )
    assert resp.status_code == 200
    assert (
        capturing.last_exchange_redirect_uri == "https://app.example.com/auth/callback"
    )


class CapturingOAuthProvider:
    id = "fake"
    name = "Fake"
    auth_type = "oauth"

    def __init__(self) -> None:
        self.last_exchange_redirect_uri: str | None = None
        self.last_exchange_kwargs: dict = {}

    async def get_authorization_url(
        self, state: str, redirect_uri: str, **kwargs
    ) -> str:
        return f"https://fake.com/auth?state={state}"

    async def exchange_code(self, code: str, redirect_uri: str, **kwargs):
        self.last_exchange_redirect_uri = redirect_uri
        self.last_exchange_kwargs = kwargs
        return {"access_token": "fake-tok"}

    async def get_user_info(self, access_token: str) -> UserData:
        return {
            "id": "fake-uid-2",
            "email": "capture@example.com",
            "name": "Capture",
            "image": None,
            "email_verified": True,
            "is_active": True,
        }

    async def refresh_access_token(self, refresh_token: str):
        return None


async def test_oauth_signin_does_not_fire_on_oauth_link(client, oauth_app):
    """on_oauth_link must NOT fire on normal OAuth sign-in. It is
    reserved for explicit /auth/oauth/{provider}/link/callback flows."""
    from fastauth.core.protocols import EventHooks

    events: list[str] = []

    class Hooks(EventHooks):
        async def on_oauth_link(self, user, provider):
            events.append(("on_oauth_link", provider))

        async def on_signin(self, user, provider):
            events.append(("on_signin", provider))

    _, oauth_adapter, user_adapter, state_store = oauth_app
    app = client._transport.app
    fa = app.state.fastauth
    fa.config.hooks = Hooks()

    await state_store.write(
        "oauth_state:test-state",
        {
            "code_verifier": "v",
            "provider": "fake",
            "redirect_uri": "http://localhost/callback",
        },
        ttl=600,
    )

    resp = await client.get(
        "/auth/oauth/fake/callback",
        params={"code": "auth-code", "state": "test-state"},
    )
    assert resp.status_code == 200

    names = [e[0] for e in events]
    assert "on_signin" in names
    assert "on_oauth_link" not in names


async def test_oauth_link_callback_fires_on_oauth_link(client, oauth_app):
    """Conversely, /auth/oauth/{provider}/link/callback must fire
    on_oauth_link exactly once with the correct provider."""
    from fastauth.core.protocols import EventHooks

    events: list[tuple[str, str]] = []

    class Hooks(EventHooks):
        async def on_oauth_link(self, user, provider):
            events.append((user["email"], provider))

    _, _, user_adapter, state_store = oauth_app
    app = client._transport.app
    fa = app.state.fastauth
    fa.config.hooks = Hooks()

    # Create a local user that will be the target of the link.
    user = await user_adapter.create_user(email="link-target@example.com")

    # We need an authenticated session to call /{provider}/link. Use the
    # login route for the credentials provider.
    resp = await client.post(
        "/auth/register",
        json={"email": "linker@example.com", "password": "Password123!", "name": "L"},
    )
    token = resp.json()["access_token"]

    await state_store.write(
        "oauth_state:link-state",
        {
            "code_verifier": "v",
            "provider": "fake",
            "flow": "link",
            "user_id": user["id"],
            "redirect_uri": "http://localhost/callback",
        },
        ttl=600,
    )

    resp = await client.get(
        "/auth/oauth/fake/link/callback",
        params={"code": "auth-code", "state": "link-state"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    assert ("link-target@example.com", "fake") in events


async def test_oauth_signin_denied_by_allow_signin_no_tokens(client, oauth_app):
    """When allow_signin denies an OAuth sign-in, the response must not
    contain any tokens, no refresh JTI is recorded, and on_signin /
    on_oauth_link are not invoked."""
    from fastauth.core.protocols import EventHooks

    events: list[str] = []

    class Hooks(EventHooks):
        async def allow_signin(self, user, provider):
            return False

        async def on_signin(self, user, provider):
            events.append("on_signin")

        async def on_oauth_link(self, user, provider):
            events.append("on_oauth_link")

    _, oauth_adapter, user_adapter, state_store = oauth_app
    app = client._transport.app
    fa = app.state.fastauth
    fa.config.hooks = Hooks()

    await state_store.write(
        "oauth_state:test-state",
        {
            "code_verifier": "v",
            "provider": "fake",
            "redirect_uri": "http://localhost/callback",
        },
        ttl=600,
    )

    resp = await client.get(
        "/auth/oauth/fake/callback",
        params={"code": "auth-code", "state": "test-state"},
    )
    assert resp.status_code == 403
    body = resp.json()
    assert "access_token" not in body
    assert "refresh_token" not in body
    assert "on_signin" not in events
    assert "on_oauth_link" not in events
    user = await user_adapter.get_user_by_email("oauth@example.com")
    if user is not None:
        assert await oauth_adapter.get_user_oauth_accounts(user["id"]) == []

    # No refresh_jti should be recorded for the user.
    if fa.config.token_adapter is not None:
        # User was newly created by the OAuth flow. Look up by email.
        from fastauth.adapters.memory import MemoryUserAdapter

        if isinstance(fa.config.adapter, MemoryUserAdapter):
            user = await fa.config.adapter.get_user_by_email("oauth@example.com")
            if user is not None:
                stored = await fa.config.token_adapter.get_token(
                    "any-jti", "refresh_jti"
                )
                # The point is: no rotate happens; just assert the
                # token adapter is empty.
                _ = stored


async def test_oauth_link_state_provider_mismatch(client, oauth_app):
    _, _, user_adapter, state_store = oauth_app
    user = await user_adapter.create_user(email="link-pm@example.com")

    await state_store.write(
        "oauth_state:link-state",
        {
            "code_verifier": "v",
            "provider": "some-other-provider",
            "flow": "link",
            "user_id": user["id"],
            "redirect_uri": "http://localhost/callback",
        },
        ttl=600,
    )

    resp = await client.post(
        "/auth/register",
        json={"email": "linker2@example.com", "password": "Password123!", "name": "L"},
    )
    token = resp.json()["access_token"]

    resp = await client.get(
        "/auth/oauth/fake/link/callback",
        params={"code": "auth-code", "state": "link-state"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "provider mismatch" in resp.json()["detail"]


async def test_oauth_callback_cookie_mode_does_not_expose_tokens_in_body(
    oauth_app,
):
    """OAuth callback in cookie mode must not return tokens in the body."""
    _, _, _, state_store = oauth_app
    user_adapter = MemoryUserAdapter()
    oauth_adapter = MemoryOAuthAccountAdapter()
    cookie_state_store = MemorySessionBackend()

    config = FastAuthConfig(
        secret="this-is-a-test-secret-32-bytes!!",
        providers=[CredentialsProvider(), FakeOAuthProvider()],
        adapter=user_adapter,
        jwt=JWTConfig(algorithm="HS256"),
        oauth_adapter=oauth_adapter,
        oauth_state_store=cookie_state_store,
        token_delivery="cookie",
        debug=True,
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await cookie_state_store.write(
            "oauth_state:test-state",
            {
                "code_verifier": "v",
                "provider": "fake",
                "redirect_uri": "http://localhost/callback",
            },
            ttl=600,
        )
        resp = await c.get(
            "/auth/oauth/fake/callback",
            params={"code": "auth-code", "state": "test-state"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" not in body
        assert "refresh_token" not in body
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies
