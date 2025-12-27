from datetime import datetime, timedelta, UTC
from sqlmodel import Session
from fastauth.adapters.sqlalchemy.password_reset import SQLAlchemyPasswordResetAdapter
from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter


def test_create_password_reset_token(session: Session):
    user_adapter = SQLAlchemyUserAdapter(session)
    user = user_adapter.create_user(
        email="test@example.com",
        hashed_password="hash"
    )

    adapter = SQLAlchemyPasswordResetAdapter(session)
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    adapter.create(
        user_id=user.id,
        token_hash="reset_token_hash",
        expires_at=expires_at
    )

    token = adapter.get_valid(token_hash="reset_token_hash")

    assert token is not None
    assert token.user_id == user.id
    assert token.token_hash == "reset_token_hash"
    assert token.used is False
    assert token.created_at is not None


def test_get_valid_token(session: Session):
    user_adapter = SQLAlchemyUserAdapter(session)
    user = user_adapter.create_user(
        email="test@example.com",
        hashed_password="hash"
    )

    adapter = SQLAlchemyPasswordResetAdapter(session)
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    adapter.create(
        user_id=user.id,
        token_hash="valid_token",
        expires_at=expires_at
    )

    token = adapter.get_valid(token_hash="valid_token")

    assert token is not None
    assert token.token_hash == "valid_token"
    assert token.used is False


def test_get_valid_token_not_found(session: Session):
    adapter = SQLAlchemyPasswordResetAdapter(session)

    token = adapter.get_valid(token_hash="nonexistent_token")

    assert token is None


def test_get_valid_excludes_used(session: Session):
    user_adapter = SQLAlchemyUserAdapter(session)
    user = user_adapter.create_user(
        email="test@example.com",
        hashed_password="hash"
    )

    adapter = SQLAlchemyPasswordResetAdapter(session)
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    adapter.create(
        user_id=user.id,
        token_hash="used_token",
        expires_at=expires_at
    )

    adapter.mark_used(token_hash="used_token")

    token = adapter.get_valid(token_hash="used_token")

    assert token is None


def test_mark_used(session: Session):
    user_adapter = SQLAlchemyUserAdapter(session)
    user = user_adapter.create_user(
        email="test@example.com",
        hashed_password="hash"
    )

    adapter = SQLAlchemyPasswordResetAdapter(session)
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    adapter.create(
        user_id=user.id,
        token_hash="token_to_mark",
        expires_at=expires_at
    )

    token_before = adapter.get_valid(token_hash="token_to_mark")
    assert token_before is not None
    assert token_before.used is False

    adapter.mark_used(token_hash="token_to_mark")

    token_after = adapter.get_valid(token_hash="token_to_mark")
    assert token_after is None


def test_mark_used_nonexistent_token(session: Session):
    adapter = SQLAlchemyPasswordResetAdapter(session)

    adapter.mark_used(token_hash="nonexistent_token")


def test_mark_used_already_used_token(session: Session):
    user_adapter = SQLAlchemyUserAdapter(session)
    user = user_adapter.create_user(
        email="test@example.com",
        hashed_password="hash"
    )

    adapter = SQLAlchemyPasswordResetAdapter(session)
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    adapter.create(
        user_id=user.id,
        token_hash="already_used",
        expires_at=expires_at
    )

    adapter.mark_used(token_hash="already_used")
    adapter.mark_used(token_hash="already_used")
