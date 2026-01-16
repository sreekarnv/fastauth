"""
SQLAlchemy email verification adapter implementation.

Provides database operations for email verification token \
    storage using SQLAlchemy/SQLModel.
"""

import uuid
from datetime import datetime

from sqlmodel import Session, select

from fastauth.adapters.base.email_verification import EmailVerificationAdapter
from fastauth.adapters.sqlalchemy.models import EmailVerificationToken


class SQLAlchemyEmailVerificationAdapter(EmailVerificationAdapter):
    """
    SQLAlchemy implementation of EmailVerificationAdapter.
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
        record = EmailVerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(record)
        self.session.commit()

    def get_valid(self, *, token_hash: str):
        statement = select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.used.is_(False),
        )
        return self.session.exec(statement).first()

    def invalidate(self, *, token_hash: str) -> None:
        statement = select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.used.is_(False),
        )
        record = self.session.exec(statement).first()
        if not record:
            return

        record.used = True
        self.session.add(record)
        self.session.commit()
