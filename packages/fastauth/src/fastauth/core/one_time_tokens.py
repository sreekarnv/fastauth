import hashlib
import secrets


def generate_one_time_token() -> str:
    return secrets.token_urlsafe(32)


def hash_one_time_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
