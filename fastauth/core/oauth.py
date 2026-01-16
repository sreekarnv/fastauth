"""
OAuth authentication core logic.

Provides business logic for OAuth flows including authorization URL generation,
callback handling, and account linking.
"""

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastauth.adapters.base.oauth_accounts import OAuthAccountAdapter
from fastauth.adapters.base.oauth_states import OAuthStateAdapter
from fastauth.adapters.base.users import UserAdapter
from fastauth.core.hashing import hash_password
from fastauth.providers.base import OAuthProvider
from fastauth.security.oauth import (
    build_authorization_url,
    generate_code_challenge,
    generate_code_verifier,
    generate_state_token,
    hash_oauth_token,
    hash_state_token,
)


class OAuthError(Exception):
    """Base exception for OAuth errors."""


class OAuthStateError(Exception):
    """Raised when OAuth state token is invalid or expired."""


class OAuthAccountAlreadyLinkedError(Exception):
    """Raised when OAuth account is already linked to a different user."""


class OAuthProviderNotFoundError(Exception):
    """Raised when OAuth provider is not found."""


def initiate_oauth_flow(
    *,
    states: OAuthStateAdapter,
    provider: OAuthProvider,
    redirect_uri: str,
    user_id: uuid.UUID | None = None,
    use_pkce: bool = True,
    state_ttl_minutes: int = 10,
) -> tuple[str, str, str | None]:
    """
    Initiate OAuth authorization flow.

    Generates state token for CSRF protection and optional PKCE challenge.
    Stores state in database and builds authorization URL.

    Args:
        states: OAuth state adapter for database operations
        provider: OAuth provider instance
        redirect_uri: Callback URL after authorization
        user_id: Optional user ID for linking mode (logged-in user)
        use_pkce: Whether to use PKCE for enhanced security (default: True)
        state_ttl_minutes: State token time-to-live in minutes (default: 10)

    Returns:
        Tuple of (authorization_url, state_token, code_verifier)
        code_verifier is None if PKCE is disabled

    Example:
        >>> auth_url, state, verifier = initiate_oauth_flow(
        ...     states=state_adapter,
        ...     provider=google_provider,
        ...     redirect_uri="https://example.com/oauth/callback",
        ...     use_pkce=True,
        ... )
    """
    state_token = generate_state_token()
    state_hash = hash_state_token(state_token)

    code_verifier = None
    code_challenge = None
    code_challenge_method = None

    if use_pkce:
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        code_challenge_method = "S256"

    expires_at = datetime.now(UTC) + timedelta(minutes=state_ttl_minutes)

    states.create(
        state_hash=state_hash,
        provider=provider.name,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        user_id=user_id,
        expires_at=expires_at,
    )

    authorization_url = build_authorization_url(
        auth_endpoint=provider.authorization_endpoint,
        client_id=provider.client_id,
        redirect_uri=redirect_uri,
        state=state_token,
        scope=provider.default_scopes,
        code_challenge=code_challenge,
    )

    return authorization_url, state_token, code_verifier


