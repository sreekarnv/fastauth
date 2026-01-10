"""Custom email client with Jinja2 templates.

This module demonstrates how to create a custom email client
that extends FastAuth's EmailClient to send beautiful HTML emails.
"""

import smtplib
from email.message import EmailMessage
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from fastauth.email.base import EmailClient
from fastauth.settings import settings


class CustomEmailClient(EmailClient):
    """Custom email client with Jinja2 template support.

    This client extends the base EmailClient to send beautiful,
    branded HTML emails using Jinja2 templates.
    """

    def __init__(self, template_dir: str = "templates/emails"):
        """Initialize the custom email client.

        Args:
            template_dir: Path to the directory containing email templates
        """
        template_path = Path(__file__).parent.parent / template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_path)),
            autoescape=True,
        )

        self.base_context = {
            "app_name": (
                settings.app_name if hasattr(settings, "app_name") else "FastAuth App"
            ),
            "company_name": "Your Company",
            "support_email": settings.smtp_from_email,
            "year": 2024,
        }

    def _send_email(
        self,
        *,
        to: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> None:
        """Send an email with both HTML and plain text versions.

        Args:
            to: Recipient email address
            subject: Email subject
            html_body: HTML version of the email
            text_body: Plain text version of the email
        """
        msg = EmailMessage()
        msg["From"] = settings.smtp_from_email
        msg["To"] = to
        msg["Subject"] = subject

        msg.set_content(text_body)

        msg.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)

    def send_verification_email(self, *, to: str, token: str) -> None:
        """Send a beautiful verification email.

        Args:
            to: User's email address
            token: Email verification token
        """
        verification_url = (
            f"http://localhost:8000/auth/email-verification/confirm?token={token}"
        )

        context = {
            **self.base_context,
            "user_email": to,
            "verification_url": verification_url,
            "token": token,
            "expires_in_hours": 24,
        }

        html_template = self.env.get_template("verification.html")
        html_body = html_template.render(context)

        text_template = self.env.get_template("verification.txt")
        text_body = text_template.render(context)

        self._send_email(
            to=to,
            subject=f"Verify your email for {self.base_context['app_name']}",
            html_body=html_body,
            text_body=text_body,
        )

    def send_password_reset_email(self, *, to: str, token: str) -> None:
        """Send a beautiful password reset email.

        Args:
            to: User's email address
            token: Password reset token
        """
        reset_url = f"http://localhost:8000/reset-password?token={token}"

        context = {
            **self.base_context,
            "user_email": to,
            "reset_url": reset_url,
            "token": token,
            "expires_in_hours": 1,
        }

        html_template = self.env.get_template("password_reset.html")
        html_body = html_template.render(context)

        text_template = self.env.get_template("password_reset.txt")
        text_body = text_template.render(context)

        self._send_email(
            to=to,
            subject=f"Reset your password for {self.base_context['app_name']}",
            html_body=html_body,
            text_body=text_body,
        )

    def send_welcome_email(self, *, to: str, name: str = None) -> None:
        """Send a welcome email after successful verification.

        This is a bonus method to show how you can add custom emails.

        Args:
            to: User's email address
            name: User's name (optional)
        """
        context = {
            **self.base_context,
            "user_email": to,
            "user_name": name or to.split("@")[0],
            "dashboard_url": "http://localhost:8000/dashboard",
        }

        html_template = self.env.get_template("welcome.html")
        html_body = html_template.render(context)

        text_template = self.env.get_template("welcome.txt")
        text_body = text_template.render(context)

        self._send_email(
            to=to,
            subject=f"Welcome to {self.base_context['app_name']}!",
            html_body=html_body,
            text_body=text_body,
        )
