"""
FastAuth - Authentication library for FastAPI.

FastAuth provides a complete authentication solution for FastAPI applications
including user registration, login, password reset, email verification,
OAuth providers, RBAC, and session management.

Installation:
    pip install sreekarnv-fastauth        # Core + SQLAlchemy adapters
    pip install sreekarnv-fastauth[oauth] # + OAuth providers
    pip install sreekarnv-fastauth[all]   # All features

Note: FastAPI is a peer dependency - your project must have FastAPI installed.

Basic usage:
    from fastapi import FastAPI
    from fastauth import auth_router, account_router, sessions_router

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(account_router)
    app.include_router(sessions_router)
"""

__version__ = "0.2.4"

from fastauth._compat import HAS_FASTAPI, HAS_HTTPX

# Core exports - always available
from fastauth.adapters.base import (
    EmailVerificationAdapter,
    OAuthAccountAdapter,
    OAuthStateAdapter,
    PasswordResetAdapter,
    RefreshTokenAdapter,
    RoleAdapter,
    SessionAdapter,
    UserAdapter,
)

# SQLAlchemy adapters and models - included by default
from fastauth.adapters.sqlalchemy import (
    OAuthAccount,
    OAuthState,
    SQLAlchemyEmailVerificationAdapter,
    SQLAlchemyOAuthAccountAdapter,
    SQLAlchemyOAuthStateAdapter,
    SQLAlchemyPasswordResetAdapter,
    SQLAlchemyRefreshTokenAdapter,
    SQLAlchemyRoleAdapter,
    SQLAlchemySessionAdapter,
    SQLAlchemyUserAdapter,
)
from fastauth.adapters.sqlalchemy.models import (
    EmailVerificationToken,
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
from fastauth.core.account import (
    EmailAlreadyExistsError,
    EmailChangeError,
    InvalidPasswordError,
    UserNotFoundError,
)
from fastauth.core.email_verification import EmailVerificationError
from fastauth.core.oauth import (
    OAuthAccountAlreadyLinkedError,
    OAuthError,
    OAuthProviderNotFoundError,
    OAuthStateError,
)
from fastauth.core.password_reset import PasswordResetError
from fastauth.core.refresh_tokens import RefreshTokenError
from fastauth.core.roles import (
    PermissionAlreadyExistsError,
    PermissionNotFoundError,
    RoleAlreadyExistsError,
    RoleNotFoundError,
)
from fastauth.core.sessions import SessionNotFoundError
from fastauth.core.users import (
    EmailNotVerifiedError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from fastauth.providers import (
    OAuthProvider,
    OAuthTokens,
    OAuthUserInfo,
    get_provider,
    list_providers,
    register_provider,
)
from fastauth.settings import Settings

__all__ = [
    "__version__",
    # Core exceptions
    "UserAlreadyExistsError",
    "InvalidCredentialsError",
    "EmailNotVerifiedError",
    "InvalidPasswordError",
    "UserNotFoundError",
    "EmailChangeError",
    "EmailAlreadyExistsError",
    "RefreshTokenError",
    "PasswordResetError",
    "EmailVerificationError",
    "RoleNotFoundError",
    "PermissionNotFoundError",
    "RoleAlreadyExistsError",
    "PermissionAlreadyExistsError",
    "SessionNotFoundError",
    "OAuthError",
    "OAuthStateError",
    "OAuthAccountAlreadyLinkedError",
    "OAuthProviderNotFoundError",
    # Base adapters
    "UserAdapter",
    "RefreshTokenAdapter",
    "PasswordResetAdapter",
    "EmailVerificationAdapter",
    "RoleAdapter",
    "SessionAdapter",
    "OAuthAccountAdapter",
    "OAuthStateAdapter",
    # SQLAlchemy adapters
    "SQLAlchemyUserAdapter",
    "SQLAlchemyRefreshTokenAdapter",
    "SQLAlchemyPasswordResetAdapter",
    "SQLAlchemyEmailVerificationAdapter",
    "SQLAlchemyRoleAdapter",
    "SQLAlchemySessionAdapter",
    "SQLAlchemyOAuthAccountAdapter",
    "SQLAlchemyOAuthStateAdapter",
    # Models
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
    # OAuth base
    "OAuthProvider",
    "OAuthTokens",
    "OAuthUserInfo",
    "get_provider",
    "register_provider",
    "list_providers",
    # Settings
    "Settings",
]

# FastAPI routers - requires fastapi (peer dependency)
if HAS_FASTAPI:
    from fastauth.api.account import router as account_router  # noqa: F401
    from fastauth.api.auth import router as auth_router  # noqa: F401
    from fastauth.api.sessions import router as sessions_router  # noqa: F401

    __all__.extend(
        [
            "account_router",
            "auth_router",
            "sessions_router",
        ]
    )

# OAuth features - requires both fastapi and httpx
if HAS_FASTAPI and HAS_HTTPX:
    from fastauth.api.oauth import router as oauth_router  # noqa: F401

    __all__.append("oauth_router")

if HAS_HTTPX:
    from fastauth.providers import GoogleOAuthProvider  # noqa: F401

    __all__.append("GoogleOAuthProvider")
