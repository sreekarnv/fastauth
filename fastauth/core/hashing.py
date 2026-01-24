"""
Password hashing utilities using Argon2.

Provides secure password hashing and verification using the Argon2 algorithm,
which is the winner of the Password Hashing Competition.
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using Argon2.
    """
    return _password_hasher.hash(password)


def verify_password(hashed_password: str | None, plain_password: str) -> bool:
    """
    Verify a plaintext password against a stored hash.

    Returns False if hashed_password is None (OAuth-only users).
    """
    if hashed_password is None:
        return False
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
