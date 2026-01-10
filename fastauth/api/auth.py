import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from fastauth.api.adapter_factory import AdapterFactory
from fastauth.api.dependencies import get_session
from fastauth.api.schemas import (
    EmailVerificationConfirm,
    EmailVerificationRequest,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from fastauth.core.constants import ErrorMessages
from fastauth.core.email_verification import (
    EmailVerificationError,
    confirm_email_verification,
    request_email_verification,
)
from fastauth.core.password_reset import (
    PasswordResetError,
    confirm_password_reset,
    request_password_reset,
)
from fastauth.core.refresh_tokens import (
    RefreshTokenError,
    create_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
)
from fastauth.core.sessions import create_session
from fastauth.core.users import (
    EmailNotVerifiedError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    authenticate_user,
    create_user,
)
from fastauth.email.factory import get_email_client
from fastauth.security.jwt import create_access_token
from fastauth.security.limits import (
    email_verification_rate_limiter,
    login_rate_limiter,
    register_rate_limiter,
)
from fastauth.security.rate_limit import RateLimitExceeded

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


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
            detail=ErrorMessages.RATE_LIMIT_REGISTRATION,
        )

    adapters = AdapterFactory(session=session)

    try:
        user = create_user(
            users=adapters.users, email=payload.email, password=payload.password
        )
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorMessages.USER_ALREADY_EXISTS,
        )

    verification_token = request_email_verification(
        users=adapters.users,
        verifications=adapters.verifications,
        email=user.email,
    )

    if verification_token:
        email_client = get_email_client()
        email_client.send_verification_email(
            to=user.email,
            token=verification_token,
        )
        logger.debug(f"Email verification token for {user.email}: {verification_token}")

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(
        refresh_tokens=adapters.refresh_tokens,
        user_id=user.id,
    )

    create_session(
        sessions=adapters.sessions,
        users=adapters.users,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
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
            detail=ErrorMessages.RATE_LIMIT_LOGIN,
        )

    adapters = AdapterFactory(session=session)

    try:
        user = authenticate_user(
            users=adapters.users,
            email=payload.email,
            password=payload.password,
        )
    except EmailNotVerifiedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorMessages.EMAIL_NOT_VERIFIED,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessages.INVALID_CREDENTIALS,
        )

    login_rate_limiter.reset(key)

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(
        refresh_tokens=adapters.refresh_tokens,
        user_id=user.id,
    )

    create_session(
        sessions=adapters.sessions,
        users=adapters.users,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
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
    adapters = AdapterFactory(session=session)

    try:
        result = rotate_refresh_token(
            refresh_tokens=adapters.refresh_tokens,
            token=payload.refresh_token,
        )
    except RefreshTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    refresh_token, user_id = result
    access_token = create_access_token(subject=str(user_id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    session: Session = Depends(get_session),
):
    adapters = AdapterFactory(session=session)
    revoke_refresh_token(
        refresh_tokens=adapters.refresh_tokens,
        token=payload.refresh_token,
    )

    return None


@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
def password_reset_request(
    payload: PasswordResetRequest,
    session: Session = Depends(get_session),
):
    adapters = AdapterFactory(session=session)

    token = request_password_reset(
        users=adapters.users,
        resets=adapters.password_resets,
        email=payload.email,
    )

    if token:
        email_client = get_email_client()
        email_client.send_password_reset_email(
            to=payload.email,
            token=token,
        )
        logger.debug(f"Password reset token: {token}")

    return None


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def password_reset_confirm(
    payload: PasswordResetConfirm,
    session: Session = Depends(get_session),
):
    adapters = AdapterFactory(session=session)

    try:
        confirm_password_reset(
            users=adapters.users,
            resets=adapters.password_resets,
            token=payload.token,
            new_password=payload.new_password,
        )
    except PasswordResetError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMessages.INVALID_OR_EXPIRED_RESET_TOKEN,
        )

    return None


@router.get("/password-reset/validate")
def password_reset_validate(
    token: str,
    session: Session = Depends(get_session),
):
    """
    Validate a password reset token via GET with query parameter.

    This endpoint checks if a reset token is valid without consuming it.
    Useful for showing a password reset form or error message.
    """
    from datetime import UTC, datetime

    from fastauth.security.refresh import hash_refresh_token

    adapters = AdapterFactory(session=session)

    token_hash = hash_refresh_token(token)
    record = adapters.password_resets.get_valid(token_hash=token_hash)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMessages.INVALID_OR_EXPIRED_RESET_TOKEN,
        )

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expired reset token",
        )

    return {
        "message": "Valid reset token",
        "status": "valid",
        "token": token,
    }


@router.post("/email-verification/request", status_code=status.HTTP_204_NO_CONTENT)
def email_verification_request(
    payload: EmailVerificationRequest,
    session: Session = Depends(get_session),
):
    adapters = AdapterFactory(session=session)

    token = request_email_verification(
        users=adapters.users,
        verifications=adapters.verifications,
        email=payload.email,
    )

    if token:
        email_client = get_email_client()
        email_client.send_verification_email(
            to=payload.email,
            token=token,
        )
        logger.debug(f"Email verification token: {token}")

    return None


def _confirm_email_verification_helper(token: str, session: Session) -> None:
    """Helper function to verify email token."""
    adapters = AdapterFactory(session=session)

    try:
        confirm_email_verification(
            users=adapters.users,
            verifications=adapters.verifications,
            token=token,
        )
    except EmailVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorMessages.INVALID_OR_EXPIRED_VERIFICATION_TOKEN,
        )


@router.post("/email-verification/confirm", status_code=status.HTTP_204_NO_CONTENT)
def email_verification_confirm(
    payload: EmailVerificationConfirm,
    session: Session = Depends(get_session),
):
    """Confirm email verification via POST with JSON payload."""
    _confirm_email_verification_helper(payload.token, session)
    return None


@router.get("/email-verification/confirm")
def email_verification_confirm_get(
    token: str,
    session: Session = Depends(get_session),
):
    """Confirm email verification via GET with query parameter.

    This endpoint enables clickable email verification links.
    """
    _confirm_email_verification_helper(token, session)
    return {
        "message": "Email verified successfully",
        "status": "success",
    }


@router.post("/email-verification/resend", status_code=status.HTTP_204_NO_CONTENT)
def resend_email_verification(
    payload: EmailVerificationRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    key = request.client.host

    try:
        email_verification_rate_limiter.hit(key)
    except RateLimitExceeded:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ErrorMessages.RATE_LIMIT_GENERAL,
        )

    adapters = AdapterFactory(session=session)

    token = request_email_verification(
        users=adapters.users,
        verifications=adapters.verifications,
        email=payload.email,
    )

    if token:
        email_client = get_email_client()
        email_client.send_verification_email(
            to=payload.email,
            token=token,
        )
        logger.debug(f"Resent email verification token: {token}")

    return None
