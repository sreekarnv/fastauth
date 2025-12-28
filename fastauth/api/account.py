from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from fastauth.adapters.sqlalchemy.email_change import SQLAlchemyEmailChangeAdapter
from fastauth.adapters.sqlalchemy.models import User
from fastauth.adapters.sqlalchemy.sessions import SQLAlchemySessionAdapter
from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter
from fastauth.api.dependencies import get_current_user, get_session
from fastauth.api.schemas import (
    ChangePasswordRequest,
    ConfirmEmailChangeRequest,
    DeleteAccountRequest,
    RequestEmailChangeRequest,
)
from fastauth.core.account import (
    EmailAlreadyExistsError,
    EmailChangeError,
    InvalidPasswordError,
    UserNotFoundError,
    change_password,
    confirm_email_change,
    delete_account,
    request_email_change,
)

router = APIRouter(prefix="/account", tags=["account"])


class MessageResponse(BaseModel):
    message: str


@router.post("/change-password", response_model=MessageResponse)
def change_user_password(
    request: ChangePasswordRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Change the current user's password.

    Requires the current password for verification.
    Invalidates all other sessions after password change for security.
    """
    users_adapter = SQLAlchemyUserAdapter(session=session)
    sessions_adapter = SQLAlchemySessionAdapter(session=session)

    try:
        change_password(
            users=users_adapter,
            sessions=sessions_adapter,
            user_id=current_user.id,
            current_password=request.current_password,
            new_password=request.new_password,
            current_session_id=None,
        )
    except InvalidPasswordError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return MessageResponse(message="Password changed successfully")


@router.delete("/delete", response_model=MessageResponse)
def delete_user_account(
    request: DeleteAccountRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Delete the current user's account.

    Requires password for verification.
    Supports both soft delete (default) and hard delete.
    Soft delete sets deleted_at timestamp and deactivates the account.
    Hard delete permanently removes the user from the database.
    """
    users_adapter = SQLAlchemyUserAdapter(session=session)
    sessions_adapter = SQLAlchemySessionAdapter(session=session)

    try:
        delete_account(
            users=users_adapter,
            sessions=sessions_adapter,
            user_id=current_user.id,
            password=request.password,
            hard_delete=request.hard_delete,
        )
    except InvalidPasswordError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect",
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    delete_type = "permanently deleted" if request.hard_delete else "deactivated"
    return MessageResponse(message=f"Account {delete_type} successfully")


class EmailChangeTokenResponse(BaseModel):
    message: str
    token: str


@router.post("/request-email-change", response_model=EmailChangeTokenResponse)
def request_user_email_change(
    request: RequestEmailChangeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Request an email change for the current user.

    Generates a verification token that must be confirmed to complete the email change.
    The token expires in 60 minutes by default.
    """
    users_adapter = SQLAlchemyUserAdapter(session=session)
    email_changes_adapter = SQLAlchemyEmailChangeAdapter(session=session)

    try:
        token = request_email_change(
            users=users_adapter,
            email_changes=email_changes_adapter,
            user_id=current_user.id,
            new_email=request.new_email,
            expires_in_minutes=60,
        )
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return EmailChangeTokenResponse(
        message="Email change requested. \
            Please verify the token to complete the change.",
        token=token,
    )


@router.post("/confirm-email-change", response_model=MessageResponse)
def confirm_user_email_change(
    request: ConfirmEmailChangeRequest,
    session: Session = Depends(get_session),
):
    """
    Confirm an email change with a verification token.

    Completes the email change process started with request-email-change.
    """
    users_adapter = SQLAlchemyUserAdapter(session=session)
    email_changes_adapter = SQLAlchemyEmailChangeAdapter(session=session)

    try:
        confirm_email_change(
            users=users_adapter,
            email_changes=email_changes_adapter,
            token=request.token,
        )
    except EmailChangeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return MessageResponse(message="Email changed successfully")
