__version__ = "0.1.0"

from fastauth.adapters.base import (
    EmailVerificationAdapter,
    PasswordResetAdapter,
    RefreshTokenAdapter,
    UserAdapter,
)
from fastauth.adapters.sqlalchemy import (
    SQLAlchemyEmailVerificationAdapter,
    SQLAlchemyPasswordResetAdapter,
    SQLAlchemyRefreshTokenAdapter,
    SQLAlchemyUserAdapter,
)
from fastauth.adapters.sqlalchemy.models import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    SQLModel,
    User,
)
from fastauth.api.auth import router as auth_router
from fastauth.core.email_verification import EmailVerificationError
from fastauth.core.password_reset import PasswordResetError
from fastauth.core.refresh_tokens import RefreshTokenError
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
    "UserAdapter",
    "RefreshTokenAdapter",
    "PasswordResetAdapter",
    "EmailVerificationAdapter",
    "SQLAlchemyUserAdapter",
    "SQLAlchemyRefreshTokenAdapter",
    "SQLAlchemyPasswordResetAdapter",
    "SQLAlchemyEmailVerificationAdapter",
    "User",
    "RefreshToken",
    "PasswordResetToken",
    "EmailVerificationToken",
    "SQLModel",
    "auth_router",
    "Settings",
]
