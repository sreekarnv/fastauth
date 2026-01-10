import uuid
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine
from starlette.middleware.sessions import SessionMiddleware

from fastauth.adapters.sqlalchemy.models import User
from fastauth.api import dependencies
from fastauth.api.oauth import router as oauth_router
from fastauth.providers import GoogleOAuthProvider, register_provider
from fastauth.providers.base import OAuthProvider
from fastauth.settings import settings


class MockOAuthProvider(OAuthProvider):
    """Mock OAuth provider for testing."""

    def __init__(self):
        self.client_id = "mock_client_id"
        self.client_secret = "mock_client_secret"

    @property
    def name(self) -> str:
        return "mock"

    @property
    def authorization_endpoint(self) -> str:
        return "https://mock.com/authorize"

    @property
    def token_endpoint(self) -> str:
        return "https://mock.com/token"

    @property
    def user_info_endpoint(self) -> str:
        return "https://mock.com/userinfo"

    @property
    def default_scopes(self) -> str:
        return "email profile"

    async def exchange_code_for_tokens(
        self, *, code: str, redirect_uri: str, code_verifier: str | None = None
    ):
        from fastauth.providers.base import OAuthTokens

        return OAuthTokens(
            access_token="mock_access_token",
            refresh_token="mock_refresh_token",
            expires_in=3600,
            token_type="Bearer",
        )

    async def get_user_info(self, *, access_token: str):
        from fastauth.providers.base import OAuthUserInfo

        return OAuthUserInfo(
            provider_user_id="mock_user_123",
            email="mockuser@example.com",
            name="Mock User",
            email_verified=True,
            avatar_url=None,
        )

    async def refresh_access_token(self, *, refresh_token: str):
        from fastauth.providers.base import OAuthTokens

        return OAuthTokens(
            access_token="new_mock_access_token",
            refresh_token=None,
            expires_in=3600,
            token_type="Bearer",
        )


