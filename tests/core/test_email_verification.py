import pytest
from datetime import timedelta, datetime

from sqlmodel import SQLModel, create_engine, Session

from fastauth.core.users import create_user
from fastauth.core.email_verification import (
    request_email_verification,
    confirm_email_verification,
    EmailVerificationError,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_email_verification_success(session):
    user = create_user(
        session=session,
        email="user@example.com",
        password="secret",
    )

    token = request_email_verification(
        session=session,
        email="user@example.com",
    )

    assert token is not None

    confirm_email_verification(
        session=session,
        token=token,
    )

    session.refresh(user)
    assert user.is_verified is True


def test_email_verification_single_use(session):
    user = create_user(
        session=session,
        email="user@example.com",
        password="secret",
    )

    token = request_email_verification(
        session=session,
        email="user@example.com",
    )

    confirm_email_verification(
        session=session,
        token=token,
    )

    with pytest.raises(EmailVerificationError):
        confirm_email_verification(
            session=session,
            token=token,
        )
