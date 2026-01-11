from datetime import UTC, datetime, timedelta

import pytest

from fastauth.core.email_verification import (
    EmailVerificationError,
    confirm_email_verification,
    request_email_verification,
)
from fastauth.core.users import create_user
from tests.fakes.email_verification import FakeEmailVerificationAdapter
from tests.fakes.users import FakeUserAdapter


@pytest.fixture
def users():
    return FakeUserAdapter()


@pytest.fixture
def verifications():
    return FakeEmailVerificationAdapter()


def test_email_verification_success(users, verifications):
    user = create_user(
        users=users,
        email="user@example.com",
        password="secret",
    )

    token = request_email_verification(
        users=users,
        verifications=verifications,
        email="user@example.com",
    )

    assert token is not None

    confirm_email_verification(
        users=users,
        verifications=verifications,
        token=token,
    )

    updated_user = users.get_by_id(user.id)
    assert updated_user.is_verified is True


def test_email_verification_single_use(users, verifications):
    create_user(
        users=users,
        email="user@example.com",
        password="secret",
    )

    token = request_email_verification(
        users=users,
        verifications=verifications,
        email="user@example.com",
    )

    confirm_email_verification(
        users=users,
        verifications=verifications,
        token=token,
    )

    with pytest.raises(EmailVerificationError):
        confirm_email_verification(
            users=users,
            verifications=verifications,
            token=token,
        )


def test_email_verification_expired_token(users, verifications):
    """Test that expired verification tokens are rejected."""
    create_user(
        users=users,
        email="user@example.com",
        password="secret",
    )

    token = request_email_verification(
        users=users,
        verifications=verifications,
        email="user@example.com",
    )

    record = next(iter(verifications.tokens.values()))
    record.expires_at = datetime.now(UTC) - timedelta(minutes=1)

    with pytest.raises(EmailVerificationError, match="Expired verification token"):
        confirm_email_verification(
            users=users,
            verifications=verifications,
            token=token,
        )
