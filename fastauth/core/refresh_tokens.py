import uuid
from datetime import UTC, datetime, timedelta

from fastauth.adapters.base.refresh_tokens import RefreshTokenAdapter
from fastauth.security.refresh import (
    generate_refresh_token,
    hash_refresh_token,
)


class RefreshTokenError(Exception):
    pass


def create_refresh_token(
    *,
    refresh_tokens: RefreshTokenAdapter,
    user_id: uuid.UUID,
    expires_in_days: int = 30,
) -> str:
    raw_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_token)

    expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

    refresh_tokens.create(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    return raw_token


def rotate_refresh_token(
    *,
    refresh_tokens: RefreshTokenAdapter,
    token: str,
    expires_in_days: int = 30,
):
    token_hash = hash_refresh_token(token)

    refresh = refresh_tokens.get_active(token_hash=token_hash)
    if not refresh:
        raise RefreshTokenError("Invalid refresh token")

    expires_at = refresh.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at < datetime.now(UTC):
        raise RefreshTokenError("Refresh token expired")

    refresh_tokens.revoke(token_hash=token_hash)

    new_token = generate_refresh_token()
    new_hash = hash_refresh_token(new_token)

    refresh_tokens.create(
        user_id=refresh.user_id,
        token_hash=new_hash,
        expires_at=datetime.now(UTC) + timedelta(days=expires_in_days),
    )

    return new_token, refresh.user_id


def revoke_refresh_token(
    *,
    refresh_tokens: RefreshTokenAdapter,
    token: str,
) -> None:
    token_hash = hash_refresh_token(token)
    refresh_tokens.revoke(token_hash=token_hash)
