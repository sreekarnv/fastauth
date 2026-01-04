from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from fastauth.adapters.sqlalchemy.models import OAuthState, User
from fastauth.adapters.sqlalchemy.oauth_states import SQLAlchemyOAuthStateAdapter


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="user")
def user_fixture(session: Session):
    user = User(email="test@example.com", hashed_password="hashed", is_verified=True)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="adapter")
def adapter_fixture(session: Session):
    return SQLAlchemyOAuthStateAdapter(session=session)


def test_create_oauth_state(adapter: SQLAlchemyOAuthStateAdapter):
    """Test creating an OAuth state token."""
    expires_at = datetime.now(UTC) + timedelta(minutes=10)

    state = adapter.create(
        state_hash="hashed_state_123",
        provider="google",
        redirect_uri="https://example.com/callback",
        code_challenge="challenge_abc",
        code_challenge_method="S256",
        expires_at=expires_at,
    )

    assert state.id is not None
    assert state.state_hash == "hashed_state_123"
    assert state.provider == "google"
    assert state.redirect_uri == "https://example.com/callback"
    assert state.code_challenge == "challenge_abc"
    assert state.code_challenge_method == "S256"
    assert state.user_id is None
    # SQLite doesn't preserve timezone info
    assert (
        state.expires_at.replace(tzinfo=UTC) == expires_at
        or abs((state.expires_at.replace(tzinfo=UTC) - expires_at).total_seconds()) < 1
    )
    assert state.used is False


def test_create_oauth_state_with_user(adapter: SQLAlchemyOAuthStateAdapter, user: User):
    """Test creating an OAuth state token with user ID (linking flow)."""
    expires_at = datetime.now(UTC) + timedelta(minutes=10)

    state = adapter.create(
        state_hash="hashed_state_456",
        provider="github",
        redirect_uri="https://example.com/callback",
        user_id=user.id,
        expires_at=expires_at,
    )

    assert state.id is not None
    assert state.user_id == user.id
    assert state.code_challenge is None
    assert state.code_challenge_method is None


def test_get_valid_state(adapter: SQLAlchemyOAuthStateAdapter):
    """Test retrieving a valid OAuth state token."""
    expires_at = datetime.now(UTC) + timedelta(minutes=10)

    created_state = adapter.create(
        state_hash="hashed_state_789",
        provider="google",
        redirect_uri="https://example.com/callback",
        expires_at=expires_at,
    )

    state = adapter.get_valid(state_hash="hashed_state_789")

    assert state is not None
    assert state.id == created_state.id
    assert state.used is False


def test_get_valid_state_not_found(adapter: SQLAlchemyOAuthStateAdapter):
    """Test retrieving non-existent OAuth state."""
    state = adapter.get_valid(state_hash="nonexistent")

    assert state is None


def test_get_valid_excludes_used_state(adapter: SQLAlchemyOAuthStateAdapter):
    """Test that get_valid excludes already used state tokens."""
    expires_at = datetime.now(UTC) + timedelta(minutes=10)

    adapter.create(
        state_hash="used_state",
        provider="google",
        redirect_uri="https://example.com/callback",
        expires_at=expires_at,
    )
    adapter.mark_used(state_hash="used_state")

    state = adapter.get_valid(state_hash="used_state")
    assert state is None


def test_mark_used(adapter: SQLAlchemyOAuthStateAdapter):
    """Test marking OAuth state token as used."""
    expires_at = datetime.now(UTC) + timedelta(minutes=10)

    state = adapter.create(
        state_hash="state_to_use",
        provider="google",
        redirect_uri="https://example.com/callback",
        expires_at=expires_at,
    )

    assert state.used is False
    adapter.mark_used(state_hash="state_to_use")
    updated_state = adapter.session.get(OAuthState, state.id)
    assert updated_state.used is True


def test_mark_used_nonexistent_state(adapter: SQLAlchemyOAuthStateAdapter):
    """Test marking non-existent state as used (should not raise error)."""
    adapter.mark_used(state_hash="nonexistent")


def test_cleanup_expired(adapter: SQLAlchemyOAuthStateAdapter):
    """Test cleaning up expired OAuth state tokens."""
    expired_state = adapter.create(
        state_hash="expired_state",
        provider="google",
        redirect_uri="https://example.com/callback",
        expires_at=datetime.now(UTC) - timedelta(minutes=10),
    )

    valid_state = adapter.create(
        state_hash="valid_state",
        provider="google",
        redirect_uri="https://example.com/callback",
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )

    adapter.cleanup_expired()

    deleted_state = adapter.session.get(OAuthState, expired_state.id)
    assert deleted_state is None

    existing_state = adapter.session.get(OAuthState, valid_state.id)
    assert existing_state is not None


def test_cleanup_expired_with_no_expired_states(adapter: SQLAlchemyOAuthStateAdapter):
    """Test cleanup when there are no expired states."""
    adapter.create(
        state_hash="valid_state_1",
        provider="google",
        redirect_uri="https://example.com/callback",
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )

    adapter.create(
        state_hash="valid_state_2",
        provider="github",
        redirect_uri="https://example.com/callback",
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
    )

    adapter.cleanup_expired()

    state1 = adapter.get_valid(state_hash="valid_state_1")
    state2 = adapter.get_valid(state_hash="valid_state_2")
    assert state1 is not None
    assert state2 is not None
