import uuid
from abc import ABC, abstractmethod


class SessionAdapter(ABC):
    @abstractmethod
    def create_session(
        self,
        *,
        user_id: uuid.UUID,
        device: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ): ...

    @abstractmethod
    def get_session_by_id(self, session_id: uuid.UUID): ...

    @abstractmethod
    def get_user_sessions(self, user_id: uuid.UUID): ...

    @abstractmethod
    def delete_session(self, session_id: uuid.UUID) -> None: ...

    @abstractmethod
    def delete_user_sessions(
        self, *, user_id: uuid.UUID, except_session_id: uuid.UUID | None = None
    ) -> None: ...

    @abstractmethod
    def update_last_active(self, session_id: uuid.UUID) -> None: ...

    @abstractmethod
    def cleanup_inactive_sessions(self, inactive_days: int = 30) -> None: ...
