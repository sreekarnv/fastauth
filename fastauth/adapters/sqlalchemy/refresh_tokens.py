"""
SQLAlchemy refresh token adapter implementation.

Provides database operations for refresh token storage using SQLAlchemy/SQLModel.
"""

import uuid
from datetime import datetime

from sqlmodel import Session, select

from fastauth.adapters.base.refresh_tokens import RefreshTokenAdapter
from fastauth.adapters.sqlalchemy.models import RefreshToken


class SQLAlchemyRefreshTokenAdapter(RefreshTokenAdapter):
    """
    SQLAlchemy implementation of RefreshTokenAdapter.
    """

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        refresh = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(refresh)
        self.session.commit()
        return refresh

    def get_valid(self, *, token_hash: str):
        statement = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
        )
        return self.session.exec(statement).first()

    def invalidate(self, *, token_hash: str) -> None:
        statement = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
        )
        refresh = self.session.exec(statement).first()
        if not refresh:
            return

        refresh.revoked = True
        self.session.add(refresh)
        self.session.commit()
