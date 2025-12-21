from datetime import datetime, timedelta
from sqlmodel import Session, select

from fastauth.db.models import User, EmailVerificationToken
from fastauth.security.email_verification import (
    generate_email_verification_token,
    hash_email_verification_token,
)


class EmailVerificationError(Exception):
    pass


def request_email_verification(
    *,
    session: Session,
    email: str,
    expires_in_minutes: int = 60,
) -> str | None:
    user = session.exec(
        select(User).where(User.email == email)
    ).first()

    if not user or user.is_verified:
        return None

    raw_token = generate_email_verification_token()
    token_hash = hash_email_verification_token(raw_token)

    record = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow()
        + timedelta(minutes=expires_in_minutes),
    )

    session.add(record)
    session.commit()

    return raw_token


def confirm_email_verification(
    *,
    session: Session,
    token: str,
) -> None:
    token_hash = hash_email_verification_token(token)

    record = session.exec(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.used == False,
        )
    ).first()

    if not record or record.expires_at < datetime.utcnow():
        raise EmailVerificationError("Invalid or expired token")

    user = session.get(User, record.user_id)
    if not user:
        raise EmailVerificationError("User not found")

    user.is_verified = True
    record.used = True

    session.add(user)
    session.add(record)
    session.commit()
