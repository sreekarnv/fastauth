"""Refresh token adapter interface.

Defines the abstract interface for refresh token storage and retrieval.
Inherits from BaseTokenAdapter for common token operations.
"""

from typing import Any

from fastauth.adapters.base.token import BaseTokenAdapter


class RefreshTokenAdapter(BaseTokenAdapter[Any]):
    """
    Abstract base class for refresh token database operations.

    Inherits from BaseTokenAdapter and provides backward compatibility
    with the get_active() and revoke() methods.
    """

    def get_active(self, *, token_hash: str) -> Any:
        """
        Get an active (not revoked) refresh token.

        This is a convenience method that calls get_valid().

        Args:
            token_hash: Hashed token to look up

        Returns:
            Token record if found and active, None otherwise
        """
        return self.get_valid(token_hash=token_hash)

    def revoke(self, *, token_hash: str) -> None:
        """
        Revoke a refresh token.

        This is a convenience method that calls invalidate().

        Args:
            token_hash: Hashed token to revoke
        """
        self.invalidate(token_hash=token_hash)
