import secrets
import hashlib


def generate_refresh_token() -> str:
    """
    Generate a cryptographically secure refresh token.
    """
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """
    Hash refresh token before storing.
    """
    return hashlib.sha256(token.encode()).hexdigest()
