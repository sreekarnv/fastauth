"""Factory for creating adapter instances with shared session.

This module provides AdapterFactory, a convenience class that eliminates
boilerplate adapter initialization code in API endpoints.

Instead of repeatedly writing:
    users = SQLAlchemyUserAdapter(session=session)
    verifications = SQLAlchemyEmailVerificationAdapter(session=session)

You can write:
    adapters = AdapterFactory(session=session)
    user = adapters.users.get_by_email("user@example.com")
    adapters.verifications.create(user_id=user.id, ...)
"""

from dataclasses import dataclass

from sqlmodel import Session

from fastauth.adapters.sqlalchemy.email_change import SQLAlchemyEmailChangeAdapter
from fastauth.adapters.sqlalchemy.email_verification import (
    SQLAlchemyEmailVerificationAdapter,
)
from fastauth.adapters.sqlalchemy.oauth_accounts import SQLAlchemyOAuthAccountAdapter
from fastauth.adapters.sqlalchemy.oauth_states import SQLAlchemyOAuthStateAdapter
from fastauth.adapters.sqlalchemy.password_reset import SQLAlchemyPasswordResetAdapter
from fastauth.adapters.sqlalchemy.refresh_tokens import SQLAlchemyRefreshTokenAdapter
from fastauth.adapters.sqlalchemy.roles import SQLAlchemyRoleAdapter
from fastauth.adapters.sqlalchemy.sessions import SQLAlchemySessionAdapter
from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter


@dataclass
class AdapterFactory:
    """
    Factory for creating adapter instances with a shared database session.

    This class eliminates boilerplate adapter initialization by providing
    properties that lazily create adapter instances as needed.

    Example:
        >>> adapters = AdapterFactory(session=session)
        >>> user = adapters.users.get_by_email("user@example.com")
        >>> adapters.verifications.create(user_id=user.id, ...)
    """

    session: Session

    @property
    def users(self) -> SQLAlchemyUserAdapter:
        """Get user adapter instance."""
        return SQLAlchemyUserAdapter(session=self.session)

    @property
    def verifications(self) -> SQLAlchemyEmailVerificationAdapter:
        """Get email verification adapter instance."""
        return SQLAlchemyEmailVerificationAdapter(session=self.session)

    @property
    def password_resets(self) -> SQLAlchemyPasswordResetAdapter:
        """Get password reset adapter instance."""
        return SQLAlchemyPasswordResetAdapter(session=self.session)

    @property
    def refresh_tokens(self) -> SQLAlchemyRefreshTokenAdapter:
        """Get refresh token adapter instance."""
        return SQLAlchemyRefreshTokenAdapter(session=self.session)

    @property
    def sessions(self) -> SQLAlchemySessionAdapter:
        """Get session adapter instance."""
        return SQLAlchemySessionAdapter(session=self.session)

    @property
    def roles(self) -> SQLAlchemyRoleAdapter:
        """Get role adapter instance."""
        return SQLAlchemyRoleAdapter(session=self.session)

    @property
    def email_changes(self) -> SQLAlchemyEmailChangeAdapter:
        """Get email change adapter instance."""
        return SQLAlchemyEmailChangeAdapter(session=self.session)

    @property
    def oauth_accounts(self) -> SQLAlchemyOAuthAccountAdapter:
        """Get OAuth account adapter instance."""
        return SQLAlchemyOAuthAccountAdapter(session=self.session)

    @property
    def oauth_states(self) -> SQLAlchemyOAuthStateAdapter:
        """Get OAuth state adapter instance."""
        return SQLAlchemyOAuthStateAdapter(session=self.session)
