import pytest
from sqlmodel import SQLModel, create_engine, Session

from fastauth.db.models import User
from fastauth.core.users import create_user, UserAlreadyExistsError


@pytest.fixture
def session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


def test_create_user_success(session):
    user = create_user(
        session=session,
        email="test@example.com",
        password="super-secret",
    )

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.hashed_password != "super-secret"


def test_create_user_duplicate_email(session):
    create_user(
        session=session,
        email="test@example.com",
        password="super-secret",
    )

    with pytest.raises(UserAlreadyExistsError):
        create_user(
            session=session,
            email="test@example.com",
            password="another-password",
        )
