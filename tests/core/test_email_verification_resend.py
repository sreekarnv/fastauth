from sqlmodel import SQLModel, create_engine, Session

from fastauth.core.users import create_user
from fastauth.core.email_verification import request_email_verification


def test_resend_verification_returns_token_for_unverified_user():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        create_user(
            session=session,
            email="user@example.com",
            password="secret",
        )

        token = request_email_verification(
            session=session,
            email="user@example.com",
        )

        assert token is not None
