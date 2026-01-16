"""
SMTP email client implementation.

Sends emails via SMTP server using standard library smtplib.
Supports TLS and authentication via settings.
"""

import smtplib
from email.message import EmailMessage

from fastauth.email.base import EmailClient
from fastauth.settings import settings


class SMTPEmailClient(EmailClient):
    """Email client that sends via SMTP server."""

    def _send(self, *, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"] = settings.smtp_from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(
                    settings.smtp_username,
                    settings.smtp_password,
                )
            server.send_message(msg)

    def send_verification_email(self, *, to: str, token: str) -> None:
        self._send(
            to=to,
            subject="Verify your email",
            body=f"Your verification token: {token}",
        )

    def send_password_reset_email(self, *, to: str, token: str) -> None:
        self._send(
            to=to,
            subject="Reset your password",
            body=f"Your password reset token: {token}",
        )
