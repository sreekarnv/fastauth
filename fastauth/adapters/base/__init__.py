"""
Base adapter interfaces for FastAuth.

This module exports all abstract adapter interfaces that define the contract
for database operations. Implementations (like SQLAlchemy adapters) must
inherit from these base classes.

Adapters:
    UserAdapter: User account management
    RefreshTokenAdapter: Refresh token storage
    PasswordResetAdapter: Password reset token storage
    EmailVerificationAdapter: Email verification token storage
    RoleAdapter: Role-based access control
    SessionAdapter: User session management
    OAuthAccountAdapter: OAuth account linking
    OAuthStateAdapter: OAuth CSRF state tokens
"""

from .email_verification import EmailVerificationAdapter
from .oauth_accounts import OAuthAccountAdapter
from .oauth_states import OAuthStateAdapter
from .password_reset import PasswordResetAdapter
from .refresh_tokens import RefreshTokenAdapter
from .roles import RoleAdapter
from .sessions import SessionAdapter
from .users import UserAdapter

__all__ = [
    "UserAdapter",
    "RefreshTokenAdapter",
    "PasswordResetAdapter",
    "EmailVerificationAdapter",
    "RoleAdapter",
    "SessionAdapter",
    "OAuthAccountAdapter",
    "OAuthStateAdapter",
]
