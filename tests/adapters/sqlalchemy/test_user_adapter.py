import pytest
from sqlmodel import Session

from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter


def test_create_user(session: Session):
    adapter = SQLAlchemyUserAdapter(session)

    user = adapter.create_user(
        email="test@example.com", hashed_password="hashed_password_123"
    )

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.hashed_password == "hashed_password_123"
    assert user.is_active is True
    assert user.is_verified is False
    assert user.created_at is not None


def test_get_by_email(session: Session):
    adapter = SQLAlchemyUserAdapter(session)

    created_user = adapter.create_user(
        email="test@example.com", hashed_password="hashed_password_123"
    )

    retrieved_user = adapter.get_by_email("test@example.com")

    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == "test@example.com"


def test_get_by_email_not_found(session: Session):
    adapter = SQLAlchemyUserAdapter(session)

    user = adapter.get_by_email("nonexistent@example.com")

    assert user is None


def test_get_by_id(session: Session):
    adapter = SQLAlchemyUserAdapter(session)

    created_user = adapter.create_user(
        email="test@example.com", hashed_password="hashed_password_123"
    )

    retrieved_user = adapter.get_by_id(created_user.id)

    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == "test@example.com"


def test_get_by_id_not_found(session: Session):
    import uuid

    adapter = SQLAlchemyUserAdapter(session)

    user = adapter.get_by_id(uuid.uuid4())

    assert user is None


def test_mark_verified(session: Session):
    adapter = SQLAlchemyUserAdapter(session)

    user = adapter.create_user(
        email="test@example.com", hashed_password="hashed_password_123"
    )

    assert user.is_verified is False

    adapter.mark_verified(user.id)

    verified_user = adapter.get_by_id(user.id)
    assert verified_user.is_verified is True


def test_mark_verified_nonexistent_user(session: Session):
    import uuid

    adapter = SQLAlchemyUserAdapter(session)

    adapter.mark_verified(uuid.uuid4())


def test_set_password(session: Session):
    adapter = SQLAlchemyUserAdapter(session)

    user = adapter.create_user(email="test@example.com", hashed_password="old_hash")

    adapter.set_password(user_id=user.id, hashed_password="new_hash")

    updated_user = adapter.get_by_id(user.id)
    assert updated_user.hashed_password == "new_hash"


def test_set_password_nonexistent_user(session: Session):
    import uuid

    adapter = SQLAlchemyUserAdapter(session)

    adapter.set_password(user_id=uuid.uuid4(), hashed_password="new_hash")


def test_unique_email_constraint(session: Session):
    from sqlalchemy.exc import IntegrityError

    adapter = SQLAlchemyUserAdapter(session)

    adapter.create_user(email="test@example.com", hashed_password="hash1")

    with pytest.raises(IntegrityError):
        adapter.create_user(email="test@example.com", hashed_password="hash2")
