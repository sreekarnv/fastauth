"""Session Management Example - FastAPI Application.

This example demonstrates:
- Session creation on login with device tracking
- View all active sessions across devices
- Revoke individual sessions remotely
- Sign out from all devices except current
- Session metadata (IP, user agent, last active, device info)
"""

import pathlib
import uuid
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from fastauth import Settings as FastAuthSettings
from fastauth.adapters.sqlalchemy import (
    SQLAlchemySessionAdapter,
    SQLAlchemyUserAdapter,
)
from fastauth.adapters.sqlalchemy.models import User
from fastauth.api import dependencies
from fastauth.api.dependencies import get_current_user
from fastauth.core.sessions import (
    create_session,
    delete_all_user_sessions,
    delete_session,
    get_user_sessions,
)
from fastauth.core.users import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    authenticate_user,
    create_user,
)
from fastauth.security.jwt import create_access_token

from .database import create_db_and_tables, get_session
from .helpers import get_session_id_from_token, parse_user_agent
from .schema import LoginRequest, RegisterRequest, SessionResponse, TokenResponse
from .settings import settings as app_settings

BASE_DIR = pathlib.Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(
    title="FastAuth Session Management Example",
    description="Demonstrates multi-device session tracking and management",
    version="0.2.0",
)

app.dependency_overrides[dependencies.get_session] = get_session

fastauth_settings = FastAuthSettings(
    jwt_secret_key=app_settings.jwt_secret_key,
    jwt_algorithm=app_settings.jwt_algorithm,
    access_token_expire_minutes=app_settings.access_token_expire_minutes,
    require_email_verification=app_settings.require_email_verification,
)


@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    create_db_and_tables()


@app.post("/register", response_model=TokenResponse)
def register(
    request: Request,
    payload: RegisterRequest,
    session: Session = Depends(get_session),
):
    """Register a new user and create first session."""
    user_adapter = SQLAlchemyUserAdapter(session)

    try:
        user = create_user(
            users=user_adapter,
            email=payload.email,
            password=payload.password,
        )

        session_adapter = SQLAlchemySessionAdapter(session)
        user_session = create_session(
            sessions=session_adapter,
            users=user_adapter,
            user_id=user.id,
            device=parse_user_agent(request.headers.get("user-agent")),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"session_id": str(user_session.id)},
        )

        return TokenResponse(access_token=access_token)

    except UserAlreadyExistsError:
        raise HTTPException(status_code=409, detail="User already exists")


@app.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    payload: LoginRequest,
    session: Session = Depends(get_session),
):
    """Login and create a new session."""
    user_adapter = SQLAlchemyUserAdapter(session)

    try:
        user = authenticate_user(
            users=user_adapter,
            email=payload.email,
            password=payload.password,
        )

        session_adapter = SQLAlchemySessionAdapter(session)
        user_session = create_session(
            sessions=session_adapter,
            users=user_adapter,
            user_id=user.id,
            device=parse_user_agent(request.headers.get("user-agent")),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"session_id": str(user_session.id)},
        )

        return TokenResponse(access_token=access_token)

    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid email or password")


@app.get("/sessions", response_model=List[SessionResponse])
def list_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """List all active sessions for the current user."""
    session_adapter = SQLAlchemySessionAdapter(session)
    user_sessions = get_user_sessions(
        sessions=session_adapter,
        user_id=current_user.id,
    )

    auth_header = request.headers.get("authorization", "")
    current_session_id = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        current_session_id = get_session_id_from_token(token)

    result = []
    for s in user_sessions:
        result.append(
            SessionResponse(
                id=str(s.id),
                device=s.device,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                last_active=s.last_active,
                created_at=s.created_at,
                is_current=s.id == current_session_id,
            )
        )

    result.sort(key=lambda x: x.last_active, reverse=True)

    return result


@app.delete("/sessions/{session_id}")
def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Revoke a specific session."""
    session_adapter = SQLAlchemySessionAdapter(session)

    try:
        delete_session(
            sessions=session_adapter,
            session_id=uuid.UUID(session_id),
            user_id=current_user.id,
        )
        return {"message": "Session revoked successfully"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Session not found")


@app.post("/sessions/revoke-all")
def revoke_all_sessions(
    request: Request,
    keep_current: bool = True,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Revoke all sessions, optionally keeping the current one."""
    session_adapter = SQLAlchemySessionAdapter(session)

    current_session_id = None
    if keep_current:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            current_session_id = get_session_id_from_token(token)

    delete_all_user_sessions(
        sessions=session_adapter,
        user_id=current_user.id,
        except_session_id=current_session_id,
    )

    if keep_current:
        return {"message": "All other sessions revoked successfully"}
    else:
        return {"message": "All sessions revoked successfully"}


@app.get("/me")
def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get current user information with session count."""
    session_adapter = SQLAlchemySessionAdapter(session)
    user_sessions = get_user_sessions(
        sessions=session_adapter,
        user_id=current_user.id,
    )

    auth_header = request.headers.get("authorization", "")
    current_session_id = None
    current_session_device = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        current_session_id = get_session_id_from_token(token)
        if current_session_id:
            current_sess = next(
                (s for s in user_sessions if s.id == current_session_id), None
            )
            if current_sess:
                current_session_device = current_sess.device

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "active_sessions": len(user_sessions),
        "current_session": {
            "id": str(current_session_id) if current_session_id else None,
            "device": current_session_device,
        },
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.jinja2", context={})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
