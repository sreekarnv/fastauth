from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fastauth.providers.google import GoogleProvider


@pytest.fixture
def provider():
    return GoogleProvider(
        client_id="test-client-id",
        client_secret="test-client-secret",
    )


async def test_authorization_url(provider):
    url = await provider.get_authorization_url(
        state="test-state",
        redirect_uri="http://localhost/callback",
    )
    assert "accounts.google.com" in url
    assert "test-client-id" in url
    assert "test-state" in url
    assert "openid" in url
    assert "email" in url
    assert "profile" in url


async def test_authorization_url_with_pkce(provider):
    url = await provider.get_authorization_url(
        state="test-state",
        redirect_uri="http://localhost/callback",
        code_challenge="test-challenge",
        code_challenge_method="S256",
    )
    assert "code_challenge=test-challenge" in url
    assert "code_challenge_method=S256" in url


async def test_custom_scopes():
    provider = GoogleProvider(
        client_id="id",
        client_secret="secret",
        scopes=["openid", "email"],
    )
    url = await provider.get_authorization_url(
        state="s", redirect_uri="http://localhost"
    )
    assert "openid+email" in url or "openid%20email" in url


async def test_exchange_code(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "google-token",
        "refresh_token": "google-refresh",
    }

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await provider.exchange_code(
            code="auth-code",
            redirect_uri="http://localhost/callback",
            code_verifier="verifier",
        )
        assert result["access_token"] == "google-token"
        mock_client.post.assert_called_once()


async def test_get_user_info(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "sub": "google-uid-123",
        "email": "user@gmail.com",
        "name": "Test User",
        "picture": "https://example.com/photo.jpg",
        "email_verified": True,
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        user = await provider.get_user_info("google-token")
        assert user["id"] == "google-uid-123"
        assert user["email"] == "user@gmail.com"
        assert user["name"] == "Test User"
        assert user["image"] == "https://example.com/photo.jpg"
        assert user["email_verified"] is True
