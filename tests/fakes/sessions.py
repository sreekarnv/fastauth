import uuid
from datetime import UTC, datetime, timedelta

from fastauth.adapters.base.sessions import SessionAdapter


class FakeSession:
    def __init__(
        self,
        user_id: uuid.UUID,
        device: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ):
        self.id = uuid.uuid4()
        self.user_id = user_id
        self.device = device
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.last_active = datetime.now(UTC)
        self.created_at = datetime.now(UTC)


class FakeSessionAdapter(SessionAdapter):
    def __init__(self):
        self.sessions = {}

    def create_session(
        self,
        *,
        user_id: uuid.UUID,
        device: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ):
        session = FakeSession(
            user_id=user_id,
            device=device,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.sessions[session.id] = session
        return session

    def get_session_by_id(self, session_id: uuid.UUID):
        return self.sessions.get(session_id)

    def get_user_sessions(self, user_id: uuid.UUID):
        return [
            session for session in self.sessions.values() if session.user_id == user_id
        ]

    def delete_session(self, session_id: uuid.UUID) -> None:
        if session_id in self.sessions:
            del self.sessions[session_id]

    def delete_user_sessions(
        self,
        *,
        user_id: uuid.UUID,
        except_session_id: uuid.UUID | None = None,
    ) -> None:
        sessions_to_delete = [
            session_id
            for session_id, session in self.sessions.items()
            if session.user_id == user_id and session_id != except_session_id
        ]
        for session_id in sessions_to_delete:
            del self.sessions[session_id]

    def update_last_active(self, session_id: uuid.UUID) -> None:
        session = self.get_session_by_id(session_id)
        if session:
            session.last_active = datetime.now(UTC)

    def cleanup_inactive_sessions(self, inactive_days: int = 30) -> None:
        cutoff_date = datetime.now(UTC) - timedelta(days=inactive_days)
        sessions_to_delete = [
            session_id
            for session_id, session in self.sessions.items()
            if session.last_active < cutoff_date
        ]
        for session_id in sessions_to_delete:
            del self.sessions[session_id]
