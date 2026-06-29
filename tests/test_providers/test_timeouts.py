from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastauth.email_transports.webhook import WebhookTransport
from fastauth.providers.github import GitHubProvider
from fastauth.providers.google import GoogleProvider


def _timeout_seconds(client_kwargs):
    if "timeout" not in client_kwargs:
        return None
    timeout = client_kwargs["timeout"]
    if isinstance(timeout, httpx.Timeout):
        return timeout.connect
    return timeout


async def test_google_exchange_code_uses_timeout():
    provider = GoogleProvider(client_id="id", client_secret="secret")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "tok"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await provider.exchange_code(code="c", redirect_uri="http://localhost/cb")
        timeout = _timeout_seconds(mock_cls.call_args.kwargs)
        assert timeout is not None
        assert float(timeout) > 0


async def test_google_get_user_info_uses_timeout():
    provider = GoogleProvider(client_id="id", client_secret="secret")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "sub": "g1",
        "email": "x@x.com",
        "email_verified": True,
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await provider.get_user_info("tok")
        timeout = _timeout_seconds(mock_cls.call_args.kwargs)
        assert timeout is not None
        assert float(timeout) > 0


async def test_google_refresh_access_token_uses_timeout():
    provider = GoogleProvider(client_id="id", client_secret="secret")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "tok"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await provider.refresh_access_token("rt")
        timeout = _timeout_seconds(mock_cls.call_args.kwargs)
        assert timeout is not None
        assert float(timeout) > 0


async def test_github_exchange_code_uses_timeout():
    provider = GitHubProvider(client_id="id", client_secret="secret")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "tok"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await provider.exchange_code(code="c", redirect_uri="http://localhost/cb")
        timeout = _timeout_seconds(mock_cls.call_args.kwargs)
        assert timeout is not None
        assert float(timeout) > 0


async def test_github_get_user_info_uses_timeout():
    provider = GitHubProvider(client_id="id", client_secret="secret")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 1,
        "login": "u",
        "email": "x@x.com",
        "avatar_url": "http://img",
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await provider.get_user_info("tok")
        timeout = _timeout_seconds(mock_cls.call_args.kwargs)
        assert timeout is not None
        assert float(timeout) > 0


async def test_webhook_uses_timeout():
    transport = WebhookTransport(url="https://hooks.example.com/email")

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await transport.send(to="a@b.com", subject="s", body_html="<p/>")
        timeout = _timeout_seconds(mock_cls.call_args.kwargs)
        assert timeout is not None
        assert float(timeout) > 0
