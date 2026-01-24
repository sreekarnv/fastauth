"""
SQLModel database models for FastAuth.

Defines all database tables used by FastAuth including users, tokens,
sessions, roles, permissions, and OAuth accounts. All models use SQLModel
for compatibility with both SQLAlchemy and Pydantic.
"""

import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """
    User account model with authentication and profile fields.
    """

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
    hashed_password: str | None = None
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    last_login: datetime | None = None
    deleted_at: datetime | None = None
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

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EmailChangeToken(SQLModel, table=True):
    __tablename__ = "email_change_tokens"

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

    new_email: str = Field(nullable=False)
    token_hash: str = Field(unique=True, index=True)

    expires_at: datetime
    used: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    name: str = Field(unique=True, nullable=False, index=True)
    description: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Permission(SQLModel, table=True):
    __tablename__ = "permissions"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    name: str = Field(unique=True, nullable=False, index=True)
    description: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"

    user_id: uuid.UUID = Field(
        foreign_key="users.id",
        primary_key=True,
    )
    role_id: uuid.UUID = Field(
        foreign_key="roles.id",
        primary_key=True,
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"

    role_id: uuid.UUID = Field(
        foreign_key="roles.id",
        primary_key=True,
    )
    permission_id: uuid.UUID = Field(
        foreign_key="permissions.id",
        primary_key=True,
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

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

    device: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None

    last_active: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OAuthAccount(SQLModel, table=True):
    __tablename__ = "oauth_accounts"

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

    provider: str = Field(nullable=False, index=True)
    provider_user_id: str = Field(nullable=False, index=True)

    access_token_hash: str = Field(nullable=False)
    refresh_token_hash: str | None = None

    expires_at: datetime | None = None

    email: str | None = None
    name: str | None = None
    avatar_url: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OAuthState(SQLModel, table=True):
    __tablename__ = "oauth_states"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    state_hash: str = Field(unique=True, index=True)

    provider: str = Field(nullable=False)
    redirect_uri: str = Field(nullable=False)

    code_challenge: str | None = None
    code_challenge_method: str | None = None

    user_id: uuid.UUID | None = Field(
        foreign_key="users.id",
        nullable=True,
        index=True,
    )

    expires_at: datetime
    used: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
