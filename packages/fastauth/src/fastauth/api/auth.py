from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from fastauth.api.deps import require_auth
from fastauth.core.credentials import hash_password
from fastauth.core.tokens import create_token_pair, decode_token
from fastauth.exceptions import (
    AuthenticationError,
    UserAlreadyExistsError,
)
from fastauth.providers.credentials import CredentialsProvider

if TYPE_CHECKING:
    from fastauth.types import UserData


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class MessageResponse(BaseModel):
    message: str


def create_auth_router(auth: object) -> APIRouter:
    router = APIRouter()

    def _get_credentials_provider() -> CredentialsProvider | None:
        from fastauth.app import FastAuth

        assert isinstance(auth, FastAuth)
        for provider in auth.config.providers:
            if isinstance(provider, CredentialsProvider):
                return provider
        return None

    @router.post("/register", response_model=TokenResponse)
    async def register(request: Request, body: RegisterRequest) -> TokenResponse:
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth
        provider = _get_credentials_provider()

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credentials provider is not configured",
            )

        try:
            hashed = hash_password(body.password)
            user = await fa.config.adapter.create_user(
                email=body.email,
                hashed_password=hashed,
                name=body.name,
            )
        except UserAlreadyExistsError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            ) from e

        if fa.config.hooks:
            await fa.config.hooks.on_signup(user)

        tokens = create_token_pair(user, fa.config)
        return TokenResponse(**tokens)

    @router.post("/login", response_model=TokenResponse)
    async def login(request: Request, body: LoginRequest) -> TokenResponse:
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth
        provider = _get_credentials_provider()
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credentials provider is not configured",
            )

        try:
            user = await provider.authenticate(
                adapter=fa.config.adapter,
                email=body.email,
                password=body.password,
            )
        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            ) from e

        if fa.config.hooks:
            await fa.config.hooks.on_signin(user, "credentials")

        tokens = create_token_pair(user, fa.config)
        return TokenResponse(**tokens)

    @router.post("/logout", response_model=MessageResponse)
    async def logout(
        request: Request, user: UserData = Depends(require_auth)
    ) -> MessageResponse:
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth

        if fa.config.hooks:
            await fa.config.hooks.on_signout(user)

        return MessageResponse(message="Logged out")

    @router.post("/refresh", response_model=TokenResponse)
    async def refresh(request: Request, body: RefreshRequest) -> TokenResponse:
        from fastauth.app import FastAuth

        fa: FastAuth = request.app.state.fastauth

        try:
            claims = decode_token(body.refresh_token, fa.config)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from e

        if claims.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user = await fa.config.adapter.get_user_by_id(claims["sub"])
        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if fa.config.hooks:
            await fa.config.hooks.on_token_refresh(user)

        tokens = create_token_pair(user, fa.config)
        return TokenResponse(**tokens)

    return router
