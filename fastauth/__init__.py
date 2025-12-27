__version__ = "0.1.0"

from fastauth.adapters.base import (
    EmailVerificationAdapter,
    PasswordResetAdapter,
    RefreshTokenAdapter,
    RoleAdapter,
    UserAdapter,
)
from fastauth.adapters.sqlalchemy import (
    SQLAlchemyEmailVerificationAdapter,
    SQLAlchemyPasswordResetAdapter,
    SQLAlchemyRefreshTokenAdapter,
    SQLAlchemyRoleAdapter,
    SQLAlchemyUserAdapter,
)
from fastauth.adapters.sqlalchemy.models import (
    EmailVerificationToken,
    PasswordResetToken,
    Permission,
    RefreshToken,
    Role,
    RolePermission,
    SQLModel,
    User,
    UserRole,
)
from fastauth.api.auth import router as auth_router
from fastauth.core.email_verification import EmailVerificationError
from fastauth.core.password_reset import PasswordResetError
from fastauth.core.refresh_tokens import RefreshTokenError
from fastauth.core.roles import (
    PermissionAlreadyExistsError,
    PermissionNotFoundError,
    RoleAlreadyExistsError,
    RoleNotFoundError,
)
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
    "UserAdapter",
    "RefreshTokenAdapter",
    "PasswordResetAdapter",
    "EmailVerificationAdapter",
    "RoleAdapter",
    "SQLAlchemyUserAdapter",
    "SQLAlchemyRefreshTokenAdapter",
    "SQLAlchemyPasswordResetAdapter",
    "SQLAlchemyEmailVerificationAdapter",
    "SQLAlchemyRoleAdapter",
    "User",
    "RefreshToken",
    "PasswordResetToken",
    "EmailVerificationToken",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "SQLModel",
    "auth_router",
    "Settings",
]
