"""Email change adapter interface.

Defines the abstract interface for email change token storage and retrieval.
Inherits from BaseTokenAdapter for common token operations.
"""

import uuid
from abc import abstractmethod
from datetime import datetime
from typing import Any

from fastauth.adapters.base.token import BaseTokenAdapter


class EmailChangeAdapter(BaseTokenAdapter[Any]):
    """
    Abstract base class for email change token database operations.

    Inherits from BaseTokenAdapter and provides backward compatibility
    with the mark_used() method.
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

    def mark_used(self, *, token_hash: str) -> None:
        """
        Mark an email change token as used.

        This is a convenience method that calls invalidate().

        Args:
            token_hash: Hashed token to mark as used
        """
        self.invalidate(token_hash=token_hash)
