from fastauth.app import FastAuth
from fastauth.config import FastAuthConfig, JWTConfig, PasswordConfig, SecurityConfig
from fastauth.core.protocols import EventHooks
from fastauth.exceptions import (
    AccountLockedError,
    AuthenticationError,
    ConfigError,
    FastAuthError,
    InvalidTokenError,
    MissingDependencyError,
    ProviderError,
    UserAlreadyExistsError,
    UserNotFoundError,
)

__version__ = "0.5.5"
__all__ = [
    "AccountLockedError",
    "AuthenticationError",
    "ConfigError",
    "EventHooks",
    "FastAuth",
    "FastAuthConfig",
    "FastAuthError",
    "InvalidTokenError",
    "JWTConfig",
    "MissingDependencyError",
    "PasswordConfig",
    "ProviderError",
    "SecurityConfig",
    "UserAlreadyExistsError",
    "UserNotFoundError",
    "__version__",
]
