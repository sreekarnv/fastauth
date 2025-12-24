import pytest

from fastauth.core.users import (
    EmailNotVerifiedError,
    create_user,
    authenticate_user,
    InvalidCredentialsError,
)

from tests.fakes.users import FakeUserAdapter


@pytest.fixture
def users():
    return FakeUserAdapter()


def test_authenticate_user_success(users):
    user = create_user(
        users=users,
        email="user@example.com",
        password="secret",
    )

    # Mark user as verified
    users.mark_verified(user.id)

    authenticated = authenticate_user(
        users=users,
        email="user@example.com",
        password="secret",
    )

    assert authenticated.id == user.id


def test_authenticate_user_wrong_password(users):
    create_user(
        users=users,
        email="user@example.com",
        password="correct-password",
    )

    users.mark_verified(
        users.get_by_email("user@example.com").id
    )

    with pytest.raises(InvalidCredentialsError):
        authenticate_user(
            users=users,
            email="user@example.com",
            password="wrong-password",
        )


def test_authenticate_user_nonexistent_email(users):
    with pytest.raises(InvalidCredentialsError):
        authenticate_user(
            users=users,
            email="missing@example.com",
            password="whatever",
        )


def test_authenticate_user_fails_if_not_verified(users):
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
