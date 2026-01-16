"""
OAuth provider implementations.

Provides OAuth provider interface and implementations for social login.
Register providers to enable OAuth authentication flows.
"""

from fastauth.providers.base import OAuthProvider, OAuthTokens, OAuthUserInfo
from fastauth.providers.google import GoogleOAuthProvider

__all__ = [
    "OAuthProvider",
    "OAuthTokens",
    "OAuthUserInfo",
    "GoogleOAuthProvider",
    "register_provider",
    "get_provider",
    "list_providers",
]


# Provider registry: maps provider name to provider instance
_PROVIDERS: dict[str, OAuthProvider] = {}


def register_provider(provider: OAuthProvider) -> None:
    """
    Register an OAuth provider.

    Args:
        provider: OAuthProvider instance to register

    Example:
        >>> from fastauth.providers import GoogleOAuthProvider, register_provider
        >>> google = GoogleOAuthProvider(
        ...     client_id="your-client-id",
        ...     client_secret="your-client-secret"
        ... )
        >>> register_provider(google)
    """
    _PROVIDERS[provider.name] = provider


def get_provider(name: str) -> OAuthProvider | None:
    """
    Get a registered OAuth provider by name.

    Args:
        name: Provider name (e.g., 'google', 'github')

    Returns:
        OAuthProvider instance or None if not found

    Example:
        >>> from fastauth.providers import get_provider
        >>> google = get_provider("google")
        >>> if google:
        ...     print(f"Found provider: {google.name}")
    """
    return _PROVIDERS.get(name)


def list_providers() -> list[str]:
    """
    List all registered provider names.

    Returns:
        List of provider names

    Example:
        >>> from fastauth.providers import list_providers
        >>> providers = list_providers()
        >>> print(f"Available providers: {', '.join(providers)}")
    """
    return list(_PROVIDERS.keys())
