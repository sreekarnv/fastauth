import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from fastauth.api import dependencies
from fastauth.api.auth import router as auth_router


@pytest.fixture(name="client", scope="function", autouse=False)
def client_fixture():
    from fastauth.security import limits
    from fastauth.settings import settings

    original_value = settings.require_email_verification
    settings.require_email_verification = False

    limits.login_rate_limiter._store.clear()
    limits.register_rate_limiter._store.clear()
    limits.email_verification_rate_limiter._store.clear()

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    app = FastAPI()
    app.include_router(auth_router)

    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[dependencies.get_session] = get_session_override

    with TestClient(app) as client:
        yield client

    settings.require_email_verification = original_value
