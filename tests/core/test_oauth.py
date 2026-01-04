import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from fastauth.core.oauth import (
    OAuthError,
    OAuthStateError,
    complete_oauth_flow,
    get_linked_accounts,
    initiate_oauth_flow,
    unlink_oauth_account,
)
from fastauth.providers.base import OAuthTokens, OAuthUserInfo
from fastauth.security.oauth import hash_oauth_token, hash_state_token
from tests.fakes.oauth_accounts import FakeOAuthAccountAdapter
from tests.fakes.oauth_states import FakeOAuthStateAdapter
from tests.fakes.users import FakeUserAdapter


def test_initiate_oauth_flow_basic():
    """Test initiating OAuth flow without PKCE."""
    states = FakeOAuthStateAdapter()

    provider = Mock()
    provider.name = "google"
    provider.authorization_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    provider.default_scopes = "openid email profile"
    provider.client_id = "test_client_id"

    auth_url, state_token, code_verifier = initiate_oauth_flow(
        states=states,
        provider=provider,
        redirect_uri="https://example.com/callback",
        use_pkce=False,
    )

    assert auth_url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert isinstance(state_token, str)
    assert code_verifier is None

    state_hash = hash_state_token(state_token)
    stored_state = states.get_valid(state_hash=state_hash)
    assert stored_state is not None
    assert stored_state.provider == "google"
    assert stored_state.redirect_uri == "https://example.com/callback"


def test_initiate_oauth_flow_with_pkce():
    """Test initiating OAuth flow with PKCE."""
    states = FakeOAuthStateAdapter()

    provider = Mock()
    provider.name = "google"
    provider.authorization_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    provider.default_scopes = "openid email profile"
    provider.client_id = "test_client_id"

    auth_url, state_token, code_verifier = initiate_oauth_flow(
        states=states,
        provider=provider,
        redirect_uri="https://example.com/callback",
        use_pkce=True,
    )

    assert auth_url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert isinstance(state_token, str)
    assert isinstance(code_verifier, str)
    assert len(code_verifier) > 43

    assert "code_challenge=" in auth_url
    assert "code_challenge_method=S256" in auth_url


def test_initiate_oauth_flow_with_user_linking():
    """Test initiating OAuth flow for linking to existing user."""
    states = FakeOAuthStateAdapter()

    provider = Mock()
    provider.name = "google"
    provider.authorization_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    provider.default_scopes = "openid email profile"
    provider.client_id = "test_client_id"

    user_id = uuid.uuid4()

    _, state_token, __ = initiate_oauth_flow(
        states=states,
        provider=provider,
        redirect_uri="https://example.com/callback",
        user_id=user_id,
    )

    state_hash = hash_state_token(state_token)
    stored_state = states.get_valid(state_hash=state_hash)
    assert stored_state.user_id == user_id


@pytest.mark.anyio
async def test_complete_oauth_flow_new_user():
    """Test completing OAuth flow creates new user."""
    states = FakeOAuthStateAdapter()
    oauth_accounts = FakeOAuthAccountAdapter()
    users = FakeUserAdapter()

    provider = Mock()
    provider.name = "google"
    provider.client_id = "test_client_id"

    _, state_token, _ = initiate_oauth_flow(
        states=states,
        provider=provider,
        redirect_uri="https://example.com/callback",
    )

    provider.exchange_code_for_tokens = AsyncMock(
        return_value=OAuthTokens(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            expires_in=3600,
        )
    )

    provider.get_user_info = AsyncMock(
        return_value=OAuthUserInfo(
            provider_user_id="google_123",
            email="newuser@example.com",
            email_verified=True,
            name="New User",
        )
    )

    user, is_new_user = await complete_oauth_flow(
        states=states,
        oauth_accounts=oauth_accounts,
        users=users,
        provider=provider,
        code="test_code",
        state=state_token,
    )

    assert is_new_user is True
    assert user.email == "newuser@example.com"
    assert user.is_verified is True

    accounts = oauth_accounts.get_by_user_id(user_id=user.id)
    assert len(accounts) == 1
    assert accounts[0].provider == "google"
    assert accounts[0].provider_user_id == "google_123"


