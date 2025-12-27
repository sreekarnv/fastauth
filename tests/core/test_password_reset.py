from datetime import UTC, datetime, timedelta

import pytest

from fastauth.core.hashing import verify_password
from fastauth.core.password_reset import (
    PasswordResetError,
    confirm_password_reset,
    request_password_reset,
)
from fastauth.core.users import create_user
from tests.fakes.password_reset import FakePasswordResetAdapter
from tests.fakes.users import FakeUserAdapter


@pytest.fixture
def users():
    return FakeUserAdapter()


@pytest.fixture
def resets():
    return FakePasswordResetAdapter()


def test_password_reset_success(users, resets):
    user = create_user(
        users=users,
        email="user@example.com",
        password="old-password",
    )

    token = request_password_reset(
        users=users,
        resets=resets,
        email="user@example.com",
    )

    assert token is not None

    confirm_password_reset(
        users=users,
        resets=resets,
        token=token,
        new_password="new-password",
    )

    updated_user = users.get_by_id(user.id)
    assert verify_password(updated_user.hashed_password, "new-password")


def test_password_reset_token_single_use(users, resets):
    create_user(
        users=users,
        email="user@example.com",
        password="old-password",
    )

    token = request_password_reset(
        users=users,
        resets=resets,
        email="user@example.com",
    )

    confirm_password_reset(
        users=users,
        resets=resets,
        token=token,
        new_password="new-password",
    )

    with pytest.raises(PasswordResetError):
        confirm_password_reset(
            users=users,
            resets=resets,
            token=token,
            new_password="another-password",
        )


def test_password_reset_expired_token(users, resets):
    create_user(
        users=users,
        email="user@example.com",
        password="old-password",
    )

    token = request_password_reset(
        users=users,
        resets=resets,
        email="user@example.com",
        expires_in_minutes=1,
    )

    record = next(iter(resets.tokens.values()))
    record.expires_at = datetime.now(UTC) - timedelta(minutes=1)

    with pytest.raises(PasswordResetError):
        confirm_password_reset(
            users=users,
            resets=resets,
            token=token,
            new_password="new-password",
        )


def test_password_reset_nonexistent_email_is_silent(users, resets):
    token = request_password_reset(
        users=users,
        resets=resets,
        email="missing@example.com",
    )

    assert token is None
