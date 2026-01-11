import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter
from fastauth.api import dependencies
from fastauth.api.account import router as account_router
from fastauth.api.auth import router as auth_router
from fastauth.security.jwt import create_access_token


@pytest.fixture(name="test_db")
def test_db_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def app_with_account(test_db):
    from fastauth.security import limits
    from fastauth.settings import settings

    original_value = settings.require_email_verification
    settings.require_email_verification = False

    limits.login_rate_limiter._store.clear()
    limits.register_rate_limiter._store.clear()
    limits.email_verification_rate_limiter._store.clear()

    app = FastAPI()
    app.include_router(account_router)
    app.include_router(auth_router)

    def get_session_override():
        with Session(test_db) as session:
            try:
                yield session
            finally:
                session.close()

    app.dependency_overrides[dependencies.get_session] = get_session_override

    yield app

    settings.require_email_verification = original_value


@pytest.fixture
def client(app_with_account):
    with TestClient(app_with_account) as client:
        yield client


@pytest.fixture
def db_session(test_db):
    with Session(test_db) as session:
        try:
            yield session
        finally:
            session.close()


@pytest.fixture
def authenticated_user(db_session):
    """Create a user and return user object and access token."""
    user_adapter = SQLAlchemyUserAdapter(db_session)
    user = user_adapter.create_user(
        email="test@example.com",
        hashed_password="hashed_password_123",
    )
    token = create_access_token(subject=str(user.id))
    return user, token


def test_change_password_success(client, db_session):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/account/change-password",
        json={
            "current_password": "password123",
            "new_password": "new-password123",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully"

    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "new-password123",
        },
    )
    assert login_response.status_code == 200


def test_change_password_invalid_current_password(client):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/account/change-password",
        json={
            "current_password": "wrong-password",
            "new_password": "new-password123",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "incorrect" in response.json()["detail"].lower()


def test_change_password_unauthenticated(client):
    response = client.post(
        "/account/change-password",
        json={
            "current_password": "password123",
            "new_password": "new-password123",
        },
    )

    assert response.status_code == 401


def test_change_password_old_token_still_works(client):
    """Test that change password doesn't invalidate the current session/token."""
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/account/change-password",
        json={
            "current_password": "password123",
            "new_password": "new-password123",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    login_with_new_password = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "new-password123",
        },
    )
    assert login_with_new_password.status_code == 200