@pytest.mark.anyio
async def test_complete_oauth_flow_existing_oauth_account():
    """Test completing OAuth flow with existing OAuth account updates tokens."""
    states = FakeOAuthStateAdapter()
    oauth_accounts = FakeOAuthAccountAdapter()
    users = FakeUserAdapter()

    existing_user = users.create_user(
        email="existing@example.com", hashed_password="dummy"
    )
    users.mark_verified(existing_user.id)

    old_token_hash = hash_oauth_token("old_access_token")
    oauth_accounts.create(
        user_id=existing_user.id,
        provider="google",
        provider_user_id="google_123",
        access_token_hash=old_token_hash,
    )

    provider = Mock()
    provider.name = "google"
    provider.client_id = "test_client_id"

    _, state_token, _ = initiate_oauth_flow(
        states=states,
        provider=provider,
        redirect_uri="https://example.com/callback",
    )

    provider.exchange_code_for_tokens = AsyncMock(
        return_value=OAuthTokens(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            expires_in=3600,
        )
    )

    provider.get_user_info = AsyncMock(
        return_value=OAuthUserInfo(
            provider_user_id="google_123",
            email="existing@example.com",
            email_verified=True,
        )
    )

    user, is_new_user = await complete_oauth_flow(
        states=states,
        oauth_accounts=oauth_accounts,
        users=users,
        provider=provider,
        code="test_code",
        state=state_token,
    )

    assert is_new_user is False
    assert user.id == existing_user.id

    accounts = oauth_accounts.get_by_user_id(user_id=user.id, provider="google")
    assert len(accounts) == 1
    new_token_hash = hash_oauth_token("new_access_token")
    assert accounts[0].access_token_hash == new_token_hash


@pytest.mark.anyio
async def test_complete_oauth_flow_invalid_state():
    """Test completing OAuth flow with invalid state raises error."""
    states = FakeOAuthStateAdapter()
    oauth_accounts = FakeOAuthAccountAdapter()
    users = FakeUserAdapter()

    provider = Mock()
    provider.name = "google"

    with pytest.raises(OAuthStateError, match="Invalid or expired state token"):
        await complete_oauth_flow(
            states=states,
            oauth_accounts=oauth_accounts,
            users=users,
            provider=provider,
            code="test_code",
            state="invalid_state_token",
        )


@pytest.mark.anyio
async def test_complete_oauth_flow_expired_state():
    """Test completing OAuth flow with expired state raises error."""
    states = FakeOAuthStateAdapter()
    oauth_accounts = FakeOAuthAccountAdapter()
    users = FakeUserAdapter()

    provider = Mock()
    provider.name = "google"

    state_hash = hash_state_token("test_state")
    states.create(
        state_hash=state_hash,
        provider="google",
        redirect_uri="https://example.com/callback",
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )

    with pytest.raises(OAuthStateError, match="State token has expired"):
        await complete_oauth_flow(
            states=states,
            oauth_accounts=oauth_accounts,
            users=users,
            provider=provider,
            code="test_code",
            state="test_state",
        )


def test_get_linked_accounts():
    """Test getting all OAuth accounts for a user."""
    oauth_accounts = FakeOAuthAccountAdapter()

    user_id = uuid.uuid4()

    oauth_accounts.create(
        user_id=user_id,
        provider="google",
        provider_user_id="google_123",
        access_token_hash="hash1",
    )
    oauth_accounts.create(
        user_id=user_id,
        provider="github",
        provider_user_id="github_456",
        access_token_hash="hash2",
    )

    accounts = get_linked_accounts(oauth_accounts=oauth_accounts, user_id=user_id)

    assert len(accounts) == 2
    providers = {acc.provider for acc in accounts}
    assert providers == {"google", "github"}


