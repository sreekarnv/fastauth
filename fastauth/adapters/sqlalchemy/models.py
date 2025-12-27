import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


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
