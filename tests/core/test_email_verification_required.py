import pytest
from sqlmodel import SQLModel, create_engine, Session

from fastauth.core.users import (
    create_user,
    authenticate_user,
    EmailNotVerifiedError,
)


def test_login_fails_if_email_not_verified():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        user = create_user(
            session=session,
            email="user@example.com",
            password="secret",
        )

        with pytest.raises(EmailNotVerifiedError):
            authenticate_user(
                session=session,
                email="user@example.com",
                password="secret",
            )
