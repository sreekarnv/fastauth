from sqlmodel import Session, select
from fastauth.db.models import User
from fastauth.core.hashing import hash_password


class UserAlreadyExistsError(Exception):
    """Raised when trying to create a user with an existing email."""


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
