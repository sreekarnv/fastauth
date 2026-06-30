from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from fastauth.api.deps import enforce_cookie_csrf, require_auth
from fastauth.api.schemas import ErrorDetail
from fastauth.core.credentials import hash_password
from fastauth.core.one_time_tokens import (
    generate_one_time_token,
    hash_one_time_token,
)
from fastauth.core.tokens import async_create_token_pair, decode_token
from fastauth.exceptions import (
    AuthenticationError,
    ConfigError,
    InvalidTokenError,
    UserAlreadyExistsError,
)
from fastauth.providers.credentials import CredentialsProvider

if TYPE_CHECKING:
    from fastauth.app import FastAuth
    from fastauth.types import TokenPair, UserData


async def _issue_tracked_tokens(
    fa: FastAuth, user: UserData, remember: bool = False
) -> TokenPair:
    """Create a token pair and, when *token_adapter* is configured, record the
    refresh-token JTI in the allowlist so that reuse can be detected later."""
    refresh_ttl = (
        fa.config.jwt.remember_me_ttl if remember else fa.config.jwt.refresh_token_ttl
    )
    modify_jwt = fa.config.hooks.modify_jwt if fa.config.hooks else None
    tokens = await async_create_token_pair(
        user,
        fa.config,
        fa.jwks_manager,
        refresh_ttl_override=refresh_ttl,
        modify_jwt=modify_jwt,
    )
    if fa.config.token_adapter:
        refresh_claims = decode_token(
            tokens["refresh_token"], fa.config, fa.jwks_manager
        )
        jti: str = refresh_claims["jti"]
        expires_at = datetime.fromtimestamp(refresh_claims["exp"], tz=timezone.utc)
        await fa.config.token_adapter.create_token(
            {
                "token": jti,
                "user_id": user["id"],
                "token_type": "refresh_jti",
                "expires_at": expires_at,
                "raw_data": None,
            }
        )
    return tokens


def _token_response_payload(
    fa: FastAuth, tokens: TokenPair
) -> TokenResponse | MessageResponse:
    """Return the appropriate response model for the configured token delivery.

    In ``"json"`` mode the full token pair is returned. In ``"cookie"`` mode
    the response body intentionally contains no token material — the tokens
    were set on the response as ``HttpOnly`` cookies by the caller.
    """
    if fa.config.token_delivery == "cookie":
        return MessageResponse(message="Authentication successful")
    return TokenResponse(**tokens)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False


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


def _set_auth_cookies(
    response: Response,
    tokens: TokenPair,
    fa: FastAuth,
    refresh_max_age: int | None = None,
) -> None:
    cfg = fa.config
    if refresh_max_age is None:
        refresh_max_age = cfg.jwt.refresh_token_ttl
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
        max_age=refresh_max_age,
        domain=cfg.cookie_domain,
    )
    response.set_cookie(
        key=cfg.csrf_cookie_name,
        value=token_urlsafe(32),
        httponly=False,
        secure=cfg.effective_cookie_secure,
        samesite=cfg.cookie_samesite,
        max_age=refresh_max_age,
        domain=cfg.cookie_domain,
    )


def _clear_auth_cookies(response: Response, fa: FastAuth) -> None:
    cfg = fa.config
    response.delete_cookie(cfg.cookie_name_access, domain=cfg.cookie_domain)
    response.delete_cookie(cfg.cookie_name_refresh, domain=cfg.cookie_domain)
    response.delete_cookie(cfg.csrf_cookie_name, domain=cfg.cookie_domain)


