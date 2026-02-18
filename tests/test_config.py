from typing import Any

import pytest
from fastauth.adapters.memory import MemoryUserAdapter
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.exceptions import ConfigError
from fastauth.providers.credentials import CredentialsProvider


def _make(**kwargs: Any) -> FastAuthConfig:
    defaults: dict[str, Any] = {
        "secret": "test-secret",
        "providers": [CredentialsProvider()],
        "adapter": MemoryUserAdapter(),
    }
    defaults.update(kwargs)
    return FastAuthConfig(**defaults)


def test_empty_secret_raises():
    with pytest.raises(ConfigError, match="secret"):
        _make(secret="")


def test_no_providers_raises():
    with pytest.raises(ConfigError, match="provider"):
        _make(providers=[])


def test_database_session_without_backend_raises():
    with pytest.raises(ConfigError, match="session_backend"):
        _make(session_strategy="database")


def test_rs256_without_keys_and_jwks_raises():
    with pytest.raises(ConfigError):
        _make(jwt=JWTConfig(algorithm="RS256"))


def test_rs256_with_keys_ok():
    config = _make(jwt=JWTConfig(algorithm="RS256", private_key="pk", public_key="pub"))
    assert config.jwt.algorithm == "RS256"


def test_rs256_with_jwks_enabled_ok():
    config = _make(jwt=JWTConfig(algorithm="RS256", jwks_enabled=True))
    assert config.jwt.jwks_enabled is True


def test_effective_cookie_secure_debug_mode():
    config = _make(debug=True)
    assert config.effective_cookie_secure is False


def test_effective_cookie_secure_production_mode():
    config = _make(debug=False)
    assert config.effective_cookie_secure is True


def test_effective_cookie_secure_explicit_false():
    config = _make(cookie_secure=False)
    assert config.effective_cookie_secure is False


def test_effective_cookie_secure_explicit_true():
    config = _make(cookie_secure=True, debug=True)
    assert config.effective_cookie_secure is True


def test_token_delivery_default():
    config = _make()
    assert config.token_delivery == "json"


def test_cookie_name_defaults():
    config = _make()
    assert config.cookie_name_access == "access_token"
    assert config.cookie_name_refresh == "refresh_token"


def test_cookie_defaults():
    config = _make()
    assert config.cookie_httponly is True
    assert config.cookie_samesite == "lax"
    assert config.cookie_domain is None
    assert config.cookie_secure is None


def test_valid_config_ok():
    config = _make()
    assert config.secret == "test-secret"
    assert len(config.providers) == 1
