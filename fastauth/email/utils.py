"""Email utility functions."""

import logging
from typing import Literal

from fastauth.email.factory import get_email_client

logger = logging.getLogger(__name__)


def send_token_email(
    email: str,
    token: str | None,
    email_type: Literal["verification", "password_reset"],
    is_resend: bool = False,
) -> None:
    """
    Send a token via email if token is present.

    This is a utility function to reduce duplication of email sending logic
    across different authentication flows.

    Args:
        email: Recipient email address
        token: Token to send (if None, no email is sent)
        email_type: Type of email to send ("verification" or "password_reset")
        is_resend: Whether this is a resend operation (affects log message)

    Example:
        >>> send_token_email("user@example.com", "abc123", "verification")
        >>> send_token_email("user@example.com", None, "verification")  # No email sent
        >>> send_token_email("user@example.com", "abc123", "verification", \
            is_resend=True)
    """
    if not token:
        return

    email_client = get_email_client()

    if email_type == "verification":
        email_client.send_verification_email(to=email, token=token)
        if is_resend:
            logger.debug(f"Resent email verification token: {token}")
        else:
            logger.debug(f"Email verification token for {email}: {token}")
    elif email_type == "password_reset":
        email_client.send_password_reset_email(to=email, token=token)
        logger.debug(f"Password reset token: {token}")