def create_auth_router(auth: object) -> APIRouter:
    router = APIRouter(
        responses={
            400: {
                "model": ErrorDetail,
                "description": "Bad request or missing configuration",
            },
            401: {
                "model": ErrorDetail,
                "description": "Authentication required or token invalid",
            },
        }
    )

    def _get_credentials_provider() -> CredentialsProvider | None:
        from fastauth.app import FastAuth

        if not isinstance(auth, FastAuth):
            raise ConfigError("auth must be a FastAuth instance")
        for provider in auth.config.providers:
            if isinstance(provider, CredentialsProvider):
                return provider
        return None

    @router.get("/me", response_model=UserResponse)
    async def me(user: UserData = Depends(require_auth)) -> UserData:
        return user

    @router.post(
        "/register",
        response_model=None,
        status_code=status.HTTP_201_CREATED,
        responses={
            201: {
                "model": TokenResponse,
                "description": "Created with token pair (JSON mode)",
            },
            409: {"model": ErrorDetail, "description": "Email already registered"},
        },
    )
    async def register(
        request: Request,
        body: RegisterRequest,
        response: Response,
    ) -> TokenResponse | MessageResponse:

        fa: FastAuth = request.app.state.fastauth
        provider = _get_credentials_provider()

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credentials provider is not configured",
            )

        try:
            from fastauth.core.credentials import validate_password

            validate_password(body.password, fa.config.password)
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
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

        if fa.role_adapter and fa.config.default_role:
            from fastauth.core.rbac import assign_default_role

            await assign_default_role(
                fa.role_adapter, user["id"], fa.config.default_role
            )

        if fa.config.hooks:
            await fa.config.hooks.on_signup(user)

        tokens = await _issue_tracked_tokens(fa, user)

        if fa.config.token_delivery == "cookie":
            _set_auth_cookies(response, tokens, fa)

        return _token_response_payload(fa, tokens)

    @router.post(
        "/login",
        response_model=None,
        responses={
            200: {
                "model": TokenResponse,
                "description": "Token pair issued (JSON mode)",
            },
        },
    )
    async def login(
        request: Request,
        body: LoginRequest,
        response: Response,
    ) -> TokenResponse | MessageResponse:

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
                token_adapter=fa.config.token_adapter,
                security=fa.config.security,
            )
        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            ) from e

        if fa.config.hooks:
            allowed = await fa.config.hooks.allow_signin(user, "credentials")
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sign in not allowed",
                )
            await fa.config.hooks.on_signin(user, "credentials")

        tokens = await _issue_tracked_tokens(fa, user, remember=body.remember)

        if fa.config.token_delivery == "cookie":
            refresh_max_age = (
                fa.config.jwt.remember_me_ttl
                if body.remember
                else fa.config.jwt.refresh_token_ttl
            )
            _set_auth_cookies(response, tokens, fa, refresh_max_age=refresh_max_age)

        return _token_response_payload(fa, tokens)

    @router.post("/logout", response_model=MessageResponse)
    async def logout(
        request: Request,
        response: Response,
        user: UserData = Depends(require_auth),
    ) -> MessageResponse:

        fa: FastAuth = request.app.state.fastauth

        if fa.config.hooks:
            await fa.config.hooks.on_signout(user)

        if fa.config.token_adapter:
            await fa.config.token_adapter.delete_user_tokens(user["id"], "refresh_jti")

        if fa.config.token_delivery == "cookie":
            _clear_auth_cookies(response, fa)

        return MessageResponse(message="Logged out")

    @router.post(
        "/refresh",
        response_model=None,
        responses={
            200: {
                "model": TokenResponse,
                "description": "Rotated token pair (JSON mode)",
            },
        },
    )
    async def refresh(
        request: Request,
        response: Response,
        body: RefreshRequest | None = None,
    ) -> TokenResponse | MessageResponse:

        fa: FastAuth = request.app.state.fastauth

        token_str = body.refresh_token if body else None
        if not token_str:
            token_str = request.cookies.get(fa.config.cookie_name_refresh)
            if token_str:
                enforce_cookie_csrf(request)
        if not token_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token required",
            )

        try:
            claims = decode_token(token_str, fa.config, fa.jwks_manager)
        except InvalidTokenError as e:
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

        old_jti = claims.get("jti")
        if fa.config.token_adapter and old_jti:
            # Atomically consume the JTI. If `consume_token` returns None the
            # token is either already used (replay) or never existed — either
            # way, revoke the entire refresh-token family for this user.
            consumed = await fa.config.token_adapter.consume_token(
                old_jti, "refresh_jti"
            )
            if consumed is None:
                await fa.config.token_adapter.delete_user_tokens(
                    user["id"], "refresh_jti"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has already been used",
                )

        if fa.config.hooks:
            await fa.config.hooks.on_token_refresh(user)

        tokens = await _issue_tracked_tokens(fa, user)

        if fa.config.token_delivery == "cookie":
            _set_auth_cookies(response, tokens, fa)

        return _token_response_payload(fa, tokens)

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

        token = generate_one_time_token()
        await fa.config.token_adapter.create_token(
            {
                "token": hash_one_time_token(token),
                "user_id": user["id"],
                "token_type": "verification",
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
                "raw_data": None,
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

        stored = await fa.config.token_adapter.consume_token(
            hash_one_time_token(token), "verification"
        )
        if not stored:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )

        await fa.config.adapter.update_user(stored["user_id"], email_verified=True)

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
            token = generate_one_time_token()
            await fa.config.token_adapter.create_token(
                {
                    "token": hash_one_time_token(token),
                    "user_id": user["id"],
                    "token_type": "password_reset",
                    "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
                    "raw_data": None,
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

        token_hash = hash_one_time_token(body.token)
        stored = await fa.config.token_adapter.consume_token(
            token_hash, "password_reset"
        )
        if not stored:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        from fastauth.core.credentials import validate_password

        try:
            validate_password(body.new_password, fa.config.password)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

        hashed = hash_password(body.new_password)
        await fa.config.adapter.set_hashed_password(stored["user_id"], hashed)
        await fa.config.token_adapter.delete_user_tokens(
            stored["user_id"], "password_reset"
        )
        # Revoke all outstanding refresh-token JTIs so any existing
        # browser/app session that knows the old password is forced to
        # re-authenticate.
        await fa.config.token_adapter.delete_user_tokens(
            stored["user_id"], "refresh_jti"
        )

        user = await fa.config.adapter.get_user_by_id(stored["user_id"])
        if user and fa.config.hooks:
            await fa.config.hooks.on_password_reset(user)

        return MessageResponse(message="Password reset successfully")

    return router
