import pytest
from fastauth.adapters.memory import (
    MemoryOAuthAccountAdapter,
    MemoryUserAdapter,
)
from fastauth.core.oauth import (
    complete_oauth_flow,
    initiate_oauth_flow,
    link_oauth_account,
)
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

    user, is_new, email_verified_now = await complete_oauth_flow(
        provider=provider,
        code="auth-code",
        state=state,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
        user_adapter=user_adapter,
        oauth_adapter=oauth_adapter,
    )

    assert is_new is True
    assert email_verified_now is True
    assert user["email"] == "oauth@example.com"
    assert user["email_verified"] is True

    accounts = await oauth_adapter.get_user_oauth_accounts(user["id"])
    assert len(accounts) == 1
    assert accounts[0]["provider"] == "fake"


async def test_complete_new_user_with_unverified_email(
    state_store, user_adapter, oauth_adapter
):
    provider = FakeOAuthProvider(
        {
            "id": "provider-uid-1",
            "email": "oauth@example.com",
            "name": "OAuth User",
            "image": None,
            "email_verified": False,
            "is_active": True,
        }
    )
    _, state = await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )

    user, is_new, email_verified_now = await complete_oauth_flow(
        provider=provider,
        code="auth-code",
        state=state,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
        user_adapter=user_adapter,
        oauth_adapter=oauth_adapter,
    )

    assert is_new is True
    assert email_verified_now is False
    assert user["email_verified"] is False


async def test_complete_existing_oauth_account(
    provider, state_store, user_adapter, oauth_adapter
):
    _, state1 = await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )
    user1, _, _ = await complete_oauth_flow(
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
    user2, is_new, _ = await complete_oauth_flow(
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


async def test_complete_existing_oauth_account_does_not_verify_unverified_email(
    state_store, user_adapter, oauth_adapter
):
    provider = FakeOAuthProvider(
        {
            "id": "provider-uid-1",
            "email": "oauth@example.com",
            "name": "OAuth User",
            "image": None,
            "email_verified": False,
            "is_active": True,
        }
    )
    user = await user_adapter.create_user(email="oauth@example.com")
    await oauth_adapter.create_oauth_account(
        {
            "provider": "fake",
            "provider_account_id": "provider-uid-1",
            "user_id": user["id"],
            "access_token": None,
            "refresh_token": None,
            "expires_at": None,
        }
    )

    _, state = await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )
    user, is_new, email_verified_now = await complete_oauth_flow(
        provider=provider,
        code="auth-code",
        state=state,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
        user_adapter=user_adapter,
        oauth_adapter=oauth_adapter,
    )

    assert is_new is False
    assert email_verified_now is False
    assert user["email_verified"] is False


async def test_complete_links_to_existing_email_user(
    provider, state_store, user_adapter, oauth_adapter
):
    existing = await user_adapter.create_user(
        email="OAuth@Example.COM", hashed_password="hashed"
    )

    _, state = await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )
    user, is_new, email_verified_now = await complete_oauth_flow(
        provider=provider,
        code="auth-code",
        state=state,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
        user_adapter=user_adapter,
        oauth_adapter=oauth_adapter,
    )

    assert is_new is False
    assert email_verified_now is True
    assert user["id"] == existing["id"]
    assert user["email"] == "oauth@example.com"
    assert user["email_verified"] is True

    accounts = await oauth_adapter.get_user_oauth_accounts(user["id"])
    assert len(accounts) == 1


async def test_complete_rejects_create_collision_for_another_user(
    provider, state_store, user_adapter
):
    class CollidingOAuthAdapter(MemoryOAuthAccountAdapter):
        async def create_oauth_account(self, account):
            return {**account, "user_id": "other-user-id"}

    _, state = await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )

    with pytest.raises(ProviderError, match="already linked"):
        await complete_oauth_flow(
            provider=provider,
            code="auth-code",
            state=state,
            redirect_uri="http://localhost/callback",
            state_store=state_store,
            user_adapter=user_adapter,
            oauth_adapter=CollidingOAuthAdapter(),
        )


