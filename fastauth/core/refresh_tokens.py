import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from sqlmodel import Session, select

from fastauth.db.models import RefreshToken
from fastauth.security.refresh import (
    generate_refresh_token,
    hash_refresh_token,
)


@dataclass(frozen=True)
class RotatedRefreshToken:
    refresh_token: str
    user_id: uuid.UUID


class RefreshTokenError(Exception):
    pass


def create_refresh_token(
    *,
    session: Session,
    user_id,
    expires_in_days: int = 30,
) -> str:
    raw_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_token)

    refresh = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(days=expires_in_days),
    )

    session.add(refresh)
    session.commit()

    return raw_token


def rotate_refresh_token(
    *,
    session: Session,
    token: str,
    expires_in_days: int = 30,
) -> RotatedRefreshToken:
    token_hash = hash_refresh_token(token)

    statement = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
    )
    refresh = session.exec(statement).first()

    if not refresh:
        raise RefreshTokenError("Invalid refresh token")

    expires_at = refresh.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at < datetime.now(UTC):
        raise RefreshTokenError("Refresh token expired")

    refresh.revoked = True
    session.add(refresh)

    new_token = generate_refresh_token()
    new_hash = hash_refresh_token(new_token)

    new_refresh = RefreshToken(
        user_id=refresh.user_id,
        token_hash=new_hash,
        expires_at=datetime.now(UTC) + timedelta(days=expires_in_days)
    )

    session.add(new_refresh)
    session.commit()

    return RotatedRefreshToken(
        refresh_token=new_token,
        user_id=refresh.user_id,
    )


def revoke_refresh_token(
    *,
    session: Session,
    token: str,
) -> None:
    """
    Revoke a refresh token (logout).
    """
    token_hash = hash_refresh_token(token)

    statement = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
    )
    refresh = session.exec(statement).first()

    if not refresh:
        return

    refresh.revoked = True
    session.add(refresh)
    session.commit()
