__version__ = "0.1.0"

from fastauth.adapters.base import (
    EmailVerificationAdapter,
    PasswordResetAdapter,
    RefreshTokenAdapter,
    RoleAdapter,
    SessionAdapter,
    UserAdapter,
)
from fastauth.adapters.sqlalchemy import (
    SQLAlchemyEmailVerificationAdapter,
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
from fastauth.api.auth import router as auth_router
from fastauth.api.sessions import router as sessions_router
from fastauth.core.email_verification import EmailVerificationError
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
from fastauth.settings import Settings

__all__ = [
    "__version__",
    "UserAlreadyExistsError",
    "InvalidCredentialsError",
    "EmailNotVerifiedError",
    "RefreshTokenError",
    "PasswordResetError",
    "EmailVerificationError",
    "RoleNotFoundError",
    "PermissionNotFoundError",
    "RoleAlreadyExistsError",
    "PermissionAlreadyExistsError",
    "SessionNotFoundError",
    "UserAdapter",
    "RefreshTokenAdapter",
    "PasswordResetAdapter",
    "EmailVerificationAdapter",
    "RoleAdapter",
    "SessionAdapter",
    "SQLAlchemyUserAdapter",
    "SQLAlchemyRefreshTokenAdapter",
    "SQLAlchemyPasswordResetAdapter",
    "SQLAlchemyEmailVerificationAdapter",
    "SQLAlchemyRoleAdapter",
    "SQLAlchemySessionAdapter",
    "User",
    "RefreshToken",
    "PasswordResetToken",
    "EmailVerificationToken",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "Session",
    "SQLModel",
    "auth_router",
    "sessions_router",
    "Settings",
]
