"""
SQLAlchemy adapter implementations for FastAuth.

This module provides SQLAlchemy/SQLModel implementations of all adapter interfaces.
Use these adapters with any SQLAlchemy-compatible database (PostgreSQL, MySQL, SQLite).

Adapters:
    SQLAlchemyUserAdapter: User account management
    SQLAlchemyRefreshTokenAdapter: Refresh token storage
    SQLAlchemyPasswordResetAdapter: Password reset token storage
    SQLAlchemyEmailVerificationAdapter: Email verification token storage
    SQLAlchemyRoleAdapter: Role-based access control
    SQLAlchemySessionAdapter: User session management
    SQLAlchemyOAuthAccountAdapter: OAuth account linking
    SQLAlchemyOAuthStateAdapter: OAuth CSRF state tokens

Models:
    User, RefreshToken, PasswordResetToken, EmailVerificationToken,
    Role, Permission, UserRole, RolePermission, Session,
    OAuthAccount, OAuthState
"""

from .email_verification import SQLAlchemyEmailVerificationAdapter
from .models import (
    EmailVerificationToken,
    OAuthAccount,
    OAuthState,
    PasswordResetToken,
    Permission,
    RefreshToken,
    Role,
    RolePermission,
    Session,
    SQLModel,
    User,
    UserRole,
)
from .oauth_accounts import SQLAlchemyOAuthAccountAdapter
from .oauth_states import SQLAlchemyOAuthStateAdapter
from .password_reset import SQLAlchemyPasswordResetAdapter
from .refresh_tokens import SQLAlchemyRefreshTokenAdapter
from .roles import SQLAlchemyRoleAdapter
from .sessions import SQLAlchemySessionAdapter
from .users import SQLAlchemyUserAdapter

__all__ = [
    "SQLAlchemyUserAdapter",
    "SQLAlchemyRefreshTokenAdapter",
    "SQLAlchemyPasswordResetAdapter",
    "SQLAlchemyEmailVerificationAdapter",
    "SQLAlchemyRoleAdapter",
    "SQLAlchemySessionAdapter",
    "SQLAlchemyOAuthAccountAdapter",
    "SQLAlchemyOAuthStateAdapter",
    "User",
    "RefreshToken",
    "PasswordResetToken",
    "EmailVerificationToken",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "Session",
    "OAuthAccount",
    "OAuthState",
    "SQLModel",
]