def test_unlink_oauth_account():
    """Test unlinking OAuth account from user."""
    oauth_accounts = FakeOAuthAccountAdapter()

    user_id = uuid.uuid4()

    oauth_accounts.create(
        user_id=user_id,
        provider="google",
        provider_user_id="google_123",
        access_token_hash="hash1",
    )

    accounts_before = get_linked_accounts(
        oauth_accounts=oauth_accounts, user_id=user_id
    )
    assert len(accounts_before) == 1

    unlink_oauth_account(
        oauth_accounts=oauth_accounts, user_id=user_id, provider="google"
    )

    accounts_after = get_linked_accounts(oauth_accounts=oauth_accounts, user_id=user_id)
    assert len(accounts_after) == 0


def test_unlink_oauth_account_not_found():
    """Test unlinking non-existent OAuth account raises error."""
    oauth_accounts = FakeOAuthAccountAdapter()

    user_id = uuid.uuid4()

    with pytest.raises(OAuthError, match="No google account linked"):
        unlink_oauth_account(
            oauth_accounts=oauth_accounts, user_id=user_id, provider="google"
        )


@pytest.mark.anyio
async def test_complete_oauth_flow_timezone_naive_expires_at():
    """Test handling timezone-naive expires_at in state record."""
    states = FakeOAuthStateAdapter()
    oauth_accounts = FakeOAuthAccountAdapter()
    users = FakeUserAdapter()

    provider = Mock()
    provider.name = "google"
    provider.client_id = "test_client_id"

    state_hash = hash_state_token("test_state")
    naive_expires_at = datetime.now() + timedelta(minutes=10)
    states.create(
        state_hash=state_hash,
        provider="google",
        redirect_uri="https://example.com/callback",
        expires_at=naive_expires_at,
    )

    provider.exchange_code_for_tokens = AsyncMock(
        return_value=OAuthTokens(
            access_token="access_token_123",
            refresh_token="refresh_token_123",
            expires_in=3600,
        )
    )

    provider.get_user_info = AsyncMock(
        return_value=OAuthUserInfo(
            provider_user_id="google_123",
            email="newuser@example.com",
            email_verified=True,
        )
    )

    user, is_new_user = await complete_oauth_flow(
        states=states,
        oauth_accounts=oauth_accounts,
        users=users,
        provider=provider,
        code="test_code",
        state="test_state",
    )

    assert user is not None
    assert is_new_user is True


@pytest.mark.anyio
async def test_complete_oauth_flow_provider_exception():
    """Test that provider exceptions are wrapped in OAuthError."""
    states = FakeOAuthStateAdapter()
    oauth_accounts = FakeOAuthAccountAdapter()
    users = FakeUserAdapter()

    provider = Mock()
    provider.name = "google"
    provider.client_id = "test_client_id"

    _, state_token, _ = initiate_oauth_flow(
        states=states,
        provider=provider,
        redirect_uri="https://example.com/callback",
    )

    provider.exchange_code_for_tokens = AsyncMock(
        side_effect=Exception("Token exchange failed")
    )

    with pytest.raises(OAuthError, match="Failed to complete OAuth flow"):
        await complete_oauth_flow(
            states=states,
            oauth_accounts=oauth_accounts,
            users=users,
            provider=provider,
            code="test_code",
            state=state_token,
        )


