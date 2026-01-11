import uuid

import pytest

from fastauth.core.account import (
    EmailAlreadyExistsError,
    EmailChangeError,
    InvalidPasswordError,
    UserNotFoundError,
    change_password,
    confirm_email_change,
    delete_account,
    request_email_change,
)
from fastauth.core.hashing import verify_password
from fastauth.core.sessions import create_session
from fastauth.core.users import create_user
from tests.fakes.email_change import FakeEmailChangeAdapter
from tests.fakes.sessions import FakeSessionAdapter
from tests.fakes.users import FakeUserAdapter


@pytest.fixture
def users():
    return FakeUserAdapter()


@pytest.fixture
def sessions():
    return FakeSessionAdapter()


@pytest.fixture
def email_changes():
    return FakeEmailChangeAdapter()


@pytest.fixture
def test_user(users):
    return create_user(
        users=users,
        email="test@example.com",
        password="old-password",
    )


def test_change_password_success(users, sessions, test_user):
    change_password(
        users=users,
        sessions=sessions,
        user_id=test_user.id,
        current_password="old-password",
        new_password="new-password",
    )

    updated_user = users.get_by_id(test_user.id)
    assert verify_password(updated_user.hashed_password, "new-password")
    assert not verify_password(updated_user.hashed_password, "old-password")


def test_change_password_invalid_current_password(users, sessions, test_user):
    with pytest.raises(InvalidPasswordError):
        change_password(
            users=users,
            sessions=sessions,
            user_id=test_user.id,
            current_password="wrong-password",
            new_password="new-password",
        )

    updated_user = users.get_by_id(test_user.id)
    assert verify_password(updated_user.hashed_password, "old-password")


def test_change_password_user_not_found(users, sessions):
    non_existent_id = uuid.uuid4()

    with pytest.raises(UserNotFoundError):
        change_password(
            users=users,
            sessions=sessions,
            user_id=non_existent_id,
            current_password="old-password",
            new_password="new-password",
        )


def test_change_password_invalidates_all_sessions(users, sessions, test_user):
    session1 = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
        device="Device 1",
    )
    session2 = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
        device="Device 2",
    )
    session3 = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
        device="Device 3",
    )

    change_password(
        users=users,
        sessions=sessions,
        user_id=test_user.id,
        current_password="old-password",
        new_password="new-password",
    )

    assert sessions.get_session_by_id(session1.id) is None
    assert sessions.get_session_by_id(session2.id) is None
    assert sessions.get_session_by_id(session3.id) is None


def test_change_password_preserves_current_session(users, sessions, test_user):
    current_session = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
        device="Current Device",
    )
    other_session = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
        device="Other Device",
    )

    change_password(
        users=users,
        sessions=sessions,
        user_id=test_user.id,
        current_password="old-password",
        new_password="new-password",
        current_session_id=current_session.id,
    )

    assert sessions.get_session_by_id(current_session.id) is not None
    assert sessions.get_session_by_id(other_session.id) is None


def test_delete_account_soft_delete(users, sessions, test_user):
    session1 = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
        device="Device 1",
    )

    delete_account(
        users=users,
        sessions=sessions,
        user_id=test_user.id,
        password="old-password",
        hard_delete=False,
    )

    deleted_user = users.get_by_id(test_user.id)
    assert deleted_user is not None
    assert deleted_user.deleted_at is not None
    assert deleted_user.is_active is False
    assert sessions.get_session_by_id(session1.id) is None


def test_delete_account_hard_delete(users, sessions, test_user):
    session1 = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
        device="Device 1",
    )

    delete_account(
        users=users,
        sessions=sessions,
        user_id=test_user.id,
        password="old-password",
        hard_delete=True,
    )

    deleted_user = users.get_by_id(test_user.id)
    assert deleted_user is None
    assert sessions.get_session_by_id(session1.id) is None


