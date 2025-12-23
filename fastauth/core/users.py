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
):
    """
    Create a new user with a hashed password.

    Raises:
        UserAlreadyExistsError: if a user with the same email already exists
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
):
    """
    Authenticate a user by email and password.

    Raises:
        InvalidCredentialsError: if email does not exist or password is wrong
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
