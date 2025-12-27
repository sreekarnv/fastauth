import uuid
from datetime import datetime, timedelta, UTC
from sqlmodel import Session
from fastauth.adapters.sqlalchemy.refresh_tokens import SQLAlchemyRefreshTokenAdapter
from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter


def test_create_refresh_token(session: Session):
    user_adapter = SQLAlchemyUserAdapter(session)
    user = user_adapter.create_user(
        email="test@example.com",
        hashed_password="hash"
    )

    adapter = SQLAlchemyRefreshTokenAdapter(session)
    expires_at = datetime.now(UTC) + timedelta(days=7)

    token = adapter.create(
        user_id=user.id,
        token_hash="token_hash_123",
        expires_at=expires_at
    )

    assert token.id is not None
    assert token.user_id == user.id
    assert token.token_hash == "token_hash_123"
    assert token.expires_at == expires_at
    assert token.revoked is False
    assert token.created_at is not None


def test_get_active_token(session: Session):
    user_adapter = SQLAlchemyUserAdapter(session)
    user = user_adapter.create_user(
        email="test@example.com",
        hashed_password="hash"
    )

    adapter = SQLAlchemyRefreshTokenAdapter(session)
    expires_at = datetime.now(UTC) + timedelta(days=7)

    created_token = adapter.create(
        user_id=user.id,
        token_hash="token_hash_123",
        expires_at=expires_at
    )

    retrieved_token = adapter.get_active(token_hash="token_hash_123")

    assert retrieved_token is not None
    assert retrieved_token.id == created_token.id
    assert retrieved_token.token_hash == "token_hash_123"
    assert retrieved_token.revoked is False


def test_get_active_token_not_found(session: Session):
    adapter = SQLAlchemyRefreshTokenAdapter(session)

    token = adapter.get_active(token_hash="nonexistent_hash")

    assert token is None


def test_get_active_excludes_revoked(session: Session):
    user_adapter = SQLAlchemyUserAdapter(session)
    user = user_adapter.create_user(
        email="test@example.com",
        hashed_password="hash"
    )

    adapter = SQLAlchemyRefreshTokenAdapter(session)
    expires_at = datetime.now(UTC) + timedelta(days=7)

    adapter.create(
        user_id=user.id,
        token_hash="revoked_token",
        expires_at=expires_at
    )

    adapter.revoke(token_hash="revoked_token")

    retrieved_token = adapter.get_active(token_hash="revoked_token")

    assert retrieved_token is None


def test_revoke_token(session: Session):
    user_adapter = SQLAlchemyUserAdapter(session)
    user = user_adapter.create_user(
        email="test@example.com",
        hashed_password="hash"
    )

    adapter = SQLAlchemyRefreshTokenAdapter(session)
    expires_at = datetime.now(UTC) + timedelta(days=7)

    token = adapter.create(
        user_id=user.id,
        token_hash="token_to_revoke",
        expires_at=expires_at
    )

    assert token.revoked is False

    adapter.revoke(token_hash="token_to_revoke")

    revoked_token = adapter.get_active(token_hash="token_to_revoke")
    assert revoked_token is None


def test_revoke_nonexistent_token(session: Session):
    adapter = SQLAlchemyRefreshTokenAdapter(session)

    adapter.revoke(token_hash="nonexistent_token")


def test_revoke_already_revoked_token(session: Session):
    user_adapter = SQLAlchemyUserAdapter(session)
    user = user_adapter.create_user(
        email="test@example.com",
        hashed_password="hash"
    )

    adapter = SQLAlchemyRefreshTokenAdapter(session)
    expires_at = datetime.now(UTC) + timedelta(days=7)

    adapter.create(
        user_id=user.id,
        token_hash="already_revoked",
        expires_at=expires_at
    )

    adapter.revoke(token_hash="already_revoked")
    adapter.revoke(token_hash="already_revoked")
