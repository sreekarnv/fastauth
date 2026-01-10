import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from fastauth.adapters.sqlalchemy.models import OAuthAccount, User
from fastauth.adapters.sqlalchemy.oauth_accounts import SQLAlchemyOAuthAccountAdapter


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()


@pytest.fixture(name="user")
def user_fixture(session: Session):
    user = User(email="test@example.com", hashed_password="hashed", is_verified=True)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="adapter")
def adapter_fixture(session: Session):
    return SQLAlchemyOAuthAccountAdapter(session=session)


def test_create_oauth_account(adapter: SQLAlchemyOAuthAccountAdapter, user: User):
    """Test creating an OAuth account."""
    expires_at = datetime.now(UTC) + timedelta(hours=1)

    account = adapter.create(
        user_id=user.id,
        provider="google",
        provider_user_id="google_123",
        access_token_hash="hashed_access_token",
        refresh_token_hash="hashed_refresh_token",
        expires_at=expires_at,
        email="oauth@example.com",
        name="OAuth User",
        avatar_url="https://example.com/avatar.jpg",
    )

    assert account.id is not None
    assert account.user_id == user.id
    assert account.provider == "google"
    assert account.provider_user_id == "google_123"
    assert account.access_token_hash == "hashed_access_token"
    assert account.refresh_token_hash == "hashed_refresh_token"
    # SQLite doesn't preserve timezone info, so compare the datetime values
    assert (
        account.expires_at.replace(tzinfo=UTC) == expires_at
        or abs((account.expires_at.replace(tzinfo=UTC) - expires_at).total_seconds())
        < 1
    )
    assert account.email == "oauth@example.com"
    assert account.name == "OAuth User"
    assert account.avatar_url == "https://example.com/avatar.jpg"


def test_create_oauth_account_minimal(
    adapter: SQLAlchemyOAuthAccountAdapter, user: User
):
    """Test creating an OAuth account with minimal fields."""
    account = adapter.create(
        user_id=user.id,
        provider="github",
        provider_user_id="github_456",
        access_token_hash="hashed_token",
    )

    assert account.id is not None
    assert account.user_id == user.id
    assert account.provider == "github"
    assert account.provider_user_id == "github_456"
    assert account.access_token_hash == "hashed_token"
    assert account.refresh_token_hash is None
    assert account.expires_at is None
    assert account.email is None
    assert account.name is None
    assert account.avatar_url is None


def test_get_by_provider_user_id(adapter: SQLAlchemyOAuthAccountAdapter, user: User):
    """Test retrieving OAuth account by provider user ID."""
    created_account = adapter.create(
        user_id=user.id,
        provider="google",
        provider_user_id="google_789",
        access_token_hash="hashed",
    )

    account = adapter.get_by_provider_user_id(
        provider="google", provider_user_id="google_789"
    )

    assert account is not None
    assert account.id == created_account.id
    assert account.provider == "google"
    assert account.provider_user_id == "google_789"


def test_get_by_provider_user_id_not_found(adapter: SQLAlchemyOAuthAccountAdapter):
    """Test retrieving non-existent OAuth account."""
    account = adapter.get_by_provider_user_id(
        provider="google", provider_user_id="nonexistent"
    )

    assert account is None


def test_get_by_user_id_all_providers(
    adapter: SQLAlchemyOAuthAccountAdapter, user: User
):
    """Test retrieving all OAuth accounts for a user."""
    adapter.create(
        user_id=user.id,
        provider="google",
        provider_user_id="google_123",
        access_token_hash="hashed1",
    )

    adapter.create(
        user_id=user.id,
        provider="github",
        provider_user_id="github_456",
        access_token_hash="hashed2",
    )

    accounts = adapter.get_by_user_id(user_id=user.id)

    assert len(accounts) == 2
    providers = {account.provider for account in accounts}
    assert providers == {"google", "github"}


def test_get_by_user_id_specific_provider(
    adapter: SQLAlchemyOAuthAccountAdapter, user: User
):
    """Test retrieving OAuth accounts for a user filtered by provider."""
    adapter.create(
        user_id=user.id,
        provider="google",
        provider_user_id="google_123",
        access_token_hash="hashed1",
    )

    adapter.create(
        user_id=user.id,
        provider="github",
        provider_user_id="github_456",
        access_token_hash="hashed2",
    )

    accounts = adapter.get_by_user_id(user_id=user.id, provider="google")

    assert len(accounts) == 1
    assert accounts[0].provider == "google"


def test_get_by_user_id_empty(adapter: SQLAlchemyOAuthAccountAdapter):
    """Test retrieving OAuth accounts for user with no linked accounts."""
    non_existent_user_id = uuid.uuid4()
    accounts = adapter.get_by_user_id(user_id=non_existent_user_id)

    assert len(accounts) == 0


def test_update_tokens(adapter: SQLAlchemyOAuthAccountAdapter, user: User):
    """Test updating OAuth account tokens."""
    account = adapter.create(
        user_id=user.id,
        provider="google",
        provider_user_id="google_123",
        access_token_hash="old_access_token",
        refresh_token_hash="old_refresh_token",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    new_expires_at = datetime.now(UTC) + timedelta(hours=2)

    adapter.update_tokens(
        account_id=account.id,
        access_token_hash="new_access_token",
        refresh_token_hash="new_refresh_token",
        expires_at=new_expires_at,
    )

    updated_account = adapter.session.get(OAuthAccount, account.id)

    assert updated_account.access_token_hash == "new_access_token"
    assert updated_account.refresh_token_hash == "new_refresh_token"
    # SQLite doesn't preserve timezone info
    assert (
        updated_account.expires_at.replace(tzinfo=UTC) == new_expires_at
        or abs(
            (
                updated_account.expires_at.replace(tzinfo=UTC) - new_expires_at
            ).total_seconds()
        )
        < 1
    )
    assert updated_account.updated_at is not None


def test_update_tokens_nonexistent_account(adapter: SQLAlchemyOAuthAccountAdapter):
    """Test updating tokens for non-existent account (should not raise error)."""
    non_existent_id = uuid.uuid4()

    adapter.update_tokens(
        account_id=non_existent_id,
        access_token_hash="new_token",
    )


def test_delete_oauth_account(adapter: SQLAlchemyOAuthAccountAdapter, user: User):
    """Test deleting an OAuth account."""
    account = adapter.create(
        user_id=user.id,
        provider="google",
        provider_user_id="google_123",
        access_token_hash="hashed",
    )

    account_id = account.id

    adapter.delete(account_id=account_id)

    deleted_account = adapter.session.get(OAuthAccount, account_id)
    assert deleted_account is None


def test_delete_nonexistent_account(adapter: SQLAlchemyOAuthAccountAdapter):
    """Test deleting non-existent account (should not raise error)."""
    non_existent_id = uuid.uuid4()

    adapter.delete(account_id=non_existent_id)
