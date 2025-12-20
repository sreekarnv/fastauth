from datetime import datetime, timedelta, UTC, timezone
from sqlmodel import Session, select

from fastauth.db.models import User, PasswordResetToken
from fastauth.security.password_reset import (
    generate_reset_token,
    hash_reset_token,
)
from fastauth.core.hashing import hash_password


class PasswordResetError(Exception):
    pass


def request_password_reset(
    *,
    session: Session,
    email: str,
    expires_in_minutes: int = 15,
) -> str | None:
    """
    Returns raw reset token if user exists.
    Returns None otherwise (do not leak info).
    """
    user = session.exec(
        select(User).where(User.email == email)
    ).first()

    if not user:
        return None

    raw_token = generate_reset_token()
    token_hash = hash_reset_token(raw_token)

    reset = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC)
        + timedelta(minutes=expires_in_minutes),
    )

    session.add(reset)
    session.commit()

    return raw_token


def confirm_password_reset(
    *,
    session: Session,
    token: str,
    new_password: str,
) -> None:
    token_hash = hash_reset_token(token)

    reset = session.exec(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used == False,
        )
    ).first()

    now = datetime.utcnow()
    if not reset or reset.expires_at < now:
        raise PasswordResetError("Invalid or expired reset token")

    user = session.get(User, reset.user_id)
    if not user:
        raise PasswordResetError("User not found")

    user.hashed_password = hash_password(new_password)
    reset.used = True

    session.add(user)
    session.add(reset)
    session.commit()
