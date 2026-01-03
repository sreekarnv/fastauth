from typing import Any

from fastauth.adapters.base.users import UserAdapter
from fastauth.core.hashing import hash_password, verify_password
from fastauth.settings import settings


class UserAlreadyExistsError(Exception):
    """Raised when trying to create a user with an existing email."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""


class EmailNotVerifiedError(Exception):
    """Raised when email is not verified"""


def create_user(
    *,
    users: UserAdapter,
    email: str,
    password: str,
) -> Any:
    """
    Create a new user with a hashed password.

    Args:
        users: User adapter for database operations
        email: User's email address
        password: Plain text password (will be hashed)

    Returns:
        Created user object

    Raises:
        UserAlreadyExistsError: If a user with the email already exists
    """

    existing_user = users.get_by_email(email=email)

    if existing_user:
        raise UserAlreadyExistsError(f"User with email {email} already exists")

    user = users.create_user(email=email, hashed_password=hash_password(password))

    return user


def authenticate_user(
    *,
    users: UserAdapter,
    email: str,
    password: str,
) -> Any:
    """
    Authenticate a user by email and password.

    Args:
        users: User adapter for database operations
        email: User's email address
        password: Plain text password to verify

    Returns:
        Authenticated user object

    Raises:
        InvalidCredentialsError: If email doesn't exist, password is wrong, \
            or user is inactive
        EmailNotVerifiedError: If email verification is required but not completed
    """

    user = users.get_by_email(email=email)

    if not user:
        raise InvalidCredentialsError("Invalid email or password")

    if not verify_password(user.hashed_password, password):
        raise InvalidCredentialsError

    if settings.require_email_verification and not user.is_verified:
        raise EmailNotVerifiedError

    if not user.is_active:
        raise InvalidCredentialsError("User is inactive")

    return user
