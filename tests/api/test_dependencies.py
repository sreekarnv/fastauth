"""Tests for API dependencies module."""

import uuid
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from fastauth.adapters.sqlalchemy.models import User
from fastauth.api import dependencies
from fastauth.security.jwt import create_access_token


@pytest.fixture(name="test_app")
def test_app_fixture():
    """Create test FastAPI app."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    app = FastAPI()

    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[dependencies.get_session] = get_session_override

    @app.get("/test-auth")
    def test_auth(user: User = dependencies.Depends(dependencies.get_current_user)):
        return {"user_id": str(user.id), "email": user.email}

    with TestClient(app) as client:
        yield client, engine

    engine.dispose()


def test_get_session_not_implemented():
    """Test that get_session raises NotImplementedError when not overridden."""
    with pytest.raises(NotImplementedError, match="get_session must be overridden"):
        dependencies.get_session()


def test_get_current_user_invalid_token(test_app):
    """Test get_current_user with invalid token."""
    client, _ = test_app

    response = client.get(
        "/test-auth", headers={"Authorization": "Bearer invalid_token_here"}
    )

    assert response.status_code == 401
    assert "Invalid or expired token" in response.text


def test_get_current_user_token_without_sub(test_app):
    """Test get_current_user with token missing 'sub' claim."""
    client, _ = test_app

    with patch("fastauth.api.dependencies.decode_access_token") as mock_decode:
        mock_decode.return_value = {"some": "data"}  # No 'sub' field

        response = client.get(
            "/test-auth", headers={"Authorization": "Bearer some_token"}
        )

    assert response.status_code == 401
    assert "Invalid token payload" in response.text


def test_get_current_user_invalid_user_id_format(test_app):
    """Test get_current_user with invalid UUID format in token."""
    client, _ = test_app

    with patch("fastauth.api.dependencies.decode_access_token") as mock_decode:
        mock_decode.return_value = {"sub": "not-a-valid-uuid"}

        response = client.get(
            "/test-auth", headers={"Authorization": "Bearer some_token"}
        )

    assert response.status_code == 401
    assert "Invalid user ID in token" in response.text


def test_get_current_user_user_not_found(test_app):
    """Test get_current_user when user doesn't exist."""
    client, _ = test_app

    non_existent_id = uuid.uuid4()
    token = create_access_token(subject=str(non_existent_id))

    response = client.get("/test-auth", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert "User not found or inactive" in response.text


def test_get_current_user_inactive_user(test_app):
    """Test get_current_user with inactive user."""
    client, engine = test_app

    with Session(engine) as session:
        user = User(
            email="inactive@example.com",
            hashed_password="hashed",
            is_verified=True,
            is_active=False,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        user_id = user.id

    token = create_access_token(subject=str(user_id))

    response = client.get("/test-auth", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert "User not found or inactive" in response.text
