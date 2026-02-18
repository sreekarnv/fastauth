from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastauth.email_transports.webhook import WebhookTransport


@pytest.fixture
def transport():
    return WebhookTransport(
        url="https://hooks.example.com/email",
        headers={"X-API-Key": "test-key"},
    )


async def test_send_posts_payload(transport):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        await transport.send(
            to="user@example.com",
            subject="Test",
            body_html="<h1>Hi</h1>",
        )

    mock_client.post.assert_called_once()
    call_kwargs = mock_client.post.call_args
    assert call_kwargs.kwargs["json"]["to"] == "user@example.com"
    assert call_kwargs.kwargs["json"]["subject"] == "Test"
    assert call_kwargs.kwargs["json"]["body_html"] == "<h1>Hi</h1>"
    assert "body_text" not in call_kwargs.kwargs["json"]


async def test_send_includes_body_text(transport):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        await transport.send(
            to="user@example.com",
            subject="Test",
            body_html="<h1>Hi</h1>",
            body_text="Hi plain",
        )

    call_kwargs = mock_client.post.call_args
    assert call_kwargs.kwargs["json"]["body_text"] == "Hi plain"


async def test_send_includes_custom_headers(transport):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client):
        await transport.send(
            to="user@example.com",
            subject="Test",
            body_html="<h1>Hi</h1>",
        )

    call_kwargs = mock_client.post.call_args
    assert call_kwargs.kwargs["headers"]["X-API-Key"] == "test-key"
