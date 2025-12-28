from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from fastauth.adapters.sqlalchemy.email_verification import (
    SQLAlchemyEmailVerificationAdapter,
)
from fastauth.adapters.sqlalchemy.password_reset import SQLAlchemyPasswordResetAdapter
from fastauth.adapters.sqlalchemy.refresh_tokens import SQLAlchemyRefreshTokenAdapter
from fastauth.adapters.sqlalchemy.sessions import SQLAlchemySessionAdapter
from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter
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

    users = SQLAlchemyUserAdapter(session=session)

    try:
        user = create_user(users=users, email=payload.email, password=payload.password)
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    verifications = SQLAlchemyEmailVerificationAdapter(session=session)
    verification_token = request_email_verification(
        users=users,
        verifications=verifications,
        email=user.email,
    )

    if verification_token:
        email_client = get_email_client()
        email_client.send_verification_email(
            to=user.email,
            token=verification_token,
        )
        print(f"Email verification token for {user.email}: {verification_token}")

    refresh_tokens = SQLAlchemyRefreshTokenAdapter(session=session)
    sessions = SQLAlchemySessionAdapter(session=session)

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(
        refresh_tokens=refresh_tokens,
        user_id=user.id,
    )

    create_session(
        sessions=sessions,
        users=users,
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
            detail="Too many login attempts. Try again later.",
        )

    users = SQLAlchemyUserAdapter(session=session)

    try:
        user = authenticate_user(
            users=users,
            email=payload.email,
            password=payload.password,
        )
    except EmailNotVerifiedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address is not verified",
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    login_rate_limiter.reset(key)

    refresh_tokens = SQLAlchemyRefreshTokenAdapter(session=session)
    sessions = SQLAlchemySessionAdapter(session=session)

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(
        refresh_tokens=refresh_tokens,
        user_id=user.id,
    )

    create_session(
        sessions=sessions,
        users=users,
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
    try:
        refresh_tokens = SQLAlchemyRefreshTokenAdapter(session=session)
        result = rotate_refresh_token(
            refresh_tokens=refresh_tokens,
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
    refresh_tokens = SQLAlchemyRefreshTokenAdapter(session=session)
    revoke_refresh_token(
        refresh_tokens=refresh_tokens,
        token=payload.refresh_token,
    )

    return None


@router.post("/password-reset/request", status_code=204)
def password_reset_request(
    payload: PasswordResetRequest,
    session: Session = Depends(get_session),
):
    users = SQLAlchemyUserAdapter(session)
    resets = SQLAlchemyPasswordResetAdapter(session)

    token = request_password_reset(
        users=users,
        resets=resets,
        email=payload.email,
    )

    if token:
        email_client = get_email_client()
        email_client.send_password_reset_email(
            to=payload.email,
            token=token,
        )
        print("Password reset token:", token)

    return None


@router.post("/password-reset/confirm", status_code=204)
def password_reset_confirm(
    payload: PasswordResetConfirm,
    session: Session = Depends(get_session),
):
    users = SQLAlchemyUserAdapter(session)
    resets = SQLAlchemyPasswordResetAdapter(session)

    try:
        confirm_password_reset(
            users=users,
            resets=resets,
            token=payload.token,
            new_password=payload.new_password,
        )
    except PasswordResetError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    return None


@router.post("/email-verification/request", status_code=204)
def email_verification_request(
    payload: EmailVerificationRequest,
    session: Session = Depends(get_session),
):
    users = SQLAlchemyUserAdapter(session)
    verifications = SQLAlchemyEmailVerificationAdapter(session)

    token = request_email_verification(
        users=users,
        verifications=verifications,
        email=payload.email,
    )

    if token:
        email_client = get_email_client()
        email_client.send_verification_email(
            to=payload.email,
            token=token,
        )
        print("Email verification token:", token)

    return None


@router.post("/email-verification/confirm", status_code=204)
def email_verification_confirm(
    payload: EmailVerificationConfirm,
    session: Session = Depends(get_session),
):
    try:
        users = SQLAlchemyUserAdapter(session)
        verifications = SQLAlchemyEmailVerificationAdapter(session)

        confirm_email_verification(
            users=users,
            verifications=verifications,
            token=payload.token,
        )
    except EmailVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    return None


@router.post("/email-verification/resend", status_code=204)
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
            detail="Too many requests. Try again later.",
        )

    users = SQLAlchemyUserAdapter(session)
    verifications = SQLAlchemyEmailVerificationAdapter(session)

    token = request_email_verification(
        users=users,
        verifications=verifications,
        email=payload.email,
    )

    if token:
        email_client = get_email_client()
        email_client.send_verification_email(
            to=payload.email,
            token=token,
        )
        print("Resent email verification token:", token)

    return None
