import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlmodel import Session

from fastauth.adapters.sqlalchemy.sessions import SQLAlchemySessionAdapter
from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter


@pytest.fixture
def user(session: Session):
    """Create a test user."""
    adapter = SQLAlchemyUserAdapter(session)
    return adapter.create_user(
        email="test@example.com",
        hashed_password="hashed_password_123",
    )


def test_create_session(session: Session, user):
    adapter = SQLAlchemySessionAdapter(session)

    session_obj = adapter.create_session(
        user_id=user.id,
        device="iPhone 13",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
    )

    assert session_obj.id is not None
    assert session_obj.user_id == user.id
    assert session_obj.device == "iPhone 13"
    assert session_obj.ip_address == "192.168.1.1"
    assert session_obj.user_agent == "Mozilla/5.0"
    assert session_obj.last_active is not None
    assert session_obj.created_at is not None


def test_create_session_minimal(session: Session, user):
    adapter = SQLAlchemySessionAdapter(session)

    session_obj = adapter.create_session(user_id=user.id)

    assert session_obj.id is not None
    assert session_obj.user_id == user.id
    assert session_obj.device is None
    assert session_obj.ip_address is None
    assert session_obj.user_agent is None


def test_get_session_by_id(session: Session, user):
    adapter = SQLAlchemySessionAdapter(session)

    created_session = adapter.create_session(user_id=user.id)

    retrieved_session = adapter.get_session_by_id(created_session.id)

    assert retrieved_session is not None
    assert retrieved_session.id == created_session.id
    assert retrieved_session.user_id == user.id


def test_get_session_by_id_not_found(session: Session):
    adapter = SQLAlchemySessionAdapter(session)

    session_obj = adapter.get_session_by_id(uuid.uuid4())

    assert session_obj is None


def test_get_user_sessions(session: Session, user):
    adapter = SQLAlchemySessionAdapter(session)
    user_adapter = SQLAlchemyUserAdapter(session)

    session1 = adapter.create_session(user_id=user.id, device="iPhone")
    session2 = adapter.create_session(user_id=user.id, device="MacBook")

    another_user = user_adapter.create_user(
        email="another@example.com",
        hashed_password="hashed_password_456",
    )
    adapter.create_session(user_id=another_user.id, device="Android")

    user_sessions = adapter.get_user_sessions(user.id)

    assert len(user_sessions) == 2
    assert session1.id in [s.id for s in user_sessions]
    assert session2.id in [s.id for s in user_sessions]


def test_get_user_sessions_empty(session: Session, user):
    adapter = SQLAlchemySessionAdapter(session)

    user_sessions = adapter.get_user_sessions(user.id)

    assert len(user_sessions) == 0


def test_delete_session(session: Session, user):
    adapter = SQLAlchemySessionAdapter(session)

    session_obj = adapter.create_session(user_id=user.id)

    adapter.delete_session(session_obj.id)

    retrieved_session = adapter.get_session_by_id(session_obj.id)
    assert retrieved_session is None


def test_delete_session_nonexistent(session: Session):
    adapter = SQLAlchemySessionAdapter(session)

    adapter.delete_session(uuid.uuid4())


def test_delete_user_sessions(session: Session, user):
    adapter = SQLAlchemySessionAdapter(session)
    user_adapter = SQLAlchemyUserAdapter(session)

    adapter.create_session(user_id=user.id, device="iPhone")
    adapter.create_session(user_id=user.id, device="MacBook")
    adapter.create_session(user_id=user.id, device="iPad")

    another_user = user_adapter.create_user(
        email="another@example.com",
        hashed_password="hashed_password_456",
    )
    adapter.create_session(user_id=another_user.id, device="Android")

    adapter.delete_user_sessions(user_id=user.id)

    user_sessions = adapter.get_user_sessions(user.id)
    other_user_sessions = adapter.get_user_sessions(another_user.id)

    assert len(user_sessions) == 0
    assert len(other_user_sessions) == 1


def test_delete_user_sessions_except_current(session: Session, user):
    adapter = SQLAlchemySessionAdapter(session)

    session2 = adapter.create_session(user_id=user.id, device="MacBook")

    adapter.delete_user_sessions(user_id=user.id, except_session_id=session2.id)

    user_sessions = adapter.get_user_sessions(user.id)

    assert len(user_sessions) == 1
    assert user_sessions[0].id == session2.id


def test_update_last_active(session: Session, user):
    adapter = SQLAlchemySessionAdapter(session)

    session_obj = adapter.create_session(user_id=user.id)
    original_last_active = session_obj.last_active

    import time

    time.sleep(0.01)

    adapter.update_last_active(session_obj.id)

    session.refresh(session_obj)

    assert session_obj.last_active > original_last_active


def test_update_last_active_nonexistent(session: Session):
    adapter = SQLAlchemySessionAdapter(session)
    adapter.update_last_active(uuid.uuid4())


def test_cleanup_inactive_sessions(session: Session, user):
    from fastauth.adapters.sqlalchemy.models import Session as SessionModel

    adapter = SQLAlchemySessionAdapter(session)

    active_session = adapter.create_session(user_id=user.id)

    old_session = SessionModel(
        user_id=user.id,
        last_active=datetime.now(UTC) - timedelta(days=31),
    )
    session.add(old_session)
    session.commit()

    adapter.cleanup_inactive_sessions(inactive_days=30)

    user_sessions = adapter.get_user_sessions(user.id)

    assert len(user_sessions) == 1
    assert user_sessions[0].id == active_session.id


def test_cleanup_inactive_sessions_custom_days(session: Session, user):
    from fastauth.adapters.sqlalchemy.models import Session as SessionModel

    adapter = SQLAlchemySessionAdapter(session)

    active_session = adapter.create_session(user_id=user.id)

    old_session = SessionModel(
        user_id=user.id,
        last_active=datetime.now(UTC) - timedelta(days=8),
    )
    session.add(old_session)
    session.commit()

    adapter.cleanup_inactive_sessions(inactive_days=7)

    user_sessions = adapter.get_user_sessions(user.id)

    assert len(user_sessions) == 1
    assert user_sessions[0].id == active_session.id
