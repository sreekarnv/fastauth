"""Base adapter for token operations.

This module provides a generic base class for all token-based adapters
(email verification, password reset, refresh tokens, email change).

By consolidating common token operations (create, get_valid, invalidate)
into a single interface, this eliminates duplicate abstract method definitions
and ensures consistency across all token adapters.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class BaseTokenAdapter(ABC, Generic[T]):
    """
    Abstract base class for token-based adapters.

    This class provides a common interface for all token adapters
    (email verification, password reset, refresh tokens, email change).
    """

    @abstractmethod
    def create(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        **extra: Any,
    ) -> T:
        """
        Create a new token record.

        Args:
            user_id: User's unique identifier
            token_hash: Hashed token
            expires_at: Token expiration datetime
            **extra: Additional fields specific to token type

        Returns:
            The created token record
        """
        ...

    @abstractmethod
    def get_valid(self, *, token_hash: str) -> T | None:
        """
        Get a valid (not used/revoked) token record by hash.

        Args:
            token_hash: Hashed token to look up

        Returns:
            Token record if found and valid, None otherwise
        """
        ...

    @abstractmethod
    def invalidate(self, *, token_hash: str) -> None:
        """
        Mark a token as invalid (used or revoked).

        Args:
            token_hash: Hashed token to invalidate
        """
        ...
