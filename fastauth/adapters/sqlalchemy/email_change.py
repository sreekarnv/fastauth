"""
SQLAlchemy email change adapter implementation.

Provides database operations for email change token storage using SQLAlchemy/SQLModel.
"""

import uuid
from datetime import datetime

from sqlmodel import Session, select

from fastauth.adapters.base.email_change import EmailChangeAdapter
from fastauth.adapters.sqlalchemy.models import EmailChangeToken


class SQLAlchemyEmailChangeAdapter(EmailChangeAdapter):
    """
    SQLAlchemy implementation of EmailChangeAdapter.
    """

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        user_id: uuid.UUID,
        new_email: str,
        token_hash: str,
        expires_at: datetime,
    ):
        token = EmailChangeToken(
            user_id=user_id,
            new_email=new_email,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        self.session.commit()
        return token

    def get_valid(self, *, token_hash: str):
        return self.session.exec(
            select(EmailChangeToken).where(
                EmailChangeToken.token_hash == token_hash,
                EmailChangeToken.used == False,  # noqa: E712
            )
        ).first()

    def invalidate(self, *, token_hash: str) -> None:
        token = self.session.exec(
            select(EmailChangeToken).where(EmailChangeToken.token_hash == token_hash)
        ).first()
        if token:
            token.used = True
            self.session.add(token)
            self.session.commit()
