import pytest

from fastauth.core.users import create_user
from fastauth.core.email_verification import (
    request_email_verification,
    confirm_email_verification,
    EmailVerificationError,
)

from tests.fakes.users import FakeUserAdapter
from tests.fakes.email_verification import FakeEmailVerificationAdapter


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
