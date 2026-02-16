from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, select

from fastauth.adapters.sqlalchemy.models import SessionModel
from fastauth.types import SessionData


def _to_session_data(session: SessionModel) -> SessionData:
    return {
        "id": session.id,
        "user_id": session.user_id,
        "expires_at": session.expires_at,
        "ip_address": session.ip_address,
        "user_agent": session.user_agent,
    }


class SQLAlchemySessionAdapter:
    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    async def create_session(self, session: SessionData) -> SessionData:
        async with self._session_factory() as db:
            model = SessionModel(
                id=session["id"],
                user_id=session["user_id"],
                expires_at=session["expires_at"],
                ip_address=session.get("ip_address"),
                user_agent=session.get("user_agent"),
                created_at=datetime.now(timezone.utc),
            )
            db.add(model)
            await db.commit()
            return session

    async def get_session(self, session_id: str) -> SessionData | None:
        async with self._session_factory() as db:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(SessionModel).where(
                    SessionModel.id == session_id,
                    SessionModel.expires_at > now,
                )
            )
            model = result.scalar_one_or_none()
            return _to_session_data(model) if model else None

    async def delete_session(self, session_id: str) -> None:
        async with self._session_factory() as db:
            await db.execute(
                delete(SessionModel).where(SessionModel.id == session_id)
            )
            await db.commit()

    async def delete_user_sessions(self, user_id: str) -> None:
        async with self._session_factory() as db:
            await db.execute(
                delete(SessionModel).where(SessionModel.user_id == user_id)
            )
            await db.commit()

    async def cleanup_expired(self) -> int:
        async with self._session_factory() as db:
            now = datetime.now(timezone.utc)
            count_result = await db.execute(
                select(func.count())
                .select_from(SessionModel)
                .where(SessionModel.expires_at <= now)
            )
            count = count_result.scalar() or 0
            await db.execute(
                delete(SessionModel).where(SessionModel.expires_at <= now)
            )
            await db.commit()
            return count
