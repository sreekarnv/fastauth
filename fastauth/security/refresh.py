from fastauth.security.tokens import generate_secure_token, hash_token


def generate_refresh_token() -> str:
    """Generate a cryptographically secure refresh token.

    This is a convenience wrapper around generate_secure_token().
    """
    return generate_secure_token(48)


def hash_refresh_token(token: str) -> str:
    """Hash refresh token before storing.

    This is a convenience wrapper around hash_token().
    """
    return hash_token(token)
