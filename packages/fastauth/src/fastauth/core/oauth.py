from __future__ import annotations

import base64
import hashlib
import secrets
from typing import TYPE_CHECKING, Any

from fastauth.exceptions import ProviderError

if TYPE_CHECKING:
    from fastauth.core.protocols import (
        OAuthAccountAdapter,
        OAuthProvider,
        SessionBackend,
        UserAdapter,
    )
    from fastauth.types import UserData


async def initiate_oauth_flow(
    provider: OAuthProvider,
    redirect_uri: str,
    state_store: SessionBackend,
) -> tuple[str, str]:
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)

    challenge_bytes = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode().rstrip("=")

    await state_store.write(
        f"oauth_state:{state}",
        {"code_verifier": code_verifier, "provider": provider.id},
        ttl=600,
    )

    url = await provider.get_authorization_url(
        state=state,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )
    return url, state


async def initiate_link_flow(
    provider: OAuthProvider,
    redirect_uri: str,
    state_store: SessionBackend,
    user_id: str,
) -> tuple[str, str]:
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)

    challenge_bytes = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode().rstrip("=")

    await state_store.write(
        f"oauth_state:{state}",
        {
            "code_verifier": code_verifier,
            "provider": provider.id,
            "flow": "link",
            "user_id": user_id,
        },
        ttl=600,
    )

    url = await provider.get_authorization_url(
        state=state,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )
    return url, state


async def link_oauth_account(
    provider: OAuthProvider,
    code: str,
    state: str,
    redirect_uri: str,
    state_store: SessionBackend,
    user_adapter: UserAdapter,
    oauth_adapter: OAuthAccountAdapter,
) -> tuple[Any, UserData]:
    stored = await state_store.read(f"oauth_state:{state}")
    if not stored or stored.get("flow") != "link":
        raise ProviderError("Invalid or expired link state")
    await state_store.delete(f"oauth_state:{state}")

    user_id: str = stored["user_id"]

    tokens: dict[str, Any] = await provider.exchange_code(
        code=code,
        redirect_uri=redirect_uri,
        code_verifier=stored.get("code_verifier"),
    )
    provider_user = await provider.get_user_info(tokens["access_token"])

    existing = await oauth_adapter.get_oauth_account(provider.id, provider_user["id"])
    if existing:
        raise ProviderError("This provider account is already linked to a user")

    account = await oauth_adapter.create_oauth_account(
        {
            "provider": provider.id,
            "provider_account_id": provider_user["id"],
            "user_id": user_id,
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
            "expires_at": None,
        }
    )

    user = await user_adapter.get_user_by_id(user_id)
    if not user:
        raise ProviderError("Linking user not found")

    return account, user


async def complete_oauth_flow(
    provider: OAuthProvider,
    code: str,
    state: str,
    redirect_uri: str,
    state_store: SessionBackend,
    user_adapter: UserAdapter,
    oauth_adapter: OAuthAccountAdapter,
) -> tuple[UserData, bool, bool]:
    """Complete an OAuth sign-in flow.

    Returns:
        A 3-tuple of ``(user, is_new, email_verified_now)`` where
        *is_new* is ``True`` when the user was just created and
        *email_verified_now* is ``True`` when ``email_verified`` was
        flipped to ``True`` during this call (useful for firing the
        ``on_email_verify`` hook in the caller).
    """
    stored = await state_store.read(f"oauth_state:{state}")
    if not stored:
        raise ProviderError("Invalid or expired OAuth state")
    await state_store.delete(f"oauth_state:{state}")

    tokens: dict[str, Any] = await provider.exchange_code(
        code=code,
        redirect_uri=redirect_uri,
        code_verifier=stored.get("code_verifier"),
    )

    provider_user = await provider.get_user_info(tokens["access_token"])

    existing = await oauth_adapter.get_oauth_account(
        provider=provider.id,
        provider_account_id=provider_user["id"],
    )

    if existing:
        user = await user_adapter.get_user_by_id(existing["user_id"])
        if not user:
            raise ProviderError("Linked user account not found")
        email_verified_now = False
        if not user.get("email_verified"):
            user = await user_adapter.update_user(user["id"], email_verified=True)
            email_verified_now = True
        return user, False, email_verified_now

    user = await user_adapter.get_user_by_email(provider_user["email"])
    is_new = False

    if not user:
        user = await user_adapter.create_user(
            email=provider_user["email"],
            name=provider_user.get("name"),
            image=provider_user.get("image"),
            email_verified=True,
        )
        is_new = True
        email_verified_now = True
    else:
        email_verified_now = False
        if not user.get("email_verified"):
            user = await user_adapter.update_user(user["id"], email_verified=True)
            email_verified_now = True

    _ = await oauth_adapter.create_oauth_account(
        {
            "provider": provider.id,
            "provider_account_id": provider_user["id"],
            "user_id": user["id"],
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
            "expires_at": None,
        }
    )

    return user, is_new, email_verified_now
