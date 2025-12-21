import secrets
import hashlib


def generate_email_verification_token() -> str:
    return secrets.token_urlsafe(48)


def hash_email_verification_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
