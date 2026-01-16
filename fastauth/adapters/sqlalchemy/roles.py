"""
SQLAlchemy role adapter implementation.

Provides database operations for role-based access control using SQLAlchemy/SQLModel.
"""

import uuid

from sqlmodel import Session, select

from fastauth.adapters.base.roles import RoleAdapter
from fastauth.adapters.sqlalchemy.models import (
    Permission,
    Role,
    RolePermission,
    UserRole,
)


class SQLAlchemyRoleAdapter(RoleAdapter):
    """
    SQLAlchemy implementation of RoleAdapter for RBAC database operations.
    """

    def __init__(self, session: Session):
        self.session = session

    def create_role(self, *, name: str, description: str | None = None):
        role = Role(name=name, description=description)
        self.session.add(role)
        self.session.commit()
        self.session.refresh(role)
        return role

    def get_role_by_name(self, name: str):
        statement = select(Role).where(Role.name == name)
        return self.session.exec(statement).first()

    def create_permission(self, *, name: str, description: str | None = None):
        permission = Permission(name=name, description=description)
        self.session.add(permission)
        self.session.commit()
        self.session.refresh(permission)
        return permission

    def get_permission_by_name(self, name: str):
        statement = select(Permission).where(Permission.name == name)
        return self.session.exec(statement).first()

    def assign_role_to_user(self, *, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        existing = self.session.exec(
            select(UserRole).where(
                UserRole.user_id == user_id, UserRole.role_id == role_id
            )
        ).first()

        if existing:
            return

        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.session.add(user_role)
        self.session.commit()

    def remove_role_from_user(self, *, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        user_role = self.session.exec(
            select(UserRole).where(
                UserRole.user_id == user_id, UserRole.role_id == role_id
            )
        ).first()

        if not user_role:
            return

        self.session.delete(user_role)
        self.session.commit()

    def get_user_roles(self, user_id: uuid.UUID):
        statement = (
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        return list(self.session.exec(statement).all())

    def assign_permission_to_role(
        self, *, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> None:
        existing = self.session.exec(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        ).first()

        if existing:
            return

        role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        self.session.add(role_permission)
        self.session.commit()

    def get_role_permissions(self, role_id: uuid.UUID):
        statement = (
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == role_id)
        )
        return list(self.session.exec(statement).all())

    def get_user_permissions(self, user_id: uuid.UUID):
        statement = (
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
            .distinct()
        )
        return list(self.session.exec(statement).all())
