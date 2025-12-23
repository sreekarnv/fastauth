# Deprecated: models moved to fastauth.adapters.sqlalchemy.models

from sqlmodel import SQLModel, Field
from datetime import datetime, UTC
import uuid


class User(SQLModel, table=True):

    __tablename__ = "users"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    email: str = Field(
        index=True,
        unique=True,
        nullable=False,
    )
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    user_id: uuid.UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
    )

    token_hash: str = Field(index=True, unique=True)

    expires_at: datetime
    revoked: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    user_id: uuid.UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
    )

    token_hash: str = Field(unique=True, index=True)

    expires_at: datetime
    used: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EmailVerificationToken(SQLModel, table=True):
    __tablename__ = "email_verification_tokens"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    user_id: uuid.UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
    )

    token_hash: str = Field(unique=True, index=True)

    expires_at: datetime
    used: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.utcnow)
