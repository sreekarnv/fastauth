from fastauth.core.users import create_user
from fastauth.core.email_verification import request_email_verification

from tests.fakes.users import FakeUserAdapter
from tests.fakes.email_verification import FakeEmailVerificationAdapter


def test_resend_verification_returns_token_for_unverified_user():
    users = FakeUserAdapter()
    verifications = FakeEmailVerificationAdapter()

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

    assert token is not None
