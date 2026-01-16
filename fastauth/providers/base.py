"""
OAuth provider base interface.

Defines the abstract interface for OAuth providers. All provider implementations
(Google, GitHub, etc.) must inherit from OAuthProvider.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OAuthUserInfo:
    """User information returned from OAuth provider."""

    provider_user_id: str
    email: str
    email_verified: bool
    name: str | None = None
    avatar_url: str | None = None


@dataclass
class OAuthTokens:
    """Tokens returned from OAuth provider."""

    access_token: str
    refresh_token: str | None = None
    expires_in: int | None = None  # Seconds until expiration
    token_type: str = "Bearer"


class OAuthProvider(ABC):
    """
    Abstract base class for OAuth providers.

    Each provider (Google, GitHub, etc.) implements this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'google', 'github')."""
        ...

    @property
    @abstractmethod
    def authorization_endpoint(self) -> str:
        """OAuth authorization URL."""
        ...

    @property
    @abstractmethod
    def token_endpoint(self) -> str:
        """OAuth token exchange URL."""
        ...

    @property
    @abstractmethod
    def user_info_endpoint(self) -> str:
        """User info API endpoint."""
        ...

    @property
    @abstractmethod
    def default_scopes(self) -> str:
        """Default OAuth scopes (space-separated)."""
        ...

    @abstractmethod
    async def exchange_code_for_tokens(
        self,
        *,
        code: str,
        redirect_uri: str,
        code_verifier: str | None = None,
    ) -> OAuthTokens:
        """
        Exchange authorization code for access/refresh tokens.

        Args:
            code: Authorization code from callback
            redirect_uri: Redirect URI used in authorization
            code_verifier: Optional PKCE code verifier

        Returns:
            OAuthTokens with access token and optional refresh token
        """
        ...

    @abstractmethod
    async def get_user_info(self, *, access_token: str) -> OAuthUserInfo:
        """
        Fetch user information using access token.

        Args:
            access_token: OAuth access token

        Returns:
            OAuthUserInfo with user profile data
        """
        ...

    @abstractmethod
    async def refresh_access_token(self, *, refresh_token: str) -> OAuthTokens:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: OAuth refresh token

        Returns:
            OAuthTokens with new access token
        """
        ...
