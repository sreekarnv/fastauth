import uuid

from fastauth.adapters.base.refresh_tokens import RefreshTokenAdapter
from fastauth.security.refresh import (
    generate_refresh_token,
    hash_refresh_token,
)
from fastauth.security.tokens import utc_from_now, validate_token_expiration


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
    expires_in_days: int = 30,
):
    token_hash = hash_refresh_token(token)

    refresh = refresh_tokens.get_active(token_hash=token_hash)
    if not refresh:
        raise RefreshTokenError("Invalid refresh token")

    try:
        validate_token_expiration(refresh.expires_at, "Refresh token expired")
    except ValueError as e:
        raise RefreshTokenError(str(e))

    refresh_tokens.revoke(token_hash=token_hash)

    new_token = generate_refresh_token()
    new_hash = hash_refresh_token(new_token)

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
    token_hash = hash_refresh_token(token)
    refresh_tokens.revoke(token_hash=token_hash)
