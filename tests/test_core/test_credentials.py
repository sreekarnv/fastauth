import pytest
from fastauth.config import PasswordConfig
from fastauth.core.credentials import hash_password, validate_password, verify_password


def test_hash_and_verify_password():
    password = "mysecretpassword"
    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password) is True


def test_verify_wrong_password():
    hashed_password = hash_password("correct")

    assert verify_password("wrong", hashed_password) is False


def test_hash_produces_different_hashes():
    password = "mysecretpassword"

    hash_1 = hash_password(password)
    hash_2 = hash_password(password)

    assert not hash_1 == hash_2


class TestValidatePassword:
    def test_valid_password_min_length(self):
        config = PasswordConfig(min_length=8)
        validate_password("12345678", config)

    def test_password_too_short(self):
        config = PasswordConfig(min_length=8)
        with pytest.raises(ValueError, match="at least 8 characters"):
            validate_password("1234567", config)

    def test_password_exceeds_max_length(self):
        config = PasswordConfig(max_length=10)
        with pytest.raises(ValueError, match="at most 10 characters"):
            validate_password("12345678901", config)

    def test_require_uppercase(self):
        config = PasswordConfig(require_uppercase=True)
        with pytest.raises(ValueError, match="uppercase"):
            validate_password("password", config)
        validate_password("Password", config)

    def test_require_lowercase(self):
        config = PasswordConfig(require_lowercase=True)
        with pytest.raises(ValueError, match="lowercase"):
            validate_password("PASSWORD", config)
        validate_password("password", config)

    def test_require_digit(self):
        config = PasswordConfig(require_digit=True)
        with pytest.raises(ValueError, match="digit"):
            validate_password("password", config)
        validate_password("password1", config)

    def test_require_special(self):
        config = PasswordConfig(require_special=True)
        with pytest.raises(ValueError, match="special"):
            validate_password("password1", config)
        validate_password("password!", config)

    def test_all_requirements(self):
        config = PasswordConfig(
            min_length=8,
            require_uppercase=True,
            require_lowercase=True,
            require_digit=True,
            require_special=True,
        )
        validate_password("Password1!", config)

    def test_all_requirements_failing(self):
        config = PasswordConfig(
            min_length=8,
            require_uppercase=True,
            require_lowercase=True,
            require_digit=True,
            require_special=True,
        )
        with pytest.raises(ValueError):
            validate_password("password", config)