async def test_complete_denied_existing_email_user_has_no_link_or_verification(
    provider, state_store, user_adapter, oauth_adapter
):
    existing = await user_adapter.create_user(
        email="oauth@example.com", hashed_password="hashed", email_verified=False
    )

    _, state = await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )

    async def deny(user, provider_id):
        return False

    with pytest.raises(ProviderError, match="Sign-in not allowed"):
        await complete_oauth_flow(
            provider=provider,
            code="auth-code",
            state=state,
            redirect_uri="http://localhost/callback",
            state_store=state_store,
            user_adapter=user_adapter,
            oauth_adapter=oauth_adapter,
            allow_signin=deny,
        )

    user = await user_adapter.get_user_by_id(existing["id"])
    assert user is not None
    assert user["email_verified"] is False
    assert await oauth_adapter.get_user_oauth_accounts(existing["id"]) == []


async def test_complete_rejects_unverified_email_link_to_existing_user(
    state_store, user_adapter, oauth_adapter
):
    provider = FakeOAuthProvider(
        {
            "id": "provider-uid-1",
            "email": "oauth@example.com",
            "name": "OAuth User",
            "image": None,
            "email_verified": False,
            "is_active": True,
        }
    )
    existing = await user_adapter.create_user(
        email="oauth@example.com", hashed_password="hashed", email_verified=True
    )

    _, state = await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )

    with pytest.raises(ProviderError, match="email is not verified"):
        await complete_oauth_flow(
            provider=provider,
            code="auth-code",
            state=state,
            redirect_uri="http://localhost/callback",
            state_store=state_store,
            user_adapter=user_adapter,
            oauth_adapter=oauth_adapter,
        )

    accounts = await oauth_adapter.get_user_oauth_accounts(existing["id"])
    assert accounts == []


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


async def test_complete_new_user_does_not_store_provider_tokens_by_default(
    provider, state_store, user_adapter, oauth_adapter
):
    _, state = await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )

    user, _, _ = await complete_oauth_flow(
        provider=provider,
        code="auth-code",
        state=state,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
        user_adapter=user_adapter,
        oauth_adapter=oauth_adapter,
    )

    accounts = await oauth_adapter.get_user_oauth_accounts(user["id"])
    assert len(accounts) == 1
    assert accounts[0]["access_token"] is None
    assert accounts[0]["refresh_token"] is None


async def test_complete_new_user_stores_provider_tokens_when_enabled(
    provider, state_store, user_adapter, oauth_adapter
):
    _, state = await initiate_oauth_flow(
        provider=provider,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
    )

    user, _, _ = await complete_oauth_flow(
        provider=provider,
        code="auth-code",
        state=state,
        redirect_uri="http://localhost/callback",
        state_store=state_store,
        user_adapter=user_adapter,
        oauth_adapter=oauth_adapter,
        store_provider_tokens=True,
    )

    accounts = await oauth_adapter.get_user_oauth_accounts(user["id"])
    assert len(accounts) == 1
    assert accounts[0]["access_token"] == "fake-access-token"
    assert accounts[0]["refresh_token"] == "fake-refresh"


async def test_link_oauth_account_does_not_store_provider_tokens_by_default(
    provider, state_store, user_adapter, oauth_adapter
):
    user = await user_adapter.create_user(email="linker@example.com")
    await state_store.write(
        "oauth_state:link-state",
        {
            "code_verifier": "verifier",
            "provider": "fake",
            "flow": "link",
            "user_id": user["id"],
            "redirect_uri": "http://localhost/callback",
        },
        ttl=600,
    )

    _, linked_user = await link_oauth_account(
        provider=provider,
        code="auth-code",
        state="link-state",
        redirect_uri="http://localhost/callback",
        state_store=state_store,
        user_adapter=user_adapter,
        oauth_adapter=oauth_adapter,
    )

    accounts = await oauth_adapter.get_user_oauth_accounts(linked_user["id"])
    assert len(accounts) == 1
    assert accounts[0]["access_token"] is None
    assert accounts[0]["refresh_token"] is None


async def test_complete_oauth_state_provider_mismatch(
    state_store, user_adapter, oauth_adapter
):
    provider_b = FakeOAuthProvider()

    await state_store.write(
        "oauth_state:s1",
        {
            "code_verifier": "v",
            "provider": "provider_a",
            "redirect_uri": "http://localhost/callback",
        },
        ttl=600,
    )

    with pytest.raises(ProviderError, match="provider mismatch"):
        await complete_oauth_flow(
            provider=provider_b,
            code="code",
            state="s1",
            redirect_uri="http://localhost/callback",
            state_store=state_store,
            user_adapter=user_adapter,
            oauth_adapter=oauth_adapter,
        )


