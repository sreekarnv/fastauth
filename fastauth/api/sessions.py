import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from fastauth.adapters.sqlalchemy.models import User
from fastauth.api.adapter_factory import AdapterFactory
from fastauth.api.dependencies import get_current_user, get_session
from fastauth.core.sessions import (
    SessionNotFoundError,
    delete_all_user_sessions,
    delete_session,
    get_user_sessions,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionResponse(BaseModel):
    id: uuid.UUID
    device: str | None
    ip_address: str | None
    user_agent: str | None
    last_active: str
    created_at: str

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]


class MessageResponse(BaseModel):
    message: str


@router.get("", response_model=SessionListResponse)
def list_sessions(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    List all active sessions for the current user.
    """
    adapters = AdapterFactory(session=session)

    user_sessions = get_user_sessions(
        sessions=adapters.sessions,
        user_id=current_user.id,
    )

    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s.id,
                device=s.device,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                last_active=s.last_active.isoformat(),
                created_at=s.created_at.isoformat(),
            )
            for s in user_sessions
        ]
    )


@router.delete("/all", response_model=MessageResponse)
def delete_all_sessions(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Delete all sessions for the current user except the current one.
    Note: This will log out the user from all other devices.
    """
    adapters = AdapterFactory(session=session)

    delete_all_user_sessions(
        sessions=adapters.sessions,
        user_id=current_user.id,
        except_session_id=None,
    )

    return MessageResponse(message="All sessions deleted successfully")


@router.delete("/{session_id}", response_model=MessageResponse)
def delete_user_session(
    session_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a specific session. Users can only delete their own sessions.
    """
    adapters = AdapterFactory(session=session)

    try:
        delete_session(
            sessions=adapters.sessions,
            session_id=session_id,
            user_id=current_user.id,
        )
    except SessionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return MessageResponse(message="Session deleted successfully")
