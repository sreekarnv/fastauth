import pytest
from datetime import timedelta, datetime, UTC

from sqlmodel import SQLModel, create_engine, Session, select

from fastauth.core.password_reset import (
    request_password_reset,
    confirm_password_reset,
    PasswordResetError,
)
from fastauth.core.users import create_user
from fastauth.core.hashing import verify_password
from fastauth.db.models import PasswordResetToken


@pytest.fixture
def session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


def test_password_reset_success(session):
    user = create_user(
        session=session,
        email="user@example.com",
        password="old-password",
    )

    token = request_password_reset(
        session=session,
        email="user@example.com",
    )

    assert token is not None

    confirm_password_reset(
        session=session,
        token=token,
        new_password="new-password",
    )

    session.refresh(user)
    assert verify_password(user.hashed_password, "new-password") is True


def test_password_reset_token_single_use(session):
    user = create_user(
        session=session,
        email="user@example.com",
        password="old-password",
    )

    token = request_password_reset(
        session=session,
        email="user@example.com",
    )

    confirm_password_reset(
        session=session,
        token=token,
        new_password="new-password",
    )

    with pytest.raises(PasswordResetError):
        confirm_password_reset(
            session=session,
            token=token,
            new_password="another-password",
        )


def test_password_reset_expired_token(session):
    user = create_user(
        session=session,
        email="user@example.com",
        password="old-password",
    )

    token = request_password_reset(
        session=session,
        email="user@example.com",
        expires_in_minutes=1,
    )

    reset_token = session.exec(
        select(PasswordResetToken)
    ).first()

    reset_token.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    session.add(reset_token)
    session.commit()

    with pytest.raises(PasswordResetError):
        confirm_password_reset(
            session=session,
            token=token,
            new_password="new-password",
        )


def test_password_reset_nonexistent_email_is_silent(session):
    token = request_password_reset(
        session=session,
        email="missing@example.com",
    )

    assert token is None
