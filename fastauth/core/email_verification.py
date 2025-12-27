from datetime import UTC, datetime, timedelta

from fastauth.adapters.base.email_verification import EmailVerificationAdapter
from fastauth.adapters.base.users import UserAdapter
from fastauth.security.email_verification import (
    generate_email_verification_token,
    hash_email_verification_token,
)


class EmailVerificationError(Exception):
    pass


def request_email_verification(
    *,
    users: UserAdapter,
    verifications: EmailVerificationAdapter,
    email: str,
    expires_in_minutes: int = 60,
) -> str | None:
    user = users.get_by_email(email)
    if not user or user.is_verified:
        return None

    raw_token = generate_email_verification_token()
    token_hash = hash_email_verification_token(raw_token)

    expires_at = datetime.now(UTC) + timedelta(minutes=expires_in_minutes)

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
    token_hash = hash_email_verification_token(token)

    record = verifications.get_valid(token_hash=token_hash)
    if not record:
        raise EmailVerificationError("Invalid or expired verification token")

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at < datetime.now(UTC):
        raise EmailVerificationError("Expired verification token")

    users.mark_verified(record.user_id)
    verifications.mark_used(token_hash=token_hash)
