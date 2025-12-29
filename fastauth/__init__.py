__version__ = "0.1.0"

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
from fastauth.api.account import router as account_router
from fastauth.api.auth import router as auth_router
from fastauth.api.oauth import router as oauth_router
from fastauth.api.sessions import router as sessions_router
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
    GoogleOAuthProvider,
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
    # Adapters
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
    # Routers
    "account_router",
    "auth_router",
    "sessions_router",
    "oauth_router",
    # OAuth providers
    "OAuthProvider",
    "OAuthTokens",
    "OAuthUserInfo",
    "GoogleOAuthProvider",
    "get_provider",
    "register_provider",
    "list_providers",
    # Settings
    "Settings",
]
