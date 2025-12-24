from datetime import datetime, timedelta, UTC

from fastauth.adapters.base.users import UserAdapter
from fastauth.adapters.base.password_reset import PasswordResetAdapter
from fastauth.core.hashing import hash_password
from fastauth.security.refresh import generate_refresh_token, hash_refresh_token


class PasswordResetError(Exception):
    pass


def request_password_reset(
    *,
    users: UserAdapter,
    resets: PasswordResetAdapter,
    email: str,
    expires_in_minutes: int = 30,
) -> str | None:
    user = users.get_by_email(email)
    if not user:
        return None

    raw_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_token)

    expires_at = datetime.now(UTC) + timedelta(minutes=expires_in_minutes)

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
    token_hash = hash_refresh_token(token)

    record = resets.get_valid(token_hash=token_hash)
    if not record:
        raise PasswordResetError("Invalid or expired reset token")

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at < datetime.now(UTC):
        raise PasswordResetError("Expired reset token")

    hashed = hash_password(new_password)

    users.set_password(
        user_id=record.user_id,
        hashed_password=hashed,
    )

    resets.mark_used(token_hash=token_hash)