@pytest.mark.anyio
async def test_complete_oauth_flow_user_not_found_for_oauth_account():
    """Test error when OAuth account exists but user doesn't."""
    states = FakeOAuthStateAdapter()
    oauth_accounts = FakeOAuthAccountAdapter()
    users = FakeUserAdapter()

    deleted_user_id = uuid.uuid4()

    oauth_accounts.create(
        user_id=deleted_user_id,
        provider="google",
        provider_user_id="google_123",
        access_token_hash="old_hash",
    )

    provider = Mock()
    provider.name = "google"
    provider.client_id = "test_client_id"

    _, state_token, _ = initiate_oauth_flow(
        states=states,
        provider=provider,
        redirect_uri="https://example.com/callback",
    )

    provider.exchange_code_for_tokens = AsyncMock(
        return_value=OAuthTokens(
            access_token="new_token",
            refresh_token="new_refresh",
            expires_in=3600,
        )
    )

    provider.get_user_info = AsyncMock(
        return_value=OAuthUserInfo(
            provider_user_id="google_123",
            email="orphaned@example.com",
            email_verified=True,
        )
    )

    with pytest.raises(OAuthError, match="User not found for existing OAuth account"):
        await complete_oauth_flow(
            states=states,
            oauth_accounts=oauth_accounts,
            users=users,
            provider=provider,
            code="test_code",
            state=state_token,
        )


@pytest.mark.anyio
async def test_complete_oauth_flow_link_to_logged_in_user():
    """Test linking OAuth account to logged-in user."""
    states = FakeOAuthStateAdapter()
    oauth_accounts = FakeOAuthAccountAdapter()
    users = FakeUserAdapter()

    existing_user = users.create_user(
        email="existing@example.com",
        hashed_password="hashed",
    )
    users.mark_verified(existing_user.id)

    provider = Mock()
    provider.name = "google"
    provider.client_id = "test_client_id"

    state_hash = hash_state_token("test_state")
    states.create(
        state_hash=state_hash,
        provider="google",
        redirect_uri="https://example.com/callback",
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        user_id=existing_user.id,
    )

    provider.exchange_code_for_tokens = AsyncMock(
        return_value=OAuthTokens(
            access_token="new_token",
            refresh_token="new_refresh",
            expires_in=3600,
        )
    )

    provider.get_user_info = AsyncMock(
        return_value=OAuthUserInfo(
            provider_user_id="google_456",
            email="oauth@example.com",
            email_verified=True,
        )
    )

    user, is_new_user = await complete_oauth_flow(
        states=states,
        oauth_accounts=oauth_accounts,
        users=users,
        provider=provider,
        code="test_code",
        state="test_state",
    )

    assert user.id == existing_user.id
    assert is_new_user is False

    accounts = oauth_accounts.get_by_user_id(user_id=user.id, provider="google")
    assert len(accounts) == 1
    assert accounts[0].provider_user_id == "google_456"


@pytest.mark.anyio
async def test_complete_oauth_flow_link_user_not_found():
    """Test error when state has user_id but user doesn't exist."""
    states = FakeOAuthStateAdapter()
    oauth_accounts = FakeOAuthAccountAdapter()
    users = FakeUserAdapter()

    deleted_user_id = uuid.uuid4()

    provider = Mock()
    provider.name = "google"
    provider.client_id = "test_client_id"

    state_hash = hash_state_token("test_state")
    states.create(
        state_hash=state_hash,
        provider="google",
        redirect_uri="https://example.com/callback",
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        user_id=deleted_user_id,
    )

    provider.exchange_code_for_tokens = AsyncMock(
        return_value=OAuthTokens(
            access_token="new_token",
            refresh_token="new_refresh",
            expires_in=3600,
        )
    )

    provider.get_user_info = AsyncMock(
        return_value=OAuthUserInfo(
            provider_user_id="google_789",
            email="oauth@example.com",
            email_verified=True,
        )
    )

    with pytest.raises(OAuthError, match="User not found for linking"):
        await complete_oauth_flow(
            states=states,
            oauth_accounts=oauth_accounts,
            users=users,
            provider=provider,
            code="test_code",
            state="test_state",
        )


