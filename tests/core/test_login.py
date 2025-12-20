import pytest
from sqlmodel import SQLModel, create_engine, Session

from fastauth.core.users import (
    create_user,
    authenticate_user,
    InvalidCredentialsError,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


def test_authenticate_user_success(session):
    create_user(
        session=session,
        email="user@example.com",
        password="correct-password",
    )

    user = authenticate_user(
        session=session,
        email="user@example.com",
        password="correct-password",
    )

    assert user.email == "user@example.com"


def test_authenticate_user_wrong_password(session):
    create_user(
        session=session,
        email="user@example.com",
        password="correct-password",
    )

    with pytest.raises(InvalidCredentialsError):
        authenticate_user(
            session=session,
            email="user@example.com",
            password="wrong-password",
        )


def test_authenticate_user_nonexistent_email(session):
    with pytest.raises(InvalidCredentialsError):
        authenticate_user(
            session=session,
            email="missing@example.com",
            password="whatever",
        )
