"""
Email verification core logic.

Provides business logic for email verification token generation and confirmation.
Used to verify user email addresses during registration.
"""

from fastauth.adapters.base.email_verification import EmailVerificationAdapter
from fastauth.adapters.base.users import UserAdapter
from fastauth.security.tokens import (
    generate_secure_token,
    hash_token,
    utc_from_now,
    validate_token_expiration,
)
from fastauth.settings import settings


class EmailVerificationError(Exception):
    """Raised when email verification fails."""


def request_email_verification(
    *,
    users: UserAdapter,
    verifications: EmailVerificationAdapter,
    email: str,
    expires_in_minutes: int | None = None,
) -> str | None:
    user = users.get_by_email(email)
    if not user or user.is_verified:
        return None

    if expires_in_minutes is None:
        expires_in_minutes = settings.email_verification_token_expiry_minutes

    raw_token = generate_secure_token(48)
    token_hash = hash_token(raw_token)

    expires_at = utc_from_now(minutes=expires_in_minutes)

    verifications.create(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    return raw_token


def confirm_email_verification(
    *,
    users: UserAdapter,
    verifications: EmailVerificationAdapter,
    token: str,
) -> None:
    token_hash = hash_token(token)

    record = verifications.get_valid(token_hash=token_hash)
    if not record:
        raise EmailVerificationError("Invalid or expired verification token")

    try:
        validate_token_expiration(record.expires_at, "Expired verification token")
    except ValueError as e:
        raise EmailVerificationError(str(e))

    users.mark_verified(record.user_id)
    verifications.mark_used(token_hash=token_hash)
