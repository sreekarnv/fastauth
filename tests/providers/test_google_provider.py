from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fastauth.providers.base import OAuthTokens, OAuthUserInfo
from fastauth.providers.google import GoogleOAuthProvider


@pytest.fixture
def provider():
    """Create Google OAuth provider instance."""
    return GoogleOAuthProvider(
        client_id="test_client_id", client_secret="test_client_secret"
    )


def test_provider_initialization():
    """Test Google OAuth provider initialization."""
    provider = GoogleOAuthProvider(
        client_id="my_client_id", client_secret="my_client_secret"
    )

    assert provider.client_id == "my_client_id"
    assert provider.client_secret == "my_client_secret"


def test_provider_name(provider: GoogleOAuthProvider):
    """Test provider name property."""
    assert provider.name == "google"


def test_authorization_endpoint(provider: GoogleOAuthProvider):
    """Test authorization endpoint property."""
    assert (
        provider.authorization_endpoint
        == "https://accounts.google.com/o/oauth2/v2/auth"
    )


def test_token_endpoint(provider: GoogleOAuthProvider):
    """Test token endpoint property."""
    assert provider.token_endpoint == "https://oauth2.googleapis.com/token"


def test_user_info_endpoint(provider: GoogleOAuthProvider):
    """Test user info endpoint property."""
    assert (
        provider.user_info_endpoint == "https://www.googleapis.com/oauth2/v2/userinfo"
    )


def test_default_scopes(provider: GoogleOAuthProvider):
    """Test default scopes property."""
    assert provider.default_scopes == "openid email profile"


@pytest.mark.anyio
async def test_exchange_code_for_tokens_success(provider: GoogleOAuthProvider):
    """Test successful code exchange for tokens."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        tokens = await provider.exchange_code_for_tokens(
            code="auth_code_123", redirect_uri="https://example.com/callback"
        )

    assert isinstance(tokens, OAuthTokens)
    assert tokens.access_token == "test_access_token"
    assert tokens.refresh_token == "test_refresh_token"
    assert tokens.expires_in == 3600
    assert tokens.token_type == "Bearer"


@pytest.mark.anyio
async def test_exchange_code_for_tokens_with_pkce(provider: GoogleOAuthProvider):
    """Test code exchange with PKCE verifier."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "test_access_token",
        "expires_in": 3600,
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        await provider.exchange_code_for_tokens(
            code="auth_code_123",
            redirect_uri="https://example.com/callback",
            code_verifier="pkce_verifier_abc",
        )

    # Verify PKCE verifier was included in the request
    call_args = mock_client.post.call_args
    assert call_args[1]["data"]["code_verifier"] == "pkce_verifier_abc"


@pytest.mark.anyio
async def test_exchange_code_for_tokens_without_refresh_token(
    provider: GoogleOAuthProvider,
):
    """Test code exchange when no refresh token is returned."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "test_access_token",
        "expires_in": 3600,
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        tokens = await provider.exchange_code_for_tokens(
            code="auth_code_123", redirect_uri="https://example.com/callback"
        )

    assert tokens.refresh_token is None


@pytest.mark.anyio
async def test_get_user_info_success(provider: GoogleOAuthProvider):
    """Test successful user info fetch."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "google_user_123",
        "email": "user@example.com",
        "verified_email": True,
        "name": "Test User",
        "picture": "https://example.com/avatar.jpg",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        user_info = await provider.get_user_info(access_token="test_token")

    assert isinstance(user_info, OAuthUserInfo)
    assert user_info.provider_user_id == "google_user_123"
    assert user_info.email == "user@example.com"
    assert user_info.email_verified is True
    assert user_info.name == "Test User"
    assert user_info.avatar_url == "https://example.com/avatar.jpg"


@pytest.mark.anyio
async def test_get_user_info_minimal(provider: GoogleOAuthProvider):
    """Test user info fetch with minimal data."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "google_user_456",
        "email": "minimal@example.com",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        user_info = await provider.get_user_info(access_token="test_token")

    assert user_info.provider_user_id == "google_user_456"
    assert user_info.email == "minimal@example.com"
    assert user_info.email_verified is False  # Default value
    assert user_info.name is None
    assert user_info.avatar_url is None


@pytest.mark.anyio
async def test_get_user_info_with_authorization_header(provider: GoogleOAuthProvider):
    """Test that user info request includes correct authorization header."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "user_123",
        "email": "user@example.com",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        await provider.get_user_info(access_token="my_access_token")

    call_args = mock_client.get.call_args
    assert call_args[1]["headers"]["Authorization"] == "Bearer my_access_token"


@pytest.mark.anyio
async def test_refresh_access_token_success(provider: GoogleOAuthProvider):
    """Test successful token refresh."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "new_access_token",
        "expires_in": 3600,
        "token_type": "Bearer",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        tokens = await provider.refresh_access_token(refresh_token="old_refresh_token")

    assert isinstance(tokens, OAuthTokens)
    assert tokens.access_token == "new_access_token"
    assert tokens.expires_in == 3600
    assert tokens.token_type == "Bearer"


@pytest.mark.anyio
async def test_refresh_access_token_with_new_refresh_token(
    provider: GoogleOAuthProvider,
):
    """Test token refresh that returns a new refresh token."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 3600,
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        tokens = await provider.refresh_access_token(refresh_token="old_refresh_token")

    assert tokens.refresh_token == "new_refresh_token"


@pytest.mark.anyio
async def test_refresh_access_token_request_data(provider: GoogleOAuthProvider):
    """Test that refresh token request includes correct data."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "new_token",
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client_class.return_value = mock_client

        await provider.refresh_access_token(refresh_token="my_refresh_token")

    call_args = mock_client.post.call_args
    data = call_args[1]["data"]
    assert data["refresh_token"] == "my_refresh_token"
    assert data["client_id"] == "test_client_id"
    assert data["client_secret"] == "test_client_secret"
    assert data["grant_type"] == "refresh_token"
