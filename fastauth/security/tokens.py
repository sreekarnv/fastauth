"""Token utility functions.

This module provides centralized utilities for token operations used throughout
FastAuth, eliminating code duplication across token-based features.

Functions:
    - generate_secure_token: Create cryptographically secure URL-safe tokens
    - hash_token: Hash tokens using SHA-256
    - validate_token_expiration: Check if tokens have expired
    - utc_now: Get current UTC datetime with timezone info
    - utc_from_now: Get UTC datetime offset from now
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta


def generate_secure_token(nbytes: int = 48) -> str:
    """Generate a cryptographically secure URL-safe token.

    Args:
        nbytes: Number of bytes for the token. Default is 48.

    Returns:
        A URL-safe base64-encoded token string.
    """
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """Hash a token using SHA-256.

    Args:
        token: The token string to hash.

    Returns:
        The hexadecimal digest of the hashed token.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def validate_token_expiration(
    expires_at: datetime, error_message: str = "Token has expired"
) -> None:
    """Validate that a token has not expired.

    Args:
        expires_at: Token expiration datetime.
        error_message: Custom error message to raise if expired.

    Raises:
        ValueError: If the token has expired.
    """
    # Ensure timezone awareness
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at < datetime.now(UTC):
        raise ValueError(error_message)


def utc_now() -> datetime:
    """Get current UTC datetime with timezone info.

    Returns:
        Current datetime in UTC timezone.
    """
    return datetime.now(UTC)


def utc_from_now(
    *, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0
) -> datetime:
    """Get UTC datetime offset from now.

    Args:
        days: Number of days to offset.
        hours: Number of hours to offset.
        minutes: Number of minutes to offset.
        seconds: Number of seconds to offset.

    Returns:
        UTC datetime offset from current time.
    """
    return utc_now() + timedelta(
        days=days, hours=hours, minutes=minutes, seconds=seconds
    )