@pytest.mark.anyio
async def test_complete_oauth_flow_autolink_existing_verified_user():
    """Test auto-linking OAuth to existing user with verified email."""
    states = FakeOAuthStateAdapter()
    oauth_accounts = FakeOAuthAccountAdapter()
    users = FakeUserAdapter()

    existing_user = users.create_user(
        email="verified@example.com",
        hashed_password="hashed",
    )
    users.mark_verified(existing_user.id)

    provider = Mock()
    provider.name = "google"
    provider.client_id = "test_client_id"

    _, state_token, _ = initiate_oauth_flow(
        states=states,
        provider=provider,
        redirect_uri="https://example.com/callback",
    )

    provider.exchange_code_for_tokens = AsyncMock(
        return_value=OAuthTokens(
            access_token="new_token",
            refresh_token="new_refresh",
            expires_in=3600,
        )
    )

    provider.get_user_info = AsyncMock(
        return_value=OAuthUserInfo(
            provider_user_id="google_999",
            email="verified@example.com",
            email_verified=True,
        )
    )

    user, is_new_user = await complete_oauth_flow(
        states=states,
        oauth_accounts=oauth_accounts,
        users=users,
        provider=provider,
        code="test_code",
        state=state_token,
    )

    assert user.id == existing_user.id
    assert is_new_user is False

    accounts = oauth_accounts.get_by_user_id(user_id=user.id, provider="google")
    assert len(accounts) == 1
    assert accounts[0].provider_user_id == "google_999"


@pytest.mark.anyio
async def test_complete_oauth_flow_no_autolink_unverified_user():
    """Test that auto-link fails when existing user email is not verified."""
    states = FakeOAuthStateAdapter()
    oauth_accounts = FakeOAuthAccountAdapter()
    users = FakeUserAdapter()

    users.create_user(
        email="unverified@example.com",
        hashed_password="hashed",
    )

    provider = Mock()
    provider.name = "google"
    provider.client_id = "test_client_id"

    _, state_token, _ = initiate_oauth_flow(
        states=states,
        provider=provider,
        redirect_uri="https://example.com/callback",
    )

    provider.exchange_code_for_tokens = AsyncMock(
        return_value=OAuthTokens(
            access_token="new_token",
            refresh_token="new_refresh",
            expires_in=3600,
        )
    )

    provider.get_user_info = AsyncMock(
        return_value=OAuthUserInfo(
            provider_user_id="google_111",
            email="unverified@example.com",
            email_verified=True,
        )
    )

    with pytest.raises(
        OAuthError, match="Cannot auto-link OAuth account.*email is not verified"
    ):
        await complete_oauth_flow(
            states=states,
            oauth_accounts=oauth_accounts,
            users=users,
            provider=provider,
            code="test_code",
            state=state_token,
        )


@pytest.mark.anyio
async def test_complete_oauth_flow_no_autolink_unverified_oauth_email():
    """Test that auto-link fails when OAuth email is not verified."""
    states = FakeOAuthStateAdapter()
    oauth_accounts = FakeOAuthAccountAdapter()
    users = FakeUserAdapter()

    existing_user = users.create_user(
        email="verified@example.com",
        hashed_password="hashed",
    )
    users.mark_verified(existing_user.id)

    provider = Mock()
    provider.name = "google"
    provider.client_id = "test_client_id"

    _, state_token, _ = initiate_oauth_flow(
        states=states,
        provider=provider,
        redirect_uri="https://example.com/callback",
    )

    provider.exchange_code_for_tokens = AsyncMock(
        return_value=OAuthTokens(
            access_token="new_token",
            refresh_token="new_refresh",
            expires_in=3600,
        )
    )

    provider.get_user_info = AsyncMock(
        return_value=OAuthUserInfo(
            provider_user_id="google_222",
            email="verified@example.com",
            email_verified=False,
        )
    )

    with pytest.raises(
        OAuthError,
        match="Cannot auto-link OAuth account.*not verified by the OAuth provider",
    ):
        await complete_oauth_flow(
            states=states,
            oauth_accounts=oauth_accounts,
            users=users,
            provider=provider,
            code="test_code",
            state=state_token,
        )
