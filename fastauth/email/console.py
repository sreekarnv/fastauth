"""
Console email client for development.

Prints emails to the console instead of sending them. Useful for
development and testing without configuring an actual email service.
"""

from fastauth.email.base import EmailClient


class ConsoleEmailClient(EmailClient):
    """Email client that prints to console for development/testing."""

    def send_verification_email(self, *, to: str, token: str) -> None:
        print(f"[EMAIL] Verify {to}: token={token}")

    def send_password_reset_email(self, *, to: str, token: str) -> None:
        print(f"[EMAIL] Reset password for {to}: token={token}")
