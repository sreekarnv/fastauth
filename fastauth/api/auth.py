from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from fastauth.api.schemas import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest
from fastauth.core.users import (
    create_user,
    authenticate_user,
    UserAlreadyExistsError,
    InvalidCredentialsError,
)
from fastauth.core.refresh_tokens import (
    create_refresh_token,
    rotate_refresh_token,
    RefreshTokenError,
)
from fastauth.db.session import get_session
from fastauth.security.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(
    payload: RegisterRequest,
    session: Session = Depends(get_session),
):
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

    token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(
        session=session,
        user_id=user.id,
    )

    return TokenResponse(access_token=token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    session: Session = Depends(get_session),
):
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

    token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(
        session=session,
        user_id=user.id,
    )

    return TokenResponse(access_token=token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshRequest,
    session: Session = Depends(get_session),
):
    try:
        new_refresh, user_id = rotate_refresh_token(
            session=session,
            token=payload.refresh_token,
        )
    except RefreshTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    access_token = create_access_token(subject=str(user_id))

    return {
        "access_token": access_token,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }
