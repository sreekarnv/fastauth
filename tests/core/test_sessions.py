import uuid
from datetime import UTC, datetime, timedelta

import pytest

from fastauth.core.sessions import (
    SessionNotFoundError,
    cleanup_inactive_sessions,
    create_session,
    delete_all_user_sessions,
    delete_session,
    get_user_sessions,
    update_session_activity,
)
from fastauth.core.users import create_user
from tests.fakes.sessions import FakeSessionAdapter
from tests.fakes.users import FakeUserAdapter


@pytest.fixture
def users():
    return FakeUserAdapter()


@pytest.fixture
def sessions():
    return FakeSessionAdapter()


@pytest.fixture
def test_user(users):
    return create_user(
        users=users,
        email="test@example.com",
        password="password123",
    )


def test_create_session_success(sessions, users, test_user):
    session = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
        device="iPhone 13",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
    )

    assert session.id is not None
    assert session.user_id == test_user.id
    assert session.device == "iPhone 13"
    assert session.ip_address == "192.168.1.1"
    assert session.user_agent == "Mozilla/5.0"
    assert session.last_active is not None
    assert session.created_at is not None


def test_create_session_updates_last_login(sessions, users, test_user):
    assert test_user.last_login is None

    create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
    )

    assert test_user.last_login is not None


def test_get_user_sessions(sessions, users, test_user):
    session1 = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
        device="iPhone 13",
    )
    session2 = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
        device="MacBook Pro",
    )

    another_user = create_user(
        users=users,
        email="another@example.com",
        password="password123",
    )
    create_session(
        sessions=sessions,
        users=users,
        user_id=another_user.id,
    )

    user_sessions = get_user_sessions(
        sessions=sessions,
        user_id=test_user.id,
    )

    assert len(user_sessions) == 2
    assert session1.id in [s.id for s in user_sessions]
    assert session2.id in [s.id for s in user_sessions]


def test_delete_session_success(sessions, users, test_user):
    session = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
    )

    delete_session(
        sessions=sessions,
        session_id=session.id,
        user_id=test_user.id,
    )

    user_sessions = get_user_sessions(
        sessions=sessions,
        user_id=test_user.id,
    )

    assert len(user_sessions) == 0


def test_delete_session_not_found(sessions, users, test_user):
    non_existent_id = uuid.uuid4()

    with pytest.raises(SessionNotFoundError):
        delete_session(
            sessions=sessions,
            session_id=non_existent_id,
            user_id=test_user.id,
        )


def test_delete_session_wrong_user(sessions, users, test_user):
    session = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
    )

    another_user = create_user(
        users=users,
        email="another@example.com",
        password="password123",
    )

    with pytest.raises(SessionNotFoundError):
        delete_session(
            sessions=sessions,
            session_id=session.id,
            user_id=another_user.id,
        )


def test_delete_all_user_sessions(sessions, users, test_user):
    create_session(sessions=sessions, users=users, user_id=test_user.id)
    create_session(sessions=sessions, users=users, user_id=test_user.id)
    create_session(sessions=sessions, users=users, user_id=test_user.id)

    another_user = create_user(
        users=users,
        email="another@example.com",
        password="password123",
    )
    create_session(sessions=sessions, users=users, user_id=another_user.id)

    delete_all_user_sessions(
        sessions=sessions,
        user_id=test_user.id,
    )

    user_sessions = get_user_sessions(
        sessions=sessions,
        user_id=test_user.id,
    )
    other_user_sessions = get_user_sessions(
        sessions=sessions,
        user_id=another_user.id,
    )

    assert len(user_sessions) == 0
    assert len(other_user_sessions) == 1


def test_delete_all_user_sessions_except_current(sessions, users, test_user):
    session = create_session(sessions=sessions, users=users, user_id=test_user.id)

    delete_all_user_sessions(
        sessions=sessions,
        user_id=test_user.id,
        except_session_id=session.id,
    )

    user_sessions = get_user_sessions(
        sessions=sessions,
        user_id=test_user.id,
    )

    assert len(user_sessions) == 1
    assert user_sessions[0].id == session.id


def test_update_session_activity(sessions, users, test_user):
    session = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
    )

    original_last_active = session.last_active

    import time

    time.sleep(0.01)

    update_session_activity(
        sessions=sessions,
        session_id=session.id,
    )

    updated_session = sessions.get_session_by_id(session.id)
    assert updated_session.last_active > original_last_active


def test_cleanup_inactive_sessions(sessions, users, test_user):
    active_session = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
    )

    old_session = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
    )
    old_session.last_active = datetime.now(UTC) - timedelta(days=31)

    cleanup_inactive_sessions(
        sessions=sessions,
        inactive_days=30,
    )

    user_sessions = get_user_sessions(
        sessions=sessions,
        user_id=test_user.id,
    )

    assert len(user_sessions) == 1
    assert user_sessions[0].id == active_session.id
