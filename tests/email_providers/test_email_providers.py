from unittest.mock import MagicMock, patch

import pytest

from fastauth.email.console import ConsoleEmailClient
from fastauth.email.factory import get_email_client
from fastauth.email.smtp import SMTPEmailClient
from fastauth.settings import settings


class TestConsoleEmailClient:
    """Tests for console email client."""

    def test_send_verification_email(self, capsys):
        """Test sending verification email to console."""
        client = ConsoleEmailClient()
        client.send_verification_email(to="user@example.com", token="verify_token_123")

        captured = capsys.readouterr()
        assert "[EMAIL] Verify user@example.com: token=verify_token_123" in captured.out

    def test_send_password_reset_email(self, capsys):
        """Test sending password reset email to console."""
        client = ConsoleEmailClient()
        client.send_password_reset_email(
            to="reset@example.com", token="reset_token_456"
        )

        captured = capsys.readouterr()
        assert (
            "[EMAIL] Reset password for reset@example.com: token=reset_token_456"
            in captured.out
        )


class TestSMTPEmailClient:
    """Tests for SMTP email client."""

    @patch("smtplib.SMTP")
    def test_send_verification_email_basic(self, mock_smtp):
        """Test sending verification email via SMTP."""

        original_smtp_from = settings.smtp_from_email
        original_smtp_host = settings.smtp_host
        original_smtp_port = settings.smtp_port
        original_smtp_use_tls = settings.smtp_use_tls
        original_smtp_username = settings.smtp_username

        settings.smtp_from_email = "noreply@example.com"
        settings.smtp_host = "smtp.example.com"
        settings.smtp_port = 587
        settings.smtp_use_tls = False
        settings.smtp_username = None

        try:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            client = SMTPEmailClient()
            client.send_verification_email(to="user@example.com", token="token_123")

            mock_smtp.assert_called_once_with("smtp.example.com", 587)

            assert mock_server.send_message.called
            msg = mock_server.send_message.call_args[0][0]
            assert msg["From"] == "noreply@example.com"
            assert msg["To"] == "user@example.com"
            assert msg["Subject"] == "Verify your email"
            assert "token_123" in msg.get_content()

        finally:
            settings.smtp_from_email = original_smtp_from
            settings.smtp_host = original_smtp_host
            settings.smtp_port = original_smtp_port
            settings.smtp_use_tls = original_smtp_use_tls
            settings.smtp_username = original_smtp_username

    @patch("smtplib.SMTP")
    def test_send_verification_email_with_tls(self, mock_smtp):
        """Test sending email with TLS enabled."""
        original_smtp_from = settings.smtp_from_email
        original_smtp_host = settings.smtp_host
        original_smtp_port = settings.smtp_port
        original_smtp_use_tls = settings.smtp_use_tls
        original_smtp_username = settings.smtp_username

        settings.smtp_from_email = "noreply@example.com"
        settings.smtp_host = "smtp.example.com"
        settings.smtp_port = 587
        settings.smtp_use_tls = True
        settings.smtp_username = None

        try:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            client = SMTPEmailClient()
            client.send_verification_email(to="user@example.com", token="token_123")

            mock_server.starttls.assert_called_once()

        finally:
            settings.smtp_from_email = original_smtp_from
            settings.smtp_host = original_smtp_host
            settings.smtp_port = original_smtp_port
            settings.smtp_use_tls = original_smtp_use_tls
            settings.smtp_username = original_smtp_username

    @patch("smtplib.SMTP")
    def test_send_verification_email_with_auth(self, mock_smtp):
        """Test sending email with SMTP authentication."""
        original_smtp_from = settings.smtp_from_email
        original_smtp_host = settings.smtp_host
        original_smtp_port = settings.smtp_port
        original_smtp_use_tls = settings.smtp_use_tls
        original_smtp_username = settings.smtp_username
        original_smtp_password = settings.smtp_password

        settings.smtp_from_email = "noreply@example.com"
        settings.smtp_host = "smtp.example.com"
        settings.smtp_port = 587
        settings.smtp_use_tls = False
        settings.smtp_username = "smtp_user"
        settings.smtp_password = "smtp_pass"

        try:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            client = SMTPEmailClient()
            client.send_verification_email(to="user@example.com", token="token_123")

            mock_server.login.assert_called_once_with("smtp_user", "smtp_pass")

        finally:
            settings.smtp_from_email = original_smtp_from
            settings.smtp_host = original_smtp_host
            settings.smtp_port = original_smtp_port
            settings.smtp_use_tls = original_smtp_use_tls
            settings.smtp_username = original_smtp_username
            settings.smtp_password = original_smtp_password

    @patch("smtplib.SMTP")
    def test_send_password_reset_email(self, mock_smtp):
        """Test sending password reset email via SMTP."""
        original_smtp_from = settings.smtp_from_email
        original_smtp_host = settings.smtp_host
        original_smtp_port = settings.smtp_port
        original_smtp_use_tls = settings.smtp_use_tls
        original_smtp_username = settings.smtp_username

        settings.smtp_from_email = "noreply@example.com"
        settings.smtp_host = "smtp.example.com"
        settings.smtp_port = 587
        settings.smtp_use_tls = False
        settings.smtp_username = None

        try:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            client = SMTPEmailClient()
            client.send_password_reset_email(
                to="reset@example.com", token="reset_token"
            )

            assert mock_server.send_message.called
            msg = mock_server.send_message.call_args[0][0]
            assert msg["Subject"] == "Reset your password"
            assert "reset_token" in msg.get_content()

        finally:
            settings.smtp_from_email = original_smtp_from
            settings.smtp_host = original_smtp_host
            settings.smtp_port = original_smtp_port
            settings.smtp_use_tls = original_smtp_use_tls
            settings.smtp_username = original_smtp_username


class TestEmailFactory:
    """Tests for email client factory."""

    def test_get_email_client_console(self):
        """Test getting console email client from factory."""
        original_backend = settings.email_backend
        settings.email_backend = "console"

        try:
            client = get_email_client()
            assert isinstance(client, ConsoleEmailClient)
        finally:
            settings.email_backend = original_backend

    def test_get_email_client_smtp(self):
        """Test getting SMTP email client from factory."""
        original_backend = settings.email_backend
        settings.email_backend = "smtp"

        try:
            client = get_email_client()
            assert isinstance(client, SMTPEmailClient)
        finally:
            settings.email_backend = original_backend

    def test_get_email_client_unsupported(self):
        """Test error when requesting unsupported email backend."""
        original_backend = settings.email_backend
        settings.email_backend = "unsupported_backend"

        try:
            with pytest.raises(RuntimeError) as exc_info:
                get_email_client()

            assert "Unsupported email_backend" in str(exc_info.value)
        finally:
            settings.email_backend = original_backend
