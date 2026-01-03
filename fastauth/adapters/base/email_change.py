import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class EmailChangeAdapter(ABC):
    """
    Abstract base class for email change token database operations.
    """

    @abstractmethod
    def create(
        self,
        *,
        user_id: uuid.UUID,
        new_email: str,
        token_hash: str,
        expires_at: datetime,
    ) -> Any:
        """
        Create an email change request with a token.

        Args:
            user_id: User's unique identifier
            new_email: The new email address to change to
            token_hash: Hashed verification token
            expires_at: Token expiration datetime
        """
        ...

    @abstractmethod
    def get_valid(self, *, token_hash: str) -> Any:
        """
        Get a valid (not used) email change record by token hash.

        Args:
            token_hash: Hashed token to look up

        Returns:
            EmailChange record if found and not used, None otherwise
        """
        ...

    @abstractmethod
    def mark_used(self, *, token_hash: str) -> None:
        """
        Mark an email change token as used.

        Args:
            token_hash: Hashed token to mark as used
        """
        ...
