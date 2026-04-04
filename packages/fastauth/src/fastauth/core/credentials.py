import re
from typing import TYPE_CHECKING

from fastauth._compat import require

if TYPE_CHECKING:
    from fastauth.config import PasswordConfig


def hash_password(password: str) -> str:
    require("argon2", "argon2")
    from argon2 import PasswordHasher

    return PasswordHasher().hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    require("argon2", "argon2")
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError

    try:
        return PasswordHasher().verify(hashed, plain)
    except VerifyMismatchError:
        return False


def validate_password(password: str, config: "PasswordConfig") -> None:
    """Validate password against strength requirements.

    Args:
        password: The plain text password to validate.
        config: Password configuration with strength requirements.

    Raises:
        ValueError: If password doesn't meet requirements.
    """
    if len(password) < config.min_length:
        raise ValueError(
            f"Password must be at least {config.min_length} characters long"
        )

    if len(password) > config.max_length:
        raise ValueError(
            f"Password must be at most {config.max_length} characters long"
        )

    if config.require_uppercase and not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")

    if config.require_lowercase and not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")

    if config.require_digit and not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")

    if config.require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character")