async def test_complete_oauth_state_missing_redirect_uri(
    state_store, user_adapter, oauth_adapter
):
    provider = FakeOAuthProvider()

    await state_store.write(
        "oauth_state:s1",
        {"code_verifier": "v", "provider": "fake"},
        ttl=600,
    )

    with pytest.raises(ProviderError, match="missing redirect_uri"):
        await complete_oauth_flow(
            provider=provider,
            code="code",
            state="s1",
            redirect_uri="http://localhost/callback",
            state_store=state_store,
            user_adapter=user_adapter,
            oauth_adapter=oauth_adapter,
        )


async def test_link_oauth_state_provider_mismatch(
    state_store, user_adapter, oauth_adapter
):
    user = await user_adapter.create_user(email="link-mismatch@example.com")
    provider_b = FakeOAuthProvider()

    await state_store.write(
        "oauth_state:link-state",
        {
            "code_verifier": "v",
            "provider": "provider_a",
            "flow": "link",
            "user_id": user["id"],
            "redirect_uri": "http://localhost/callback",
        },
        ttl=600,
    )

    with pytest.raises(ProviderError, match="provider mismatch"):
        await link_oauth_account(
            provider=provider_b,
            code="code",
            state="link-state",
            redirect_uri="http://localhost/callback",
            state_store=state_store,
            user_adapter=user_adapter,
            oauth_adapter=oauth_adapter,
        )


async def test_complete_oauth_uses_redirect_uri_from_state(
    state_store, user_adapter, oauth_adapter
):
    """The callback must pass the originally stored redirect_uri to
    provider.exchange_code, even if the caller passed a different one."""

    class CapturingProvider(FakeOAuthProvider):
        def __init__(self) -> None:
            super().__init__()
            self.last_exchange_redirect_uri: str | None = None

        async def exchange_code(self, code: str, redirect_uri: str, **kwargs):
            self.last_exchange_redirect_uri = redirect_uri
            return await super().exchange_code(code, redirect_uri, **kwargs)

    provider = CapturingProvider()

    await state_store.write(
        "oauth_state:s1",
        {
            "code_verifier": "v",
            "provider": "fake",
            "redirect_uri": "https://app.example.com/auth/callback",
        },
        ttl=600,
    )

    # Caller passes a *different* redirect_uri — the stored one must win.
    await complete_oauth_flow(
        provider=provider,
        code="code",
        state="s1",
        redirect_uri="https://attacker.example.com/callback",
        state_store=state_store,
        user_adapter=user_adapter,
        oauth_adapter=oauth_adapter,
    )

    assert (
        provider.last_exchange_redirect_uri == "https://app.example.com/auth/callback"
    )


async def test_link_oauth_uses_redirect_uri_from_state(
    state_store, user_adapter, oauth_adapter
):
    """Same redirect_uri-from-state guarantee for the link flow."""

    class CapturingProvider(FakeOAuthProvider):
        def __init__(self) -> None:
            super().__init__()
            self.last_exchange_redirect_uri: str | None = None

        async def exchange_code(self, code: str, redirect_uri: str, **kwargs):
            self.last_exchange_redirect_uri = redirect_uri
            return await super().exchange_code(code, redirect_uri, **kwargs)

    provider = CapturingProvider()
    user = await user_adapter.create_user(email="link-redir@example.com")

    await state_store.write(
        "oauth_state:link-state",
        {
            "code_verifier": "v",
            "provider": "fake",
            "flow": "link",
            "user_id": user["id"],
            "redirect_uri": "https://app.example.com/auth/link/callback",
        },
        ttl=600,
    )

    await link_oauth_account(
        provider=provider,
        code="code",
        state="link-state",
        redirect_uri="https://attacker.example.com/callback",
        state_store=state_store,
        user_adapter=user_adapter,
        oauth_adapter=oauth_adapter,
    )

    assert (
        provider.last_exchange_redirect_uri
        == "https://app.example.com/auth/link/callback"
    )
