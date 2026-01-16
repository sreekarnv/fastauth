"""
OAuth account adapter interface.

Defines the abstract interface for OAuth account storage and management.
Handles linking OAuth provider accounts to internal user accounts.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class OAuthAccountAdapter(ABC):
    """
    Abstract base class for OAuth account database operations.

    Implementations must provide database-specific logic for OAuth account management.
    The core business logic remains database-agnostic.
    """

    @abstractmethod
    def create(
        self,
        *,
        user_id: uuid.UUID,
        provider: str,
        provider_user_id: str,
        access_token_hash: str,
        refresh_token_hash: str | None = None,
        expires_at: datetime | None = None,
        email: str | None = None,
        name: str | None = None,
        avatar_url: str | None = None,
    ) -> Any:
        """
        Create a new OAuth account link.

        Args:
            user_id: Internal user ID
            provider: OAuth provider name (google, github, etc.)
            provider_user_id: User ID from OAuth provider
            access_token_hash: Hashed OAuth access token
            refresh_token_hash: Optional hashed OAuth refresh token
            expires_at: Token expiration time
            email: Email from provider (for reference)
            name: Display name from provider
            avatar_url: Profile picture URL

        Returns:
            Created OAuth account object
        """
        ...

    @abstractmethod
    def get_by_provider_user_id(self, *, provider: str, provider_user_id: str) -> Any:
        """
        Get OAuth account by provider and provider user ID.

        Args:
            provider: OAuth provider name
            provider_user_id: User ID from OAuth provider

        Returns:
            OAuth account if found, None otherwise
        """
        ...

    @abstractmethod
    def get_by_user_id(
        self, *, user_id: uuid.UUID, provider: str | None = None
    ) -> list[Any]:
        """
        Get OAuth accounts for a user, optionally filtered by provider.

        Args:
            user_id: User's unique identifier
            provider: Optional provider name to filter by

        Returns:
            List of OAuth account objects
        """
        ...

    @abstractmethod
    def update_tokens(
        self,
        *,
        account_id: uuid.UUID,
        access_token_hash: str,
        refresh_token_hash: str | None = None,
        expires_at: datetime | None = None,
    ) -> None:
        """
        Update OAuth tokens for an account.

        Args:
            account_id: OAuth account ID
            access_token_hash: New hashed access token
            refresh_token_hash: New hashed refresh token (if applicable)
            expires_at: New expiration time
        """
        ...

    @abstractmethod
    def delete(self, *, account_id: uuid.UUID) -> None:
        """
        Remove OAuth account link.

        Args:
            account_id: OAuth account ID to delete
        """
        ...
