import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from fastauth.api.auth import router as auth_router
from fastauth.api import dependencies
from fastapi import FastAPI


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="app")
def app_fixture(session):
    app = FastAPI()
    app.include_router(auth_router)

    def get_session_override():
        return session

    app.dependency_overrides[dependencies.get_session] = get_session_override

    return app


@pytest.fixture(name="client")
def client_fixture(app):
    return TestClient(app)
