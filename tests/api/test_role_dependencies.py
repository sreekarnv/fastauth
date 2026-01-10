import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from fastauth.adapters.sqlalchemy.roles import SQLAlchemyRoleAdapter
from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter
from fastauth.api import dependencies
from fastauth.api.auth import router as auth_router
from fastauth.api.dependencies import require_permission, require_role
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
def app_with_protected_routes(test_db):
    from fastauth.security import limits
    from fastauth.settings import settings

    original_value = settings.require_email_verification
    settings.require_email_verification = False

    limits.login_rate_limiter._store.clear()
    limits.register_rate_limiter._store.clear()
    limits.email_verification_rate_limiter._store.clear()

    app = FastAPI()
    app.include_router(auth_router)

    @app.get("/admin-only", dependencies=[Depends(require_role("admin"))])
    def admin_only_route():
        return {"message": "Admin access granted"}

    @app.get("/moderator-only", dependencies=[Depends(require_role("moderator"))])
    def moderator_only_route():
        return {"message": "Moderator access granted"}

    @app.get("/read-users", dependencies=[Depends(require_permission("read:users"))])
    def read_users_route():
        return {"message": "Read users permission granted"}

    @app.delete(
        "/delete-users", dependencies=[Depends(require_permission("delete:users"))]
    )
    def delete_users_route():
        return {"message": "Delete users permission granted"}

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
def client(app_with_protected_routes):
    with TestClient(app_with_protected_routes) as client:
        yield client


@pytest.fixture
def session(test_db):
    with Session(test_db) as session:
        try:
            yield session
        finally:
            session.close()


def test_require_role_with_correct_role(client, session):
    user_adapter = SQLAlchemyUserAdapter(session)
    role_adapter = SQLAlchemyRoleAdapter(session)

    user = user_adapter.create_user(email="admin@example.com", hashed_password="hashed")
    admin_role = role_adapter.create_role(name="admin")
    role_adapter.assign_role_to_user(user_id=user.id, role_id=admin_role.id)

    token = create_access_token(subject=str(user.id))

    response = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"message": "Admin access granted"}


def test_require_role_without_role(client, session):
    user_adapter = SQLAlchemyUserAdapter(session)

    user = user_adapter.create_user(email="user@example.com", hashed_password="hashed")

    token = create_access_token(subject=str(user.id))

    response = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Role 'admin' required"


def test_require_role_with_wrong_role(client, session):
    user_adapter = SQLAlchemyUserAdapter(session)
    role_adapter = SQLAlchemyRoleAdapter(session)

    user = user_adapter.create_user(email="user@example.com", hashed_password="hashed")
    moderator_role = role_adapter.create_role(name="moderator")
    role_adapter.assign_role_to_user(user_id=user.id, role_id=moderator_role.id)

    token = create_access_token(subject=str(user.id))

    response = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Role 'admin' required"


def test_require_permission_with_correct_permission(client, session):
    user_adapter = SQLAlchemyUserAdapter(session)
    role_adapter = SQLAlchemyRoleAdapter(session)

    user = user_adapter.create_user(email="user@example.com", hashed_password="hashed")
    role = role_adapter.create_role(name="viewer")
    permission = role_adapter.create_permission(name="read:users")

    role_adapter.assign_permission_to_role(role_id=role.id, permission_id=permission.id)
    role_adapter.assign_role_to_user(user_id=user.id, role_id=role.id)

    token = create_access_token(subject=str(user.id))

    response = client.get("/read-users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"message": "Read users permission granted"}


def test_require_permission_without_permission(client, session):
    user_adapter = SQLAlchemyUserAdapter(session)

    user = user_adapter.create_user(email="user@example.com", hashed_password="hashed")

    token = create_access_token(subject=str(user.id))

    response = client.get("/read-users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Permission 'read:users' required"


def test_require_permission_with_wrong_permission(client, session):
    user_adapter = SQLAlchemyUserAdapter(session)
    role_adapter = SQLAlchemyRoleAdapter(session)

    user = user_adapter.create_user(email="user@example.com", hashed_password="hashed")
    role = role_adapter.create_role(name="viewer")
    permission = role_adapter.create_permission(name="write:users")

    role_adapter.assign_permission_to_role(role_id=role.id, permission_id=permission.id)
    role_adapter.assign_role_to_user(user_id=user.id, role_id=role.id)

    token = create_access_token(subject=str(user.id))

    response = client.get("/read-users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Permission 'read:users' required"


def test_require_permission_from_multiple_roles(client, session):
    user_adapter = SQLAlchemyUserAdapter(session)
    role_adapter = SQLAlchemyRoleAdapter(session)

    user = user_adapter.create_user(email="user@example.com", hashed_password="hashed")

    admin_role = role_adapter.create_role(name="admin")
    moderator_role = role_adapter.create_role(name="moderator")

    delete_permission = role_adapter.create_permission(name="delete:users")

    role_adapter.assign_permission_to_role(
        role_id=moderator_role.id, permission_id=delete_permission.id
    )

    role_adapter.assign_role_to_user(user_id=user.id, role_id=admin_role.id)
    role_adapter.assign_role_to_user(user_id=user.id, role_id=moderator_role.id)

    token = create_access_token(subject=str(user.id))

    response = client.delete(
        "/delete-users", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Delete users permission granted"}


def test_require_role_unauthenticated(client):
    response = client.get("/admin-only")

    assert response.status_code == 401


def test_require_permission_unauthenticated(client):
    response = client.get("/read-users")

    assert response.status_code == 401
