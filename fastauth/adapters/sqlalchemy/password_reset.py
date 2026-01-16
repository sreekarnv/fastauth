"""
SQLAlchemy password reset adapter implementation.

Provides database operations for password reset token storage using SQLAlchemy/SQLModel.
"""

import uuid
from datetime import datetime

from sqlmodel import Session, select

from fastauth.adapters.base.password_reset import PasswordResetAdapter
from fastauth.adapters.sqlalchemy.models import PasswordResetToken


class SQLAlchemyPasswordResetAdapter(PasswordResetAdapter):
    """
    SQLAlchemy implementation of PasswordResetAdapter.
    """

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        record = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(record)
        self.session.commit()

    def get_valid(self, *, token_hash: str):
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used.is_(False),
        )
        return self.session.exec(statement).first()

    def invalidate(self, *, token_hash: str) -> None:
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used.is_(False),
        )
        record = self.session.exec(statement).first()
        if not record:
            return

        record.used = True
        self.session.add(record)
        self.session.commit()
