__version__ = "0.1.0"

from fastauth.core.users import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    EmailNotVerifiedError,
)
from fastauth.core.refresh_tokens import RefreshTokenError
from fastauth.core.password_reset import PasswordResetError
from fastauth.core.email_verification import EmailVerificationError

from fastauth.adapters.base import (
    UserAdapter,
    RefreshTokenAdapter,
    PasswordResetAdapter,
    EmailVerificationAdapter,
)

from fastauth.adapters.sqlalchemy import (
    SQLAlchemyUserAdapter,
    SQLAlchemyRefreshTokenAdapter,
    SQLAlchemyPasswordResetAdapter,
    SQLAlchemyEmailVerificationAdapter,
)

from fastauth.adapters.sqlalchemy.models import (
    User,
    RefreshToken,
    PasswordResetToken,
    EmailVerificationToken,
    SQLModel,
)

from fastauth.api.auth import router as auth_router

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
