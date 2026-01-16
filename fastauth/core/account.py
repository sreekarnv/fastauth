"""
Account management core logic.

Provides business logic for account operations including password change,
email change, and account deletion.
"""

import uuid

from fastauth.adapters.base.email_change import EmailChangeAdapter
from fastauth.adapters.base.sessions import SessionAdapter
from fastauth.adapters.base.users import UserAdapter
from fastauth.core.hashing import hash_password, verify_password
from fastauth.security.tokens import (
    generate_secure_token,
    hash_token,
    utc_from_now,
    validate_token_expiration,
)
from fastauth.settings import settings


class InvalidPasswordError(Exception):
    """Raised when the current password is incorrect."""


class UserNotFoundError(Exception):
    """Raised when the user is not found."""


class EmailChangeError(Exception):
    """Raised when there's an error with email change."""


class EmailAlreadyExistsError(Exception):
    """Raised when the new email already exists."""


def change_password(
    *,
    users: UserAdapter,
    sessions: SessionAdapter,
    user_id: uuid.UUID,
    current_password: str,
    new_password: str,
    current_session_id: uuid.UUID | None = None,
) -> None:
    """
    Change a user's password.

    Args:
        users: User adapter for database operations
        sessions: Session adapter for database operations
        user_id: ID of the user changing their password
        current_password: Current password for verification
        new_password: New password to set
        current_session_id: Optional session ID to preserve during logout

    Raises:
        UserNotFoundError: If the user doesn't exist
        InvalidPasswordError: If the current password is incorrect
    """
    user = users.get_by_id(user_id)
    if not user:
        raise UserNotFoundError("User not found")

    if not verify_password(user.hashed_password, current_password):
        raise InvalidPasswordError("Current password is incorrect")

    hashed_new_password = hash_password(new_password)
    users.set_password(user_id=user_id, hashed_password=hashed_new_password)

    sessions.delete_user_sessions(
        user_id=user_id,
        except_session_id=current_session_id,
    )


def request_email_change(
    *,
    users: UserAdapter,
    email_changes: EmailChangeAdapter,
    user_id: uuid.UUID,
    new_email: str,
    expires_in_minutes: int | None = None,
) -> str | None:
    """
    Request an email change for a user.

    Args:
        users: User adapter for database operations
        email_changes: Email change adapter for database operations
        user_id: ID of the user requesting email change
        new_email: New email address
        expires_in_minutes: Token expiration time in minutes \
            (defaults to settings value)

    Returns:
        Verification token if successful, None if user not found

    Raises:
        EmailAlreadyExistsError: If the new email already exists
    """
    user = users.get_by_id(user_id)
    if not user:
        return None

    existing_user = users.get_by_email(new_email)
    if existing_user:
        raise EmailAlreadyExistsError(f"Email {new_email} already exists")

    if expires_in_minutes is None:
        expires_in_minutes = settings.email_change_token_expiry_minutes

    raw_token = generate_secure_token(48)
    token_hash = hash_token(raw_token)

    expires_at = utc_from_now(minutes=expires_in_minutes)

    email_changes.create(
        user_id=user_id,
        new_email=new_email,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    return raw_token


def confirm_email_change(
    *,
    users: UserAdapter,
    email_changes: EmailChangeAdapter,
    token: str,
) -> None:
    """
    Confirm an email change with a verification token.

    Args:
        users: User adapter for database operations
        email_changes: Email change adapter for database operations
        token: Verification token

    Raises:
        EmailChangeError: If token is invalid or expired
        EmailAlreadyExistsError: If the new email already exists
    """
    token_hash = hash_token(token)

    record = email_changes.get_valid(token_hash=token_hash)
    if not record:
        raise EmailChangeError("Invalid or expired email change token")

    try:
        validate_token_expiration(record.expires_at, "Expired email change token")
    except ValueError as e:
        raise EmailChangeError(str(e))

    existing_user = users.get_by_email(record.new_email)
    if existing_user:
        raise EmailAlreadyExistsError(
            f"Email {record.new_email} is no longer available"
        )

    users.update_email(user_id=record.user_id, new_email=record.new_email)
    email_changes.mark_used(token_hash=token_hash)


def delete_account(
    *,
    users: UserAdapter,
    sessions: SessionAdapter,
    user_id: uuid.UUID,
    password: str,
    hard_delete: bool = False,
) -> None:
    """
    Delete a user account (soft or hard delete).

    Args:
        users: User adapter for database operations
        sessions: Session adapter for database operations
        user_id: ID of the user to delete
        password: Password for verification
        hard_delete: If True, permanently delete the user; if False, soft delete

    Raises:
        UserNotFoundError: If the user doesn't exist
        InvalidPasswordError: If the password is incorrect
    """
    user = users.get_by_id(user_id)
    if not user:
        raise UserNotFoundError("User not found")

    if not verify_password(user.hashed_password, password):
        raise InvalidPasswordError("Password is incorrect")

    sessions.delete_user_sessions(user_id=user_id)

    if hard_delete:
        users.hard_delete_user(user_id=user_id)
    else:
        users.soft_delete_user(user_id=user_id)
