import uuid

from fastauth.adapters.base.refresh_tokens import RefreshTokenAdapter
from fastauth.security.tokens import (
    generate_secure_token,
    hash_token,
    utc_from_now,
    validate_token_expiration,
)
from fastauth.settings import settings


class RefreshTokenError(Exception):
    pass


def create_refresh_token(
    *,
    refresh_tokens: RefreshTokenAdapter,
    user_id: uuid.UUID,
    expires_in_days: int | None = None,
) -> str:
    if expires_in_days is None:
        expires_in_days = settings.refresh_token_expiry_days

    raw_token = generate_secure_token(48)
    token_hash = hash_token(raw_token)

    expires_at = utc_from_now(days=expires_in_days)

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
    expires_in_days: int | None = None,
):
    if expires_in_days is None:
        expires_in_days = settings.refresh_token_expiry_days

    token_hash = hash_token(token)

    refresh = refresh_tokens.get_active(token_hash=token_hash)
    if not refresh:
        raise RefreshTokenError("Invalid refresh token")

    try:
        validate_token_expiration(refresh.expires_at, "Refresh token expired")
    except ValueError as e:
        raise RefreshTokenError(str(e))

    refresh_tokens.revoke(token_hash=token_hash)

    new_token = generate_secure_token(48)
    new_hash = hash_token(new_token)

    refresh_tokens.create(
        user_id=refresh.user_id,
        token_hash=new_hash,
        expires_at=utc_from_now(days=expires_in_days),
    )

    return new_token, refresh.user_id


def revoke_refresh_token(
    *,
    refresh_tokens: RefreshTokenAdapter,
    token: str,
) -> None:
    token_hash = hash_token(token)
    refresh_tokens.revoke(token_hash=token_hash)
