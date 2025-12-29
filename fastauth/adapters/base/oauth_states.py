import uuid
from abc import ABC, abstractmethod
from datetime import datetime


class OAuthStateAdapter(ABC):
    """
    Abstract base class for OAuth state token operations.

    State tokens prevent CSRF attacks in OAuth flows.
    """

    @abstractmethod
    def create(
        self,
        *,
        state_hash: str,
        provider: str,
        redirect_uri: str,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
        user_id: uuid.UUID | None = None,
        expires_at: datetime,
    ):
        """
        Create a new OAuth state token.

        Args:
            state_hash: Hashed state token
            provider: OAuth provider name
            redirect_uri: Callback URL after OAuth
            code_challenge: Optional PKCE code challenge
            code_challenge_method: PKCE challenge method (e.g., 'S256')
            user_id: Optional user ID for linking existing account
            expires_at: State token expiration datetime

        Returns:
            Created OAuth state object
        """
        ...

    @abstractmethod
    def get_valid(self, *, state_hash: str):
        """
        Get a valid (unused, non-expired) state token.

        Args:
            state_hash: Hashed state token to look up

        Returns:
            OAuth state record if found and not used, None otherwise
        """
        ...

    @abstractmethod
    def mark_used(self, *, state_hash: str) -> None:
        """
        Mark a state token as used (one-time use).

        Args:
            state_hash: Hashed state token to mark as used
        """
        ...

    @abstractmethod
    def cleanup_expired(self) -> None:
        """
        Remove expired state tokens from database.

        This can be called periodically to clean up old state tokens.
        """
        ...
