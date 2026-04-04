from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from fastauth.api.deps import require_auth

if TYPE_CHECKING:
    from fastauth.types import UserData


class SessionResponse(BaseModel):
    id: str
    user_id: str
    ip_address: str | None = None
    user_agent: str | None = None


class MessageResponse(BaseModel):
    message: str


def create_session_router(auth: object) -> APIRouter:
    router = APIRouter(prefix="/sessions")

    @router.get("", response_model=list[SessionResponse])
    async def list_sessions(
        request: Request, user: UserData = Depends(require_auth)
    ) -> list[SessionResponse]:
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth
        if not hasattr(fa, "session_adapter") or fa.session_adapter is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session management is not configured",
            )
        sessions = await fa.session_adapter.list_user_sessions(user["id"])
        return [
            SessionResponse(
                id=s["id"],
                user_id=s["user_id"],
                ip_address=s.get("ip_address"),
                user_agent=s.get("user_agent"),
            )
            for s in sessions
        ]

    @router.delete("/{session_id}", response_model=MessageResponse)
    async def revoke_session(
        request: Request,
        session_id: str,
        user: UserData = Depends(require_auth),
    ) -> MessageResponse:
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth
        if not hasattr(fa, "session_adapter") or fa.session_adapter is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session management is not configured",
            )
        await fa.session_adapter.delete_session(session_id)
        return MessageResponse(message="Session revoked")

    @router.delete("/all", response_model=MessageResponse)
    async def revoke_all_sessions(
        request: Request, user: UserData = Depends(require_auth)
    ) -> MessageResponse:
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth
        if not hasattr(fa, "session_adapter") or fa.session_adapter is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session management is not configured",
            )
        await fa.session_adapter.delete_user_sessions(user["id"])
        return MessageResponse(message="All sessions revoked")

    return router
