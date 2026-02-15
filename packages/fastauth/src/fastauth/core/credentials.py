from fastauth._compat import require


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
