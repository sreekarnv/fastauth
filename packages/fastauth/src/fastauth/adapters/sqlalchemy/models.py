from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship
from sqlalchemy.orm.base import Mapped


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "fastauth_users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    image: Mapped[str | None] = mapped_column(String, nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    roles = relationship(
        "RoleModel",
        secondary="fastauth_user_roles",
        back_populates="users",
    )
    sessions = relationship(
        "SessionModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    oauth_accounts = relationship(
        "OAuthAccountModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )


user_roles = Table(
    "fastauth_user_roles",
    Base.metadata,
    Column("user_id", String, ForeignKey("fastauth_users.id"), primary_key=True),
    Column("role_name", String, ForeignKey("fastauth_roles.name"), primary_key=True),
)


class RoleModel(Base):
    __tablename__ = "fastauth_roles"

    name: Mapped[str] = mapped_column(String, primary_key=True)
    users = relationship("UserModel", secondary=user_roles, back_populates="roles")


role_permissions = Table(
    "fastauth_role_permissions",
    Base.metadata,
    Column("role_name", String, ForeignKey("fastauth_roles.name"), primary_key=True),
    Column("permission", String, primary_key=True),
)


class SessionModel(Base):
    __tablename__ = "fastauth_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("fastauth_users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user = relationship("UserModel", back_populates="sessions")


class TokenModel(Base):
    __tablename__ = "fastauth_tokens"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("fastauth_users.id"), index=True
    )
    token_type: Mapped[str] = mapped_column(String)
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class OAuthAccountModel(Base):
    __tablename__ = "fastauth_oauth_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider: Mapped[str] = mapped_column(String)
    provider_account_id: Mapped[str] = mapped_column(String)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("fastauth_users.id"))
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user = relationship("UserModel", back_populates="oauth_accounts")
