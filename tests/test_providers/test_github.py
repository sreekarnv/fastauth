from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fastauth.providers.github import GitHubProvider


@pytest.fixture
def provider():
    return GitHubProvider(
        client_id="test-client-id",
        client_secret="test-client-secret",
    )


async def test_authorization_url(provider):
    url = await provider.get_authorization_url(
        state="test-state",
        redirect_uri="http://localhost/callback",
    )
    assert "github.com/login/oauth/authorize" in url
    assert "test-client-id" in url
    assert "test-state" in url
    assert "user%3Aemail" in url or "user:email" in url


async def test_no_pkce(provider):
    url = await provider.get_authorization_url(
        state="s",
        redirect_uri="http://localhost/callback",
        code_challenge="should-be-ignored",
    )
    assert "code_challenge" not in url


async def test_exchange_code(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "gh-token",
        "token_type": "bearer",
        "scope": "user:email",
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
        )
        assert result["access_token"] == "gh-token"

        call_kwargs = mock_client.post.call_args
        assert call_kwargs.kwargs["headers"]["Accept"] == "application/json"


async def test_get_user_info_with_email(provider):
    user_response = MagicMock()
    user_response.status_code = 200
    user_response.json.return_value = {
        "id": 12345,
        "login": "testuser",
        "name": "Test User",
        "email": "user@github.com",
        "avatar_url": "https://avatars.githubusercontent.com/u/12345",
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = user_response

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        user = await provider.get_user_info("gh-token")
        assert user["id"] == "12345"
        assert user["email"] == "user@github.com"
        assert user["name"] == "Test User"


async def test_get_user_info_email_fallback(provider):
    user_response = MagicMock()
    user_response.status_code = 200
    user_response.json.return_value = {
        "id": 12345,
        "login": "testuser",
        "name": None,
        "email": None,
        "avatar_url": None,
    }

    emails_response = MagicMock()
    emails_response.status_code = 200
    emails_response.json.return_value = [
        {
            "email": "secondary@example.com",
            "primary": False,
            "verified": True,
        },
        {
            "email": "primary@example.com",
            "primary": True,
            "verified": True,
        },
    ]

    mock_client = AsyncMock()
    mock_client.get.side_effect = [user_response, emails_response]

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        user = await provider.get_user_info("gh-token")
        assert user["email"] == "primary@example.com"
        assert user["name"] == "testuser"


async def test_refresh_returns_none(provider):
    result = await provider.refresh_access_token("token")
    assert result is None
