from fastauth.security.tokens import generate_secure_token, hash_token


def generate_email_verification_token() -> str:
    """Generate an email verification token.

    This is a convenience wrapper around generate_secure_token().
    """
    return generate_secure_token(48)


def hash_email_verification_token(token: str) -> str:
    """Hash an email verification token.

    This is a convenience wrapper around hash_token().
    """
    return hash_token(token)
