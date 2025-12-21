import pytest
from sqlmodel import SQLModel, create_engine, Session

from fastauth.core.users import (
    EmailNotVerifiedError,
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


def test_authenticate_user_success():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        user = create_user(
            session=session,
            email="user@example.com",
            password="secret",
        )

        user.is_verified = True
        session.add(user)
        session.commit()

        authenticated = authenticate_user(
            session=session,
            email="user@example.com",
            password="secret",
        )

        assert authenticated.id == user.id


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


def test_authenticate_user_fails_if_not_verified():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        create_user(
            session=session,
            email="user@example.com",
            password="secret",
        )

        with pytest.raises(EmailNotVerifiedError):
            authenticate_user(
                session=session,
                email="user@example.com",
                password="secret",
            )
