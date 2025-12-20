from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from fastauth.api.schemas import LoginRequest, RegisterRequest, TokenResponse
from fastauth.core.users import (
    create_user,
    authenticate_user,
    UserAlreadyExistsError,
    InvalidCredentialsError,
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

    return TokenResponse(access_token=token)


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

    return TokenResponse(access_token=token)
