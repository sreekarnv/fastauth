"""Password reset adapter interface.

Defines the abstract interface for password reset token storage and retrieval.
Inherits from BaseTokenAdapter for common token operations.
"""

from typing import Any

from fastauth.adapters.base.token import BaseTokenAdapter


class PasswordResetAdapter(BaseTokenAdapter[Any]):
    """
    Abstract base class for password reset token database operations.

    Inherits from BaseTokenAdapter and provides backward compatibility
    with the mark_used() method.
    """

    def mark_used(self, *, token_hash: str) -> None:
        """
        Mark a password reset token as used.

        This is a convenience method that calls invalidate().

        Args:
            token_hash: Hashed token to mark as used
        """
        self.invalidate(token_hash=token_hash)
