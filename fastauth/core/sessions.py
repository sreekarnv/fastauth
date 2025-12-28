import uuid

from fastauth.adapters.base.sessions import SessionAdapter
from fastauth.adapters.base.users import UserAdapter


class SessionNotFoundError(Exception):
    """Raised when a session is not found."""


def create_session(
    *,
    sessions: SessionAdapter,
    users: UserAdapter,
    user_id: uuid.UUID,
    device: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
):
    """
    Create a new session for a user.

    Args:
        sessions: Session adapter for database operations
        users: User adapter for database operations
        user_id: User's unique identifier
        device: Device information
        ip_address: IP address of the client
        user_agent: User agent string

    Returns:
        Created session object
    """
    session = sessions.create_session(
        user_id=user_id,
        device=device,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    users.update_last_login(user_id=user_id)

    return session


def get_user_sessions(
    *,
    sessions: SessionAdapter,
    user_id: uuid.UUID,
):
    """
    Get all active sessions for a user.

    Args:
        sessions: Session adapter for database operations
        user_id: User's unique identifier

    Returns:
        List of session objects
    """
    return sessions.get_user_sessions(user_id)


def delete_session(
    *,
    sessions: SessionAdapter,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """
    Delete a specific session.

    Args:
        sessions: Session adapter for database operations
        session_id: Session's unique identifier
        user_id: User's unique identifier (for authorization)

    Raises:
        SessionNotFoundError: If session doesn't exist or doesn't belong to user
    """
    session = sessions.get_session_by_id(session_id)

    if not session or session.user_id != user_id:
        raise SessionNotFoundError("Session not found")

    sessions.delete_session(session_id)


def delete_all_user_sessions(
    *,
    sessions: SessionAdapter,
    user_id: uuid.UUID,
    except_session_id: uuid.UUID | None = None,
) -> None:
    """
    Delete all sessions for a user, optionally excluding the current session.

    Args:
        sessions: Session adapter for database operations
        user_id: User's unique identifier
        except_session_id: Optional session ID to keep (current session)
    """
    sessions.delete_user_sessions(
        user_id=user_id,
        except_session_id=except_session_id,
    )


def update_session_activity(
    *,
    sessions: SessionAdapter,
    session_id: uuid.UUID,
) -> None:
    """
    Update the last active timestamp for a session.

    Args:
        sessions: Session adapter for database operations
        session_id: Session's unique identifier
    """
    sessions.update_last_active(session_id)


def cleanup_inactive_sessions(
    *,
    sessions: SessionAdapter,
    inactive_days: int = 30,
) -> None:
    """
    Remove sessions that haven't been active for a specified number of days.

    Args:
        sessions: Session adapter for database operations
        inactive_days: Number of days of inactivity before cleanup (default: 30)
    """
    sessions.cleanup_inactive_sessions(inactive_days)
