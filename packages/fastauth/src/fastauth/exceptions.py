class FastAuthError(Exception):
    """Base exception for all fastauth errors."""


class ConfigError(FastAuthError):
    """Invalid configuration."""


class MissingDependencyError(FastAuthError):
    """An optional dependency is not installed."""

    def __init__(self, package: str, extra: str):
        super().__init__(
            f"'{package}' is required for this feature. "
            f"Install it with: pip install fastauth[{extra}]"
        )


class AuthenticationError(FastAuthError):
    """Authentication failed (bad credentials, expired token, etc.)."""


class UserAlreadyExistsError(FastAuthError):
    """Tried to register with an email that's already taken."""


class UserNotFoundError(FastAuthError):
    """User does not exist."""


class InvalidTokenError(FastAuthError):
    """Token is invalid, expired, or revoked."""


class ProviderError(FastAuthError):
    """Error from an auth provider (OAuth failure, etc.)."""
