from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from cuid2 import cuid_wrapper
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from fastauth.api.deps import require_auth
from fastauth.app import FastAuth
from fastauth.core.credentials import hash_password, verify_password

if TYPE_CHECKING:
    from fastauth.types import UserData

generate_token = cuid_wrapper()


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ChangeEmailRequest(BaseModel):
    new_email: EmailStr
    password: str


class DeleteAccountRequest(BaseModel):
    password: str


class MessageResponse(BaseModel):
    message: str


def create_account_router(auth: object) -> APIRouter:
    router = APIRouter(prefix="/account")

    @router.post("/change-password", response_model=MessageResponse)
    async def change_password(
        request: Request,
        body: ChangePasswordRequest,
        user: UserData = Depends(require_auth),
    ) -> MessageResponse:

        fa: FastAuth = request.app.state.fastauth

        stored_hash = await fa.config.adapter.get_hashed_password(user["id"])
        if not stored_hash or not verify_password(body.current_password, stored_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        hashed = hash_password(body.new_password)
        await fa.config.adapter.set_hashed_password(user["id"], hashed)

        if fa.config.token_adapter:
            await fa.config.token_adapter.delete_user_tokens(user["id"], "refresh")

        return MessageResponse(message="Password changed successfully")

    @router.post("/change-email", response_model=MessageResponse)
    async def change_email(
        request: Request,
        body: ChangeEmailRequest,
        user: UserData = Depends(require_auth),
    ) -> MessageResponse:
        fa: FastAuth = request.app.state.fastauth

        stored_hash = await fa.config.adapter.get_hashed_password(user["id"])
        if not stored_hash or not verify_password(body.password, stored_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is incorrect",
            )

        existing = await fa.config.adapter.get_user_by_email(body.new_email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already in use",
            )

        if not fa.config.token_adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token adapter is not configured",
            )

        token = generate_token()
        await fa.config.token_adapter.create_token(
            {
                "token": token,
                "user_id": user["id"],
                "token_type": "email_change",
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
                "raw_data": {"email": body.new_email},
            }
        )

        if fa.email_dispatcher:
            await fa.email_dispatcher.send_email_change_email(
                user, body.new_email, token, expires_in_minutes=30
            )

        return MessageResponse(message="Confirmation email sent to new address")

    @router.get("/confirm-email-change", response_model=MessageResponse)
    async def confirm_email_change(request: Request, token: str) -> MessageResponse:
        fa: FastAuth = request.app.state.fastauth

        if not fa.config.token_adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token adapter is not configured",
            )

        stored = await fa.config.token_adapter.get_token(token, "email_change")
        if (
            not stored
            or stored["raw_data"] is None
            or "email" not in stored["raw_data"]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token",
            )

        await fa.config.adapter.update_user(
            stored["user_id"], email=stored["raw_data"]["email"]
        )

        await fa.config.token_adapter.delete_token(token)

        return MessageResponse(message="Email changed successfully")

    @router.delete("", response_model=MessageResponse)
    async def delete_account(
        request: Request,
        body: DeleteAccountRequest,
        user: UserData = Depends(require_auth),
    ) -> MessageResponse:
        fa: FastAuth = request.app.state.fastauth

        stored_hash = await fa.config.adapter.get_hashed_password(user["id"])
        if not stored_hash or not verify_password(body.password, stored_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is incorrect",
            )

        await fa.config.adapter.delete_user(user["id"], soft=True)

        return MessageResponse(message="Account deleted successfully")

    return router
