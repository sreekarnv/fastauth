"""
OAuth provider implementations.

Provides OAuth provider interface and implementations for social login.
Register providers to enable OAuth authentication flows.

Requires: pip install sreekarnv-fastauth[oauth] (for provider implementations)
"""

from fastauth._compat import HAS_HTTPX
from fastauth.providers.base import OAuthProvider, OAuthTokens, OAuthUserInfo

__all__ = [
    "OAuthProvider",
    "OAuthTokens",
    "OAuthUserInfo",
    "register_provider",
    "get_provider",
    "list_providers",
]

if HAS_HTTPX:
    from fastauth.providers.google import GoogleOAuthProvider  # noqa: F401

    __all__.append("GoogleOAuthProvider")


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
