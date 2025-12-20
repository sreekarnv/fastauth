from sqlmodel import SQLModel, create_engine, Session, select

from fastauth.core.refresh_tokens import (
    create_refresh_token,
    revoke_refresh_token,
)
from fastauth.core.users import create_user
from fastauth.db.models import RefreshToken


def test_logout_revokes_refresh_token():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        user = create_user(
            session=session,
            email="test@example.com",
            password="secret",
        )

        raw_token = create_refresh_token(
            session=session,
            user_id=user.id,
        )

        revoke_refresh_token(
            session=session,
            token=raw_token,
        )

        tokens = session.exec(select(RefreshToken)).all()

        assert len(tokens) == 1
        assert tokens[0].revoked is True
