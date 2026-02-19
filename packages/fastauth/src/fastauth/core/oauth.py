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


async def complete_oauth_flow(
    provider: OAuthProvider,
    code: str,
    state: str,
    redirect_uri: str,
    state_store: SessionBackend,
    user_adapter: UserAdapter,
    oauth_adapter: OAuthAccountAdapter,
) -> tuple[UserData, bool]:
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
        return user, False

    user = await user_adapter.get_user_by_email(provider_user["email"])
    is_new = False

    if not user:
        user = await user_adapter.create_user(
            email=provider_user["email"],
            name=provider_user.get("name"),
            image=provider_user.get("image"),
        )
        is_new = True

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

    return user, is_new
