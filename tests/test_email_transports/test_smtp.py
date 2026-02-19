from unittest.mock import AsyncMock, patch

import pytest
from fastauth.email_transports.smtp import SMTPTransport


@pytest.fixture
def smtp():
    return SMTPTransport(
        host="smtp.example.com",
        port=587,
        username="user@example.com",
        password="secret",
        from_email="noreply@example.com",
    )


@pytest.fixture
def smtp_no_tls():
    return SMTPTransport(
        host="smtp.example.com",
        port=25,
        username="user@example.com",
        password="secret",
        from_email="noreply@example.com",
        use_tls=False,
    )


@patch("aiosmtplib.send", new_callable=AsyncMock)
async def test_send_html_only(mock_send, smtp):
    await smtp.send(
        to="recipient@example.com",
        subject="Hello",
        body_html="<p>Hello</p>",
    )
    mock_send.assert_called_once()
    kwargs = mock_send.call_args.kwargs
    assert kwargs["hostname"] == "smtp.example.com"
    assert kwargs["port"] == 587
    assert kwargs["username"] == "user@example.com"
    assert kwargs["use_tls"] is True


@patch("aiosmtplib.send", new_callable=AsyncMock)
async def test_send_with_plain_text(mock_send, smtp):
    await smtp.send(
        to="recipient@example.com",
        subject="Hello",
        body_html="<p>Hello</p>",
        body_text="Hello",
    )
    mock_send.assert_called_once()


@patch("aiosmtplib.send", new_callable=AsyncMock)
async def test_send_no_tls(mock_send, smtp_no_tls):
    await smtp_no_tls.send(
        to="recipient@example.com",
        subject="Test",
        body_html="<p>Test</p>",
    )
    mock_send.assert_called_once()
    kwargs = mock_send.call_args.kwargs
    assert kwargs["use_tls"] is False


@patch("aiosmtplib.send", new_callable=AsyncMock)
async def test_send_sets_correct_headers(mock_send, smtp):
    await smtp.send(
        to="recipient@example.com",
        subject="Subject Line",
        body_html="<b>body</b>",
    )
    msg = mock_send.call_args.args[0]
    assert msg["To"] == "recipient@example.com"
    assert msg["From"] == "noreply@example.com"
    assert msg["Subject"] == "Subject Line"
