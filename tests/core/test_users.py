import pytest

from fastauth.core.users import create_user, UserAlreadyExistsError
from tests.fakes.users import FakeUserAdapter


@pytest.fixture
def users():
    return FakeUserAdapter()


def test_create_user_success(users):
    user = create_user(
        users=users,
        email="test@example.com",
        password="super-secret",
    )

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.hashed_password != "super-secret"


def test_create_user_duplicate_email(users):
    create_user(
        users=users,
        email="test@example.com",
        password="super-secret",
    )

    with pytest.raises(UserAlreadyExistsError):
        create_user(
            users=users,
            email="test@example.com",
            password="another-password",
        )
