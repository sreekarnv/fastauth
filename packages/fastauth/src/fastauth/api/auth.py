from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from cuid2 import cuid_wrapper
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
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
    from fastauth.app import FastAuth
    from fastauth.types import TokenPair, UserData

generate_token = cuid_wrapper()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None = None
    image: str | None = None
    email_verified: bool
    is_active: bool


class MessageResponse(BaseModel):
    message: str


def _set_auth_cookies(response: Response, tokens: TokenPair, fa: FastAuth) -> None:
    cfg = fa.config
    response.set_cookie(
        key=cfg.cookie_name_access,
        value=tokens["access_token"],
        httponly=cfg.cookie_httponly,
        secure=cfg.effective_cookie_secure,
        samesite=cfg.cookie_samesite,
        max_age=cfg.jwt.access_token_ttl,
        domain=cfg.cookie_domain,
    )
    response.set_cookie(
        key=cfg.cookie_name_refresh,
        value=tokens["refresh_token"],
        httponly=cfg.cookie_httponly,
        secure=cfg.effective_cookie_secure,
        samesite=cfg.cookie_samesite,
        max_age=cfg.jwt.refresh_token_ttl,
        domain=cfg.cookie_domain,
    )


def _clear_auth_cookies(response: Response, fa: FastAuth) -> None:
    cfg = fa.config
    response.delete_cookie(cfg.cookie_name_access, domain=cfg.cookie_domain)
    response.delete_cookie(cfg.cookie_name_refresh, domain=cfg.cookie_domain)


def create_auth_router(auth: object) -> APIRouter:
    router = APIRouter()

    def _get_credentials_provider() -> CredentialsProvider | None:
        from fastauth.app import FastAuth

        assert isinstance(auth, FastAuth)
        for provider in auth.config.providers:
            if isinstance(provider, CredentialsProvider):
                return provider
        return None

    @router.get("/me", response_model=UserResponse)
    async def me(user: UserData = Depends(require_auth)) -> UserData:
        return user

    @router.post(
        "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
    )
    async def register(
        request: Request, body: RegisterRequest, response: Response
    ) -> TokenResponse:

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

        tokens = create_token_pair(user, fa.config, fa.jwks_manager)

        if fa.config.token_delivery == "cookie":
            _set_auth_cookies(response, tokens, fa)

        return TokenResponse(**tokens)

    @router.post("/login", response_model=TokenResponse)
    async def login(
        request: Request, body: LoginRequest, response: Response
    ) -> TokenResponse:

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

        tokens = create_token_pair(user, fa.config, fa.jwks_manager)

        if fa.config.token_delivery == "cookie":
            _set_auth_cookies(response, tokens, fa)

        return TokenResponse(**tokens)

    @router.post("/logout", response_model=MessageResponse)
    async def logout(
        request: Request,
        response: Response,
        user: UserData = Depends(require_auth),
    ) -> MessageResponse:

        fa: FastAuth = request.app.state.fastauth

        if fa.config.hooks:
            await fa.config.hooks.on_signout(user)

        if fa.config.token_delivery == "cookie":
            _clear_auth_cookies(response, fa)

        return MessageResponse(message="Logged out")

    @router.post("/refresh", response_model=TokenResponse)
    async def refresh(
        request: Request,
        response: Response,
        body: RefreshRequest | None = None,
    ) -> TokenResponse:

        fa: FastAuth = request.app.state.fastauth

        token_str = request.cookies.get(fa.config.cookie_name_refresh)
        if not token_str and body:
            token_str = body.refresh_token
        if not token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token required",
            )

        try:
            claims = decode_token(token_str, fa.config, fa.jwks_manager)
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

        tokens = create_token_pair(user, fa.config, fa.jwks_manager)

        if fa.config.token_delivery == "cookie":
            _set_auth_cookies(response, tokens, fa)

        return TokenResponse(**tokens)

    @router.post("/request-verify-email", response_model=MessageResponse)
    async def request_verify_email(
        request: Request, user: UserData = Depends(require_auth)
    ) -> MessageResponse:

        fa: FastAuth = request.app.state.fastauth
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
                "token_type": "verification",
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
            }
        )

        if fa.email_dispatcher:
            await fa.email_dispatcher.send_verification_email(
                user, token, expires_in_minutes=1440
            )

        return MessageResponse(message="Verification email sent")

    @router.get("/verify-email", response_model=MessageResponse)
    async def verify_email_get(request: Request, token: str) -> MessageResponse:
        return await _verify_email(request, token)

    @router.post("/verify-email", response_model=MessageResponse)
    async def verify_email_post(
        request: Request, body: VerifyEmailRequest
    ) -> MessageResponse:
        return await _verify_email(request, body.token)

    async def _verify_email(request: Request, token: str) -> MessageResponse:

        fa: FastAuth = request.app.state.fastauth
        if not fa.config.token_adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token adapter is not configured",
            )

        stored = await fa.config.token_adapter.get_token(token, "verification")
        if not stored:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )

        await fa.config.adapter.update_user(stored["user_id"], email_verified=True)
        await fa.config.token_adapter.delete_token(token)

        user = await fa.config.adapter.get_user_by_id(stored["user_id"])
        if user and fa.config.hooks:
            await fa.config.hooks.on_email_verify(user)

        return MessageResponse(message="Email verified successfully")

    @router.post("/forgot-password", response_model=MessageResponse)
    async def forgot_password(
        request: Request, body: ForgotPasswordRequest
    ) -> MessageResponse:

        fa: FastAuth = request.app.state.fastauth
        if not fa.config.token_adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token adapter is not configured",
            )

        user = await fa.config.adapter.get_user_by_email(body.email)
        if user:
            token = generate_token()
            await fa.config.token_adapter.create_token(
                {
                    "token": token,
                    "user_id": user["id"],
                    "token_type": "password_reset",
                    "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
                }
            )
            if fa.email_dispatcher:
                await fa.email_dispatcher.send_password_reset_email(
                    user, token, expires_in_minutes=30
                )

        return MessageResponse(
            message="If the email exists, a reset link has been sent"
        )

    @router.post("/reset-password", response_model=MessageResponse)
    async def reset_password(
        request: Request, body: ResetPasswordRequest
    ) -> MessageResponse:

        fa: FastAuth = request.app.state.fastauth
        if not fa.config.token_adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token adapter is not configured",
            )

        stored = await fa.config.token_adapter.get_token(body.token, "password_reset")
        if not stored:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        hashed = hash_password(body.new_password)
        await fa.config.adapter.set_hashed_password(stored["user_id"], hashed)
        await fa.config.token_adapter.delete_token(body.token)
        await fa.config.token_adapter.delete_user_tokens(
            stored["user_id"], "password_reset"
        )

        user = await fa.config.adapter.get_user_by_id(stored["user_id"])
        if user and fa.config.hooks:
            await fa.config.hooks.on_password_reset(user)

        return MessageResponse(message="Password reset successfully")

    return router
