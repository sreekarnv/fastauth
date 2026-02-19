class FastAuthError(Exception):
    """Base exception for all FastAuth errors."""


class ConfigError(FastAuthError):
    """Raised when the :class:`~fastauth.config.FastAuthConfig` is invalid.

    Common causes: missing ``secret``, no providers configured, or a
    ``session_strategy="database"`` without a ``session_backend``.
    """


class MissingDependencyError(FastAuthError):
    """Raised when an optional dependency is not installed.

    FastAuth uses optional extras (``jwt``, ``oauth``, ``sqlalchemy``, etc.).
    This error tells you exactly which package to install and which extra to use.

    Args:
        package: The missing Python package name.
        extra: The FastAuth extra that includes the package.
    """

    def __init__(self, package: str, extra: str):
        super().__init__(
            f"'{package}' is required for this feature. "
            f"Install it with: pip install fastauth[{extra}]"
        )


class AuthenticationError(FastAuthError):
    """Raised when authentication fails.

    Covers bad credentials, expired tokens, revoked sessions, and similar
    scenarios where the identity of the requester cannot be confirmed.
    """


class UserAlreadyExistsError(FastAuthError):
    """Raised when attempting to register an email address that is already taken."""


class UserNotFoundError(FastAuthError):
    """Raised when a user lookup returns no result."""


class InvalidTokenError(FastAuthError):
    """Raised when a token is invalid, expired, or has been revoked."""


class ProviderError(FastAuthError):
    """Raised when an auth provider returns an error.

    Typically wraps OAuth provider failures (bad ``code``, revoked tokens, etc.).
    """
