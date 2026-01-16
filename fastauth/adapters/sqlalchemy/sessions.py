"""
SQLAlchemy session adapter implementation.

Provides database operations for user session management using SQLAlchemy/SQLModel.
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlmodel import Session as DBSession
from sqlmodel import select

from fastauth.adapters.base.sessions import SessionAdapter
from fastauth.adapters.sqlalchemy.models import Session


class SQLAlchemySessionAdapter(SessionAdapter):
    """
    SQLAlchemy implementation of SessionAdapter for session database operations.
    """

    def __init__(self, session: DBSession):
        self.session = session

    def create_session(
        self,
        *,
        user_id: uuid.UUID,
        device: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ):
        session_obj = Session(
            user_id=user_id,
            device=device,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(session_obj)
        self.session.commit()
        self.session.refresh(session_obj)
        return session_obj

    def get_session_by_id(self, session_id: uuid.UUID):
        statement = select(Session).where(Session.id == session_id)
        return self.session.exec(statement).first()

    def get_user_sessions(self, user_id: uuid.UUID):
        statement = (
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.last_active.desc())
        )
        return list(self.session.exec(statement).all())

    def delete_session(self, session_id: uuid.UUID) -> None:
        session_obj = self.get_session_by_id(session_id)
        if session_obj:
            self.session.delete(session_obj)
            self.session.commit()

    def delete_user_sessions(
        self, *, user_id: uuid.UUID, except_session_id: uuid.UUID | None = None
    ) -> None:
        statement = select(Session).where(Session.user_id == user_id)

        if except_session_id:
            statement = statement.where(Session.id != except_session_id)

        sessions = self.session.exec(statement).all()
        for session_obj in sessions:
            self.session.delete(session_obj)
        self.session.commit()

    def update_last_active(self, session_id: uuid.UUID) -> None:
        session_obj = self.get_session_by_id(session_id)
        if session_obj:
            session_obj.last_active = datetime.now(UTC)
            self.session.add(session_obj)
            self.session.commit()

    def cleanup_inactive_sessions(self, inactive_days: int = 30) -> None:
        cutoff_date = datetime.now(UTC) - timedelta(days=inactive_days)
        statement = select(Session).where(Session.last_active < cutoff_date)
        sessions = self.session.exec(statement).all()
        for session_obj in sessions:
            self.session.delete(session_obj)
        self.session.commit()