async def complete_oauth_flow(
    *,
    states: OAuthStateAdapter,
    oauth_accounts: OAuthAccountAdapter,
    users: UserAdapter,
    provider: OAuthProvider,
    code: str,
    state: str,
    code_verifier: str | None = None,
) -> tuple[object, bool]:
    """
    Complete OAuth authorization flow.

    Validates state token, exchanges code for tokens, fetches user info,
    and handles account linking logic.

    Account Linking Strategy:
    1. If OAuth account exists → update tokens, return existing user
    2. If user_id in state (linking mode) → link OAuth to that user
    3. If user exists by email (verified) → auto-link OAuth account
    4. If new user → create user with random password, mark verified, link OAuth

    Args:
        states: OAuth state adapter
        oauth_accounts: OAuth account adapter
        users: User adapter
        provider: OAuth provider instance
        code: Authorization code from OAuth callback
        state: State token from OAuth callback
        code_verifier: Optional PKCE code verifier

    Returns:
        Tuple of (user, is_new_user)

    Raises:
        OAuthStateError: If state token is invalid or expired
        OAuthAccountAlreadyLinkedError: If OAuth account is linked to different user
        OAuthError: If OAuth flow fails for any reason
    """
    state_hash = hash_state_token(state)
    state_record = states.get_valid(state_hash=state_hash)

    if not state_record:
        raise OAuthStateError("Invalid or expired state token")

    expires_at = state_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at < datetime.now(UTC):
        raise OAuthStateError("State token has expired")

    states.mark_used(state_hash=state_hash)

    try:
        oauth_tokens = await provider.exchange_code_for_tokens(
            code=code,
            redirect_uri=state_record.redirect_uri,
            code_verifier=code_verifier,
        )

        user_info = await provider.get_user_info(access_token=oauth_tokens.access_token)

    except Exception as e:
        raise OAuthError(f"Failed to complete OAuth flow: {e!s}") from e

    access_token_hash = hash_oauth_token(oauth_tokens.access_token)
    refresh_token_hash = (
        hash_oauth_token(oauth_tokens.refresh_token)
        if oauth_tokens.refresh_token
        else None
    )

    token_expires_at = None
    if oauth_tokens.expires_in:
        token_expires_at = datetime.now(UTC) + timedelta(
            seconds=oauth_tokens.expires_in
        )

    existing_oauth_account = oauth_accounts.get_by_provider_user_id(
        provider=provider.name,
        provider_user_id=user_info.provider_user_id,
    )

    if existing_oauth_account:
        oauth_accounts.update_tokens(
            account_id=existing_oauth_account.id,
            access_token_hash=access_token_hash,
            refresh_token_hash=refresh_token_hash,
            expires_at=token_expires_at,
        )

        user = users.get_by_id(user_id=existing_oauth_account.user_id)
        if not user:
            raise OAuthError("User not found for existing OAuth account")

        return user, False

    if state_record.user_id:
        user = users.get_by_id(user_id=state_record.user_id)
        if not user:
            raise OAuthError("User not found for linking")

        oauth_accounts.create(
            user_id=user.id,
            provider=provider.name,
            provider_user_id=user_info.provider_user_id,
            access_token_hash=access_token_hash,
            refresh_token_hash=refresh_token_hash,
            expires_at=token_expires_at,
            email=user_info.email,
            name=user_info.name,
            avatar_url=user_info.avatar_url,
        )

        return user, False

    existing_user = users.get_by_email(email=user_info.email)

    if existing_user:
        if not existing_user.is_verified:
            raise OAuthError(
                f"Cannot auto-link OAuth account. User with email {user_info.email} "
                "exists but email is not verified. Please verify email first or "
                "login and manually link the OAuth account."
            )

        if not user_info.email_verified:
            raise OAuthError(
                f"Cannot auto-link OAuth account. Email {user_info.email} is not "
                "verified by the OAuth provider."
            )

        oauth_accounts.create(
            user_id=existing_user.id,
            provider=provider.name,
            provider_user_id=user_info.provider_user_id,
            access_token_hash=access_token_hash,
            refresh_token_hash=refresh_token_hash,
            expires_at=token_expires_at,
            email=user_info.email,
            name=user_info.name,
            avatar_url=user_info.avatar_url,
        )

        return existing_user, False

    random_password = secrets.token_urlsafe(32)
    hashed_password = hash_password(random_password)

    user = users.create_user(
        email=user_info.email,
        hashed_password=hashed_password,
    )

    if user_info.email_verified:
        users.mark_verified(user.id)

    oauth_accounts.create(
        user_id=user.id,
        provider=provider.name,
        provider_user_id=user_info.provider_user_id,
        access_token_hash=access_token_hash,
        refresh_token_hash=refresh_token_hash,
        expires_at=token_expires_at,
        email=user_info.email,
        name=user_info.name,
        avatar_url=user_info.avatar_url,
    )

    return user, True


def unlink_oauth_account(
    *,
    oauth_accounts: OAuthAccountAdapter,
    user_id: uuid.UUID,
    provider: str,
) -> None:
    """
    Unlink an OAuth provider from a user's account.

    Args:
        oauth_accounts: OAuth account adapter
        user_id: User ID to unlink from
        provider: Provider name (e.g., 'google', 'github')

    Raises:
        OAuthError: If OAuth account not found
    """
    accounts = oauth_accounts.get_by_user_id(user_id=user_id, provider=provider)

    if not accounts:
        raise OAuthError(f"No {provider} account linked to this user")

    for account in accounts:
        oauth_accounts.delete(account_id=account.id)


def get_linked_accounts(
    *,
    oauth_accounts: OAuthAccountAdapter,
    user_id: uuid.UUID,
) -> list:
    """
    Get all OAuth accounts linked to a user.

    Args:
        oauth_accounts: OAuth account adapter
        user_id: User ID to get linked accounts for

    Returns:
        List of OAuth account records
    """
    return oauth_accounts.get_by_user_id(user_id=user_id)
