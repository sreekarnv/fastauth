from sqlmodel import Session, select
from fastauth.db.models import User
from fastauth.core.hashing import hash_password, verify_password


class UserAlreadyExistsError(Exception):
    """Raised when trying to create a user with an existing email."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""


def create_user(
    *,
    session: Session,
    email: str,
    password: str,
    is_superuser: bool = False,
) -> User:
    """
    Create a new user with a hashed password.

    Raises:
        UserAlreadyExistsError: if a user with the same email already exists
    """

    statement = select(User).where(User.email == email)
    existing_user = session.exec(statement).first()

    if existing_user:
        raise UserAlreadyExistsError(f"User with email {email} already exists")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        is_superuser=is_superuser,
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def authenticate_user(
    *,
    session: Session,
    email: str,
    password: str,
) -> User:
    """
    Authenticate a user by email and password.

    Raises:
        InvalidCredentialsError: if email does not exist or password is wrong
    """

    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()

    if not user:
        # Do not reveal whether email exists
        raise InvalidCredentialsError("Invalid email or password")

    if not verify_password(user.hashed_password, password):
        raise InvalidCredentialsError("Invalid email or password")

    if not user.is_active:
        raise InvalidCredentialsError("User is inactive")

    return user
