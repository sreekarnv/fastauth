"""
Session adapter interface.

Defines the abstract interface for user session management.
Handles session creation, retrieval, deletion, and cleanup.
"""

import uuid
from abc import ABC, abstractmethod
from typing import Any


class SessionAdapter(ABC):
    """
    Abstract base class for user session database operations.

    Implementations must provide database-specific logic for session management.
    Sessions track user login state across multiple devices.
    """

    @abstractmethod
    def create_session(
        self,
        *,
        user_id: uuid.UUID,
        device: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Any:
        """
        Create a new user session.

        Args:
            user_id: User's unique identifier
            device: Optional device name/description
            ip_address: Client IP address
            user_agent: Browser/client user agent string

        Returns:
            Created session object
        """
        ...

    @abstractmethod
    def get_session_by_id(self, session_id: uuid.UUID) -> Any:
        """
        Retrieve a session by its ID.

        Args:
            session_id: Session's unique identifier

        Returns:
            Session object if found, None otherwise
        """
        ...

    @abstractmethod
    def get_user_sessions(self, user_id: uuid.UUID) -> list[Any]:
        """
        Get all sessions for a user.

        Args:
            user_id: User's unique identifier

        Returns:
            List of session objects
        """
        ...

    @abstractmethod
    def delete_session(self, session_id: uuid.UUID) -> None:
        """
        Delete a specific session.

        Args:
            session_id: Session's unique identifier
        """
        ...

    @abstractmethod
    def delete_user_sessions(
        self, *, user_id: uuid.UUID, except_session_id: uuid.UUID | None = None
    ) -> None:
        """
        Delete all sessions for a user, optionally keeping one.

        Args:
            user_id: User's unique identifier
            except_session_id: Optional session ID to preserve
        """
        ...

    @abstractmethod
    def update_last_active(self, session_id: uuid.UUID) -> None:
        """
        Update the last active timestamp for a session.

        Args:
            session_id: Session's unique identifier
        """
        ...

    @abstractmethod
    def cleanup_inactive_sessions(self, inactive_days: int = 30) -> None:
        """
        Remove sessions that have been inactive for too long.

        Args:
            inactive_days: Number of days of inactivity before cleanup
        """
        ...
