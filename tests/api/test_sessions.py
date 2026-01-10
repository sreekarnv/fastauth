import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from fastauth.adapters.sqlalchemy.sessions import SQLAlchemySessionAdapter
from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter
from fastauth.api import dependencies
from fastauth.api.auth import router as auth_router
from fastauth.api.sessions import router as sessions_router
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
def app_with_sessions(test_db):
    from fastauth.security import limits
    from fastauth.settings import settings

    original_value = settings.require_email_verification
    settings.require_email_verification = False

    limits.login_rate_limiter._store.clear()
    limits.register_rate_limiter._store.clear()
    limits.email_verification_rate_limiter._store.clear()

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(sessions_router)

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
def client(app_with_sessions):
    with TestClient(app_with_sessions) as client:
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


def test_list_sessions_empty(client, authenticated_user):
    _, token = authenticated_user

    response = client.get(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert len(data["sessions"]) == 0


def test_list_sessions_after_login(client):
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert len(data["sessions"]) == 2


def test_list_sessions_multiple(client, db_session, authenticated_user):
    user, token = authenticated_user
    session_adapter = SQLAlchemySessionAdapter(db_session)

    session_adapter.create_session(user_id=user.id, device="iPhone")
    session_adapter.create_session(user_id=user.id, device="MacBook")

    response = client.get(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["sessions"]) == 2


def test_list_sessions_unauthenticated(client):
    response = client.get("/sessions")

    assert response.status_code == 401


def test_delete_session_success(client, db_session, authenticated_user):
    user, token = authenticated_user
    session_adapter = SQLAlchemySessionAdapter(db_session)

    session_obj = session_adapter.create_session(user_id=user.id, device="iPhone")

    response = client.delete(
        f"/sessions/{session_obj.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "deleted" in data["message"].lower()

    # Verify session is deleted
    sessions = session_adapter.get_user_sessions(user.id)
    assert len(sessions) == 0


def test_delete_session_not_found(client, authenticated_user):
    import uuid

    _, token = authenticated_user
    non_existent_id = uuid.uuid4()

    response = client.delete(
        f"/sessions/{non_existent_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_delete_session_wrong_user(client, db_session, authenticated_user):
    _, token = authenticated_user
    session_adapter = SQLAlchemySessionAdapter(db_session)
    user_adapter = SQLAlchemyUserAdapter(db_session)

    another_user = user_adapter.create_user(
        email="another@example.com",
        hashed_password="hashed_password_456",
    )
    another_session = session_adapter.create_session(user_id=another_user.id)

    response = client.delete(
        f"/sessions/{another_session.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404

    sessions = session_adapter.get_user_sessions(another_user.id)
    assert len(sessions) == 1


def test_delete_session_unauthenticated(client, db_session, authenticated_user):
    import uuid

    session_id = uuid.uuid4()

    response = client.delete(f"/sessions/{session_id}")

    assert response.status_code == 401


def test_delete_all_sessions(client, db_session, authenticated_user):
    user, token = authenticated_user
    session_adapter = SQLAlchemySessionAdapter(db_session)

    session_adapter.create_session(user_id=user.id, device="iPhone")
    session_adapter.create_session(user_id=user.id, device="MacBook")
    session_adapter.create_session(user_id=user.id, device="iPad")

    response = client.delete(
        "/sessions/all",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "deleted" in data["message"].lower()

    sessions = session_adapter.get_user_sessions(user.id)
    assert len(sessions) == 0


def test_delete_all_sessions_preserves_other_users(
    client, db_session, authenticated_user
):
    user, token = authenticated_user
    session_adapter = SQLAlchemySessionAdapter(db_session)
    user_adapter = SQLAlchemyUserAdapter(db_session)

    session_adapter.create_session(user_id=user.id, device="iPhone")
    session_adapter.create_session(user_id=user.id, device="MacBook")

    another_user = user_adapter.create_user(
        email="another@example.com",
        hashed_password="hashed_password_456",
    )
    session_adapter.create_session(user_id=another_user.id, device="Android")

    client.delete(
        "/sessions/all",
        headers={"Authorization": f"Bearer {token}"},
    )

    user_sessions = session_adapter.get_user_sessions(user.id)
    assert len(user_sessions) == 0

    other_sessions = session_adapter.get_user_sessions(another_user.id)
    assert len(other_sessions) == 1


def test_delete_all_sessions_unauthenticated(client):
    response = client.delete("/sessions/all")

    assert response.status_code == 401


def test_session_response_format(client, db_session, authenticated_user):
    user, token = authenticated_user
    session_adapter = SQLAlchemySessionAdapter(db_session)

    session_obj = session_adapter.create_session(
        user_id=user.id,
        device="iPhone 13",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
    )

    response = client.get(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["sessions"]) == 1

    session_data = data["sessions"][0]
    assert session_data["id"] == str(session_obj.id)
    assert session_data["device"] == "iPhone 13"
    assert session_data["ip_address"] == "192.168.1.1"
    assert session_data["user_agent"] == "Mozilla/5.0"
    assert "last_active" in session_data
    assert "created_at" in session_data
