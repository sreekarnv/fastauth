import pytest
from fastauth.adapters.memory import (
    MemoryOAuthAccountAdapter,
    MemoryUserAdapter,
)
from fastauth.core.oauth import complete_oauth_flow, initiate_oauth_flow
from fastauth.exceptions import ProviderError
from fastauth.session_backends.memory import MemorySessionBackend
from fastauth.types import UserData


class FakeOAuthProvider:
    id = "fake"
    name = "Fake"
    auth_type = "oauth"

    def __init__(self, user_info: UserData | None = None) -> None:
        self._user_info = user_info or {
            "id": "provider-uid-1",
            "email": "oauth@example.com",
            "name": "OAuth User",
            "image": None,
            "email_verified": True,
            "is_active": True,
        }
        self.last_auth_url_kwargs: dict = {}

    async def get_authorization_url(
        self, state: str, redirect_uri: str, **kwargs
    ) -> str:
        self.last_auth_url_kwargs = kwargs
        return f"https://fake.com/auth?state={state}&redirect_uri={redirect_uri}"

    async def exchange_code(self, code: str, redirect_uri: str, **kwargs):
        return {"access_token": "fake-access-token", "refresh_token": "fake-refresh"}

    async def get_user_info(self, access_token: str) -> UserData:
        return self._user_info

    async def refresh_access_token(self, refresh_token: str):
        return None


@pytest.fixture
def state_store():
    return MemorySessionBackend()


@pytest.fixture
def user_adapter():
    return MemoryUserAdapter()


@pytest.fixture
def oauth_adapter():
    return MemoryOAuthAccountAdapter()


@pytest.fixture
def provider():
    return FakeOAuthProvider()


async def test_initiate_stores_state(provider, state_store):
    url, state = await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )
    assert "https://fake.com/auth" in url
    assert state in url

    stored = await state_store.read(f"oauth_state:{state}")
    assert stored is not None
    assert "code_verifier" in stored
    assert stored["provider"] == "fake"


async def test_initiate_passes_pkce(provider, state_store):
    await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )
    assert "code_challenge" in provider.last_auth_url_kwargs
    assert provider.last_auth_url_kwargs["code_challenge_method"] == "S256"


async def test_complete_new_user(provider, state_store, user_adapter, oauth_adapter):
    _, state = await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )

    user, is_new = await complete_oauth_flow(
        provider=provider,
        code="auth-code",
        state=state,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
        user_adapter=user_adapter,
        oauth_adapter=oauth_adapter,
    )

    assert is_new is True
    assert user["email"] == "oauth@example.com"

    accounts = await oauth_adapter.get_user_oauth_accounts(user["id"])
    assert len(accounts) == 1
    assert accounts[0]["provider"] == "fake"


async def test_complete_existing_oauth_account(
    provider, state_store, user_adapter, oauth_adapter
):
    _, state1 = await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )
    user1, _ = await complete_oauth_flow(
        provider=provider,
        code="code1",
        state=state1,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
        user_adapter=user_adapter,
        oauth_adapter=oauth_adapter,
    )

    _, state2 = await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )
    user2, is_new = await complete_oauth_flow(
        provider=provider,
        code="code2",
        state=state2,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
        user_adapter=user_adapter,
        oauth_adapter=oauth_adapter,
    )

    assert is_new is False
    assert user2["id"] == user1["id"]


async def test_complete_links_to_existing_email_user(
    provider, state_store, user_adapter, oauth_adapter
):
    existing = await user_adapter.create_user(
        email="oauth@example.com", hashed_password="hashed"
    )

    _, state = await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )
    user, is_new = await complete_oauth_flow(
        provider=provider,
        code="auth-code",
        state=state,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
        user_adapter=user_adapter,
        oauth_adapter=oauth_adapter,
    )

    assert is_new is False
    assert user["id"] == existing["id"]

    accounts = await oauth_adapter.get_user_oauth_accounts(user["id"])
    assert len(accounts) == 1


async def test_complete_invalid_state(
    provider, state_store, user_adapter, oauth_adapter
):
    with pytest.raises(ProviderError, match="Invalid or expired"):
        await complete_oauth_flow(
            provider=provider,
            code="code",
            state="bad-state",
            redirect_uri="http://localhost/callback",
            state_store=state_store,
            user_adapter=user_adapter,
            oauth_adapter=oauth_adapter,
        )
