from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session

from fastauth.api.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest
)
from fastauth.core.users import (
    create_user,
    authenticate_user,
    UserAlreadyExistsError,
    InvalidCredentialsError,
)
from fastauth.core.refresh_tokens import (
    create_refresh_token,
    rotate_refresh_token,
    revoke_refresh_token,
    RefreshTokenError,
)
from fastauth.core.password_reset import (
    request_password_reset,
    confirm_password_reset,
    PasswordResetError,
    
)
from fastauth.db.session import get_session
from fastauth.security.jwt import create_access_token
from fastauth.security.limits import login_rate_limiter, register_rate_limiter
from fastauth.security.rate_limit import RateLimitExceeded


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(
    payload: RegisterRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    key = request.client.host

    try:
        register_rate_limiter.hit(key)
    except RateLimitExceeded:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Try again later.",
        )

    try:
        user = create_user(
            session=session,
            email=payload.email,
            password=payload.password,
        )
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(
        session=session,
        user_id=user.id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    key = f"{request.client.host}:{payload.email}"

    try:
        login_rate_limiter.hit(key)
    except RateLimitExceeded:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )

    try:
        user = authenticate_user(
            session=session,
            email=payload.email,
            password=payload.password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    login_rate_limiter.reset(key)

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(
        session=session,
        user_id=user.id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshRequest,
    session: Session = Depends(get_session),
):
    try:
        result = rotate_refresh_token(
            session=session,
            token=payload.refresh_token,
        )
    except RefreshTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    access_token = create_access_token(subject=str(result.user_id))

    return {
        "access_token": access_token,
        "refresh_token": result.refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    session: Session = Depends(get_session),
):
    revoke_refresh_token(
        session=session,
        token=payload.refresh_token,
    )


@router.post("/password-reset/request", status_code=204)
def password_reset_request(
    payload: PasswordResetRequest,
    session: Session = Depends(get_session),
):
    token = request_password_reset(
        session=session,
        email=payload.email,
    )

    if token:
        # TODO: impl send email
        print("Password reset token:", token)

    return None


@router.post("/password-reset/confirm", status_code=204)
def password_reset_confirm(
    payload: PasswordResetConfirm,
    session: Session = Depends(get_session),
):
    try:
        confirm_password_reset(
            session=session,
            token=payload.token,
            new_password=payload.new_password,
        )
    except PasswordResetError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    return None