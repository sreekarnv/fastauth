import pytest

from fastauth.core.users import (
    EmailNotVerifiedError,
    authenticate_user,
    create_user,
)
from tests.fakes.users import FakeUserAdapter


def test_login_fails_if_email_not_verified():
    users = FakeUserAdapter()

    create_user(
        users=users,
        email="user@example.com",
        password="secret",
    )

    with pytest.raises(EmailNotVerifiedError):
        authenticate_user(
            users=users,
            email="user@example.com",
            password="secret",
        )