def test_delete_account_soft_delete(client, db_session):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.request(
        "DELETE",
        "/account/delete",
        json={"password": "password123", "hard_delete": False},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert "deactivated" in response.json()["message"]

    from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter

    user_adapter = SQLAlchemyUserAdapter(db_session)
    user = user_adapter.get_by_email("test@example.com")
    assert user is not None
    assert user.deleted_at is not None
    assert user.is_active is False


def test_delete_account_hard_delete(client, db_session):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.request(
        "DELETE",
        "/account/delete",
        json={"password": "password123", "hard_delete": True},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert "permanently deleted" in response.json()["message"]

    from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter

    user_adapter = SQLAlchemyUserAdapter(db_session)
    user = user_adapter.get_by_email("test@example.com")
    assert user is None


def test_delete_account_invalid_password(client):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.request(
        "DELETE",
        "/account/delete",
        json={"password": "wrong-password", "hard_delete": False},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "incorrect" in response.json()["detail"].lower()


def test_delete_account_unauthenticated(client):
    response = client.request(
        "DELETE",
        "/account/delete",
        json={"password": "password123", "hard_delete": False},
    )

    assert response.status_code == 401


def test_delete_account_invalidates_token(client):
    """Test that deleting account invalidates the current token."""
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.request(
        "DELETE",
        "/account/delete",
        json={"password": "password123", "hard_delete": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    protected_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert protected_response.status_code == 404


def test_request_email_change_success(client):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/account/request-email-change",
        json={"new_email": "newemail@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert "token" in response.json()
    assert "message" in response.json()


def test_request_email_change_email_already_exists(client):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    client.post(
        "/auth/register",
        json={"email": "existing@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/account/request-email-change",
        json={"new_email": "existing@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_request_email_change_unauthenticated(client):
    response = client.post(
        "/account/request-email-change",
        json={"new_email": "newemail@example.com"},
    )

    assert response.status_code == 401


def test_confirm_email_change_success(client, db_session):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    email_change_response = client.post(
        "/account/request-email-change",
        json={"new_email": "newemail@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    email_token = email_change_response.json()["token"]

    response = client.post(
        "/account/confirm-email-change",
        json={"token": email_token},
    )

    assert response.status_code == 200
    assert "Email changed successfully" in response.json()["message"]

    from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter

    user_adapter = SQLAlchemyUserAdapter(db_session)
    user = user_adapter.get_by_email("newemail@example.com")
    assert user is not None
    assert user.email == "newemail@example.com"
    assert user.is_verified is False


def test_confirm_email_change_invalid_token(client):
    response = client.post(
        "/account/confirm-email-change",
        json={"token": "invalid-token"},
    )

    assert response.status_code == 400


def test_confirm_email_change_get_success(client, db_session):
    """Test confirm email change via GET endpoint."""
    client.post(
        "/auth/register",
        json={"email": "test_get@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test_get@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    email_change_response = client.post(
        "/account/request-email-change",
        json={"new_email": "newemail_get@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    email_token = email_change_response.json()["token"]

    response = client.get(f"/account/confirm-email-change?token={email_token}")

    assert response.status_code == 200
    assert response.json()["message"] == "Email changed successfully"
    assert response.json()["status"] == "success"

    from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter

    user_adapter = SQLAlchemyUserAdapter(db_session)
    user = user_adapter.get_by_email("newemail_get@example.com")
    assert user is not None
    assert user.email == "newemail_get@example.com"


def test_confirm_email_change_get_invalid_token(client):
    """Test confirm email change via GET with invalid token."""
    response = client.get("/account/confirm-email-change?token=invalid-token")

    assert response.status_code == 400


def test_confirm_email_change_get_email_already_exists(client):
    """Test confirm email change via GET when email is already taken."""
    client.post(
        "/auth/register",
        json={"email": "existing@example.com", "password": "password123"},
    )

    client.post(
        "/auth/register",
        json={"email": "second@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "second@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    email_change_response = client.post(
        "/account/request-email-change",
        json={"new_email": "existing@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    email_json = email_change_response.json()

    assert email_change_response.status_code == 400
    assert "already exists" in email_json["detail"].lower()


def test_confirm_email_change_email_taken_after_request(client):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    email_change_response = client.post(
        "/account/request-email-change",
        json={"new_email": "newemail@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    email_token = email_change_response.json()["token"]

    client.post(
        "/auth/register",
        json={"email": "newemail@example.com", "password": "password123"},
    )

    response = client.post(
        "/account/confirm-email-change",
        json={"token": email_token},
    )

    assert response.status_code == 400
    assert "no longer available" in response.json()["detail"].lower()


def test_confirm_email_change_get_email_taken_after_request(client):
    """Test GET confirm email change when email is taken after request."""
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    email_change_response = client.post(
        "/account/request-email-change",
        json={"new_email": "newemail@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    email_token = email_change_response.json()["token"]

    client.post(
        "/auth/register",
        json={"email": "newemail@example.com", "password": "password123"},
    )

    response = client.get(f"/account/confirm-email-change?token={email_token}")

    assert response.status_code == 400
    assert "no longer available" in response.json()["detail"].lower()


def test_change_password_user_not_found_error(client):
    """Test change password when core function raises UserNotFoundError."""
    from unittest.mock import patch

    from fastauth.core.account import UserNotFoundError

    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    with patch("fastauth.api.account.change_password") as mock_change:
        mock_change.side_effect = UserNotFoundError("User not found")

        response = client.post(
            "/account/change-password",
            json={
                "current_password": "password123",
                "new_password": "newpassword456",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404
    assert "User not found" in response.text


def test_delete_account_user_not_found_error(client):
    """Test delete account when core function raises UserNotFoundError."""
    from unittest.mock import patch

    from fastauth.core.account import UserNotFoundError

    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    with patch("fastauth.api.account.delete_account") as mock_delete:
        mock_delete.side_effect = UserNotFoundError("User not found")

        response = client.request(
            "DELETE",
            "/account/delete",
            json={"password": "password123", "hard_delete": False},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404
    assert "User not found" in response.text


def test_request_email_change_no_token_returned(client):
    """Test request email change when core function returns None."""
    from unittest.mock import patch

    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    with patch("fastauth.api.account.request_email_change") as mock_request:
        mock_request.return_value = None

        response = client.post(
            "/account/request-email-change",
            json={"new_email": "newemail@example.com"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404
    assert "User not found" in response.text