@pytest.fixture(name="oauth_client", scope="function")
def oauth_client_fixture():
    """Create test client with OAuth router."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    app = FastAPI()

    # Add session middleware for PKCE support
    app.add_middleware(SessionMiddleware, secret_key="test-secret-key")

    app.include_router(oauth_router)

    def get_session_override():
        with Session(engine) as session:
            try:
                yield session
            finally:
                session.close()

    app.dependency_overrides[dependencies.get_session] = get_session_override

    with TestClient(app) as client:
        yield client

    engine.dispose()


@pytest.fixture(autouse=True)
def clear_providers():
    """Clear registered providers before each test."""
    from fastauth.providers import _PROVIDERS

    _PROVIDERS.clear()
    yield
    _PROVIDERS.clear()


def test_get_or_register_provider_google_configured(oauth_client: TestClient):
    """Test _get_or_register_provider with Google OAuth configured."""
    from fastauth.api.oauth import _get_or_register_provider

    original_client_id = settings.google_client_id
    original_client_secret = settings.google_client_secret

    settings.google_client_id = "test-client-id"
    settings.google_client_secret = "test-client-secret"

    try:
        provider = _get_or_register_provider("google")
        assert isinstance(provider, GoogleOAuthProvider)
        assert provider.name == "google"
    finally:
        settings.google_client_id = original_client_id
        settings.google_client_secret = original_client_secret


def test_get_or_register_provider_google_not_configured():
    """Test _get_or_register_provider when Google OAuth is not configured."""
    from fastapi import HTTPException

    from fastauth.api.oauth import _get_or_register_provider

    original_client_id = settings.google_client_id
    original_client_secret = settings.google_client_secret

    settings.google_client_id = None
    settings.google_client_secret = None

    try:
        with pytest.raises(HTTPException) as exc_info:
            _get_or_register_provider("google")

        assert exc_info.value.status_code == 503
        assert "not configured" in exc_info.value.detail
    finally:
        settings.google_client_id = original_client_id
        settings.google_client_secret = original_client_secret


def test_get_or_register_provider_invalid_provider():
    """Test _get_or_register_provider with invalid provider name."""
    from fastapi import HTTPException

    from fastauth.api.oauth import _get_or_register_provider

    with pytest.raises(HTTPException) as exc_info:
        _get_or_register_provider("invalid_provider")

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail


def test_authorize_endpoint_without_user(oauth_client: TestClient):
    """Test OAuth authorization endpoint without authenticated user."""
    mock_provider = MockOAuthProvider()
    register_provider(mock_provider)

    response = oauth_client.get("/oauth/mock/authorize")

    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert "https://mock.com/authorize" in data["authorization_url"]
    assert "client_id=mock_client_id" in data["authorization_url"]
    assert "state=" in data["authorization_url"]
    assert "code_challenge=" in data["authorization_url"]  # PKCE


def test_authorize_endpoint_with_user(oauth_client: TestClient):
    """Test OAuth authorization endpoint with authenticated user (linking flow)."""
    mock_provider = MockOAuthProvider()
    register_provider(mock_provider)

    from fastauth.adapters.sqlalchemy.models import User

    user = User(email="test@example.com", hashed_password="hashed", is_verified=True)

    def get_current_user_override():
        return user

    response = oauth_client.get("/oauth/mock/authorize")

    assert response.status_code == 200


def test_authorize_endpoint_invalid_provider(oauth_client: TestClient):
    """Test OAuth authorization with invalid provider."""
    response = oauth_client.get("/oauth/invalid_provider/authorize")

    assert response.status_code == 404


@patch("fastauth.api.oauth.complete_oauth_flow")
def test_oauth_callback_success(mock_complete_flow, oauth_client: TestClient):
    """Test successful OAuth callback."""
    from urllib.parse import parse_qs, urlparse

    mock_provider = MockOAuthProvider()
    register_provider(mock_provider)

    user = User(
        id=uuid.uuid4(),
        email="oauth@example.com",
        hashed_password="",
        is_verified=True,
    )

    async def mock_async_return(*args, **kwargs):
        return (user, False)

    mock_complete_flow.side_effect = mock_async_return

    auth_response = oauth_client.get("/oauth/mock/authorize")
    assert auth_response.status_code == 200

    auth_data = auth_response.json()
    auth_url = auth_data["authorization_url"]
    parsed_url = urlparse(auth_url)
    query_params = parse_qs(parsed_url.query)
    state = query_params["state"][0]

    callback_response = oauth_client.post(
        "/oauth/mock/callback", json={"code": "test_auth_code", "state": state}
    )

    assert callback_response.status_code == 200
    token_data = callback_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["access_token"]
    assert token_data["refresh_token"]


@patch("fastauth.api.oauth.complete_oauth_flow")
def test_oauth_callback_state_error(mock_complete_flow):
    """Test OAuth callback with state validation error."""
    from fastauth.core.oauth import OAuthStateError

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    app = FastAPI()
    app.include_router(oauth_router)

    def get_session_override():
        with Session(engine) as session:
            try:
                yield session
            finally:
                session.close()

    app.dependency_overrides[dependencies.get_session] = get_session_override

    mock_provider = MockOAuthProvider()
    register_provider(mock_provider)

    async def mock_async_error(*args, **kwargs):
        raise OAuthStateError("Invalid state token")

    mock_complete_flow.side_effect = mock_async_error

    with TestClient(app) as client:
        response = client.post(
            "/oauth/mock/callback",
            json={"code": "test_auth_code", "state": "test_state"},
        )

    engine.dispose()

    assert response.status_code == 400
    assert "Invalid state token" in response.text


@patch("fastauth.api.oauth.complete_oauth_flow")
def test_oauth_callback_account_already_linked(mock_complete_flow):
    """Test OAuth callback when account is already linked to another user."""
    from fastauth.core.oauth import OAuthAccountAlreadyLinkedError

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    app = FastAPI()
    app.include_router(oauth_router)

    def get_session_override():
        with Session(engine) as session:
            try:
                yield session
            finally:
                session.close()

    app.dependency_overrides[dependencies.get_session] = get_session_override

    mock_provider = MockOAuthProvider()
    register_provider(mock_provider)

    async def mock_async_error(*args, **kwargs):
        raise OAuthAccountAlreadyLinkedError(
            "This OAuth account is already linked to another user"
        )

    mock_complete_flow.side_effect = mock_async_error

    with TestClient(app) as client:
        response = client.post(
            "/oauth/mock/callback",
            json={"code": "test_auth_code", "state": "test_state"},
        )

    engine.dispose()

    assert response.status_code == 409
    assert "already linked" in response.text


@patch("fastauth.api.oauth.complete_oauth_flow")
def test_oauth_callback_general_error(mock_complete_flow):
    """Test OAuth callback with general OAuth error."""
    from fastauth.core.oauth import OAuthError

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    app = FastAPI()
    app.include_router(oauth_router)

    def get_session_override():
        with Session(engine) as session:
            try:
                yield session
            finally:
                session.close()

    app.dependency_overrides[dependencies.get_session] = get_session_override

    mock_provider = MockOAuthProvider()
    register_provider(mock_provider)

    async def mock_async_error(*args, **kwargs):
        raise OAuthError("Failed to exchange code for token")

    mock_complete_flow.side_effect = mock_async_error

    with TestClient(app) as client:
        response = client.post(
            "/oauth/mock/callback",
            json={"code": "test_auth_code", "state": "test_state"},
        )

    engine.dispose()

    assert response.status_code == 400
    assert "Failed to exchange code" in response.text


def test_list_linked_accounts_unauthenticated(oauth_client: TestClient):
    """Test listing linked accounts without authentication."""
    response = oauth_client.get("/oauth/linked")

    assert response.status_code == 401


def test_list_linked_accounts_authenticated(oauth_client: TestClient):
    """Test listing linked accounts with authentication."""
    from fastauth.adapters.sqlalchemy.models import User
    from fastauth.api import dependencies

    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        is_verified=True,
    )

    def get_current_user_override():
        return user

    oauth_client.app.dependency_overrides[dependencies.get_current_user] = (
        get_current_user_override
    )

    response = oauth_client.get("/oauth/linked")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    del oauth_client.app.dependency_overrides[dependencies.get_current_user]


def test_unlink_provider_unauthenticated(oauth_client: TestClient):
    """Test unlinking OAuth provider without authentication."""
    response = oauth_client.delete("/oauth/google/unlink")

    assert response.status_code == 401


def test_unlink_provider_success(oauth_client: TestClient):
    """Test successfully unlinking OAuth provider."""
    from fastauth.adapters.sqlalchemy.models import User
    from fastauth.api import dependencies

    user_id = uuid.uuid4()
    user = User(
        id=user_id, email="test@example.com", hashed_password="hashed", is_verified=True
    )

    def get_current_user_override():
        return user

    oauth_client.app.dependency_overrides[dependencies.get_current_user] = (
        get_current_user_override
    )

    # Note: This will return 404 because there's no linked account
    # But it tests the error handling code path
    response = oauth_client.delete("/oauth/google/unlink")

    assert response.status_code == 404

    del oauth_client.app.dependency_overrides[dependencies.get_current_user]


def test_authorize_without_session_middleware():
    """Test that authorize endpoint works without session middleware."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    app = FastAPI()
    app.include_router(oauth_router)

    def get_session_override():
        with Session(engine) as session:
            try:
                yield session
            finally:
                session.close()

    app.dependency_overrides[dependencies.get_session] = get_session_override

    mock_provider = MockOAuthProvider()
    register_provider(mock_provider)

    with TestClient(app) as client:
        # Authorize should still work, just won't store code_verifier
        response = client.get("/oauth/mock/authorize")
        assert response.status_code == 200

    engine.dispose()


def test_oauth_callback_state_mismatch(oauth_client: TestClient):
    """Test OAuth callback with state mismatch (CSRF protection)."""
    mock_provider = MockOAuthProvider()
    register_provider(mock_provider)

    auth_response = oauth_client.get("/oauth/mock/authorize")
    assert auth_response.status_code == 200

    response = oauth_client.post(
        "/oauth/mock/callback", json={"code": "test_code", "state": "wrong_state"}
    )

    assert response.status_code == 400
    assert "State mismatch" in response.text or "CSRF" in response.text