def test_delete_account_invalid_password(users, sessions, test_user):
    with pytest.raises(InvalidPasswordError):
        delete_account(
            users=users,
            sessions=sessions,
            user_id=test_user.id,
            password="wrong-password",
            hard_delete=False,
        )

    user = users.get_by_id(test_user.id)
    assert user is not None
    assert user.deleted_at is None
    assert user.is_active is True


def test_delete_account_user_not_found(users, sessions):
    non_existent_id = uuid.uuid4()

    with pytest.raises(UserNotFoundError):
        delete_account(
            users=users,
            sessions=sessions,
            user_id=non_existent_id,
            password="password",
            hard_delete=False,
        )


def test_delete_account_deletes_all_sessions(users, sessions, test_user):
    session1 = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
        device="Device 1",
    )
    session2 = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
        device="Device 2",
    )
    session3 = create_session(
        sessions=sessions,
        users=users,
        user_id=test_user.id,
        device="Device 3",
    )

    delete_account(
        users=users,
        sessions=sessions,
        user_id=test_user.id,
        password="old-password",
        hard_delete=False,
    )

    assert sessions.get_session_by_id(session1.id) is None
    assert sessions.get_session_by_id(session2.id) is None
    assert sessions.get_session_by_id(session3.id) is None


def test_request_email_change_success(users, email_changes, test_user):
    token = request_email_change(
        users=users,
        email_changes=email_changes,
        user_id=test_user.id,
        new_email="newemail@example.com",
        expires_in_minutes=60,
    )

    assert token is not None
    assert len(token) > 0


def test_request_email_change_user_not_found(users, email_changes):
    non_existent_id = uuid.uuid4()

    token = request_email_change(
        users=users,
        email_changes=email_changes,
        user_id=non_existent_id,
        new_email="newemail@example.com",
        expires_in_minutes=60,
    )

    assert token is None


def test_request_email_change_email_already_exists(users, email_changes, test_user):
    create_user(
        users=users,
        email="existing@example.com",
        password="password",
    )

    with pytest.raises(EmailAlreadyExistsError):
        request_email_change(
            users=users,
            email_changes=email_changes,
            user_id=test_user.id,
            new_email="existing@example.com",
            expires_in_minutes=60,
        )


def test_confirm_email_change_success(users, email_changes, test_user):
    token = request_email_change(
        users=users,
        email_changes=email_changes,
        user_id=test_user.id,
        new_email="newemail@example.com",
        expires_in_minutes=60,
    )

    confirm_email_change(
        users=users,
        email_changes=email_changes,
        token=token,
    )

    updated_user = users.get_by_id(test_user.id)
    assert updated_user.email == "newemail@example.com"
    assert updated_user.is_verified is False


def test_confirm_email_change_invalid_token(users, email_changes):
    with pytest.raises(EmailChangeError):
        confirm_email_change(
            users=users,
            email_changes=email_changes,
            token="invalid-token",
        )


def test_confirm_email_change_expired_token(users, email_changes, test_user):
    from datetime import UTC, datetime, timedelta

    from fastauth.security.tokens import hash_token

    token = request_email_change(
        users=users,
        email_changes=email_changes,
        user_id=test_user.id,
        new_email="newemail@example.com",
        expires_in_minutes=60,
    )

    token_hash = hash_token(token)
    email_change_record = email_changes.get_valid(token_hash=token_hash)
    email_change_record.expires_at = datetime.now(UTC) - timedelta(hours=1)

    with pytest.raises(EmailChangeError):
        confirm_email_change(
            users=users,
            email_changes=email_changes,
            token=token,
        )


def test_confirm_email_change_email_taken_by_another_user(
    users, email_changes, test_user
):
    token = request_email_change(
        users=users,
        email_changes=email_changes,
        user_id=test_user.id,
        new_email="newemail@example.com",
        expires_in_minutes=60,
    )

    create_user(
        users=users,
        email="newemail@example.com",
        password="password",
    )

    with pytest.raises(EmailAlreadyExistsError):
        confirm_email_change(
            users=users,
            email_changes=email_changes,
            token=token,
        )
