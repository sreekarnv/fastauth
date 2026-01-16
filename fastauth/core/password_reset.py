"""
Password reset core logic.

Provides business logic for password reset token generation and confirmation.
Used when users forget their password and need to reset it.
"""

from fastauth.adapters.base.password_reset import PasswordResetAdapter
from fastauth.adapters.base.users import UserAdapter
from fastauth.core.hashing import hash_password
from fastauth.security.tokens import (
    generate_secure_token,
    hash_token,
    utc_from_now,
    validate_token_expiration,
)
from fastauth.settings import settings


class PasswordResetError(Exception):
    """Raised when password reset fails."""


def request_password_reset(
    *,
    users: UserAdapter,
    resets: PasswordResetAdapter,
    email: str,
    expires_in_minutes: int | None = None,
) -> str | None:
    user = users.get_by_email(email)
    if not user:
        return None

    if expires_in_minutes is None:
        expires_in_minutes = settings.password_reset_token_expiry_minutes

    raw_token = generate_secure_token(48)
    token_hash = hash_token(raw_token)

    expires_at = utc_from_now(minutes=expires_in_minutes)

    resets.create(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    return raw_token


def confirm_password_reset(
    *,
    users: UserAdapter,
    resets: PasswordResetAdapter,
    token: str,
    new_password: str,
) -> None:
    token_hash = hash_token(token)

    record = resets.get_valid(token_hash=token_hash)
    if not record:
        raise PasswordResetError("Invalid or expired reset token")

    try:
        validate_token_expiration(record.expires_at, "Expired reset token")
    except ValueError as e:
        raise PasswordResetError(str(e))

    hashed = hash_password(new_password)

    users.set_password(
        user_id=record.user_id,
        hashed_password=hashed,
    )

    resets.mark_used(token_hash=token_hash)
