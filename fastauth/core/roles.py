import uuid
from typing import Any

from fastauth.adapters.base.roles import RoleAdapter


class RoleNotFoundError(Exception):
    """Raised when a role is not found."""


class PermissionNotFoundError(Exception):
    """Raised when a permission is not found."""


class RoleAlreadyExistsError(Exception):
    """Raised when trying to create a role that already exists."""


class PermissionAlreadyExistsError(Exception):
    """Raised when trying to create a permission that already exists."""


def create_role(
    *,
    roles: RoleAdapter,
    name: str,
    description: str | None = None,
) -> Any:
    """
    Create a new role.

    Args:
        roles: Role adapter for database operations
        name: Unique role name
        description: Optional role description

    Returns:
        Created role object

    Raises:
        RoleAlreadyExistsError: If a role with the name already exists
    """
    existing_role = roles.get_role_by_name(name=name)

    if existing_role:
        raise RoleAlreadyExistsError(f"Role with name {name} already exists")

    role = roles.create_role(name=name, description=description)

    return role


def create_permission(
    *,
    roles: RoleAdapter,
    name: str,
    description: str | None = None,
) -> Any:
    """
    Create a new permission.

    Args:
        roles: Role adapter for database operations
        name: Unique permission name
        description: Optional permission description

    Returns:
        Created permission object

    Raises:
        PermissionAlreadyExistsError: If a permission with the name already exists
    """
    existing_permission = roles.get_permission_by_name(name=name)

    if existing_permission:
        raise PermissionAlreadyExistsError(
            f"Permission with name {name} already exists"
        )

    permission = roles.create_permission(name=name, description=description)

    return permission


def assign_role(
    *,
    roles: RoleAdapter,
    user_id: uuid.UUID,
    role_name: str,
) -> None:
    """
    Assign a role to a user by role name.

    Args:
        roles: Role adapter for database operations
        user_id: User's unique identifier
        role_name: Name of the role to assign

    Raises:
        RoleNotFoundError: If the role does not exist
    """
    role = roles.get_role_by_name(name=role_name)

    if not role:
        raise RoleNotFoundError(f"Role {role_name} not found")

    roles.assign_role_to_user(user_id=user_id, role_id=role.id)


def remove_role(
    *,
    roles: RoleAdapter,
    user_id: uuid.UUID,
    role_name: str,
) -> None:
    """
    Remove a role from a user by role name.

    Args:
        roles: Role adapter for database operations
        user_id: User's unique identifier
        role_name: Name of the role to remove

    Raises:
        RoleNotFoundError: If the role does not exist
    """
    role = roles.get_role_by_name(name=role_name)

    if not role:
        raise RoleNotFoundError(f"Role {role_name} not found")

    roles.remove_role_from_user(user_id=user_id, role_id=role.id)


def assign_permission_to_role(
    *,
    roles: RoleAdapter,
    role_name: str,
    permission_name: str,
) -> None:
    """
    Assign a permission to a role by names.

    Args:
        roles: Role adapter for database operations
        role_name: Name of the role
        permission_name: Name of the permission to assign

    Raises:
        RoleNotFoundError: If the role does not exist
        PermissionNotFoundError: If the permission does not exist
    """
    role = roles.get_role_by_name(name=role_name)
    if not role:
        raise RoleNotFoundError(f"Role {role_name} not found")

    permission = roles.get_permission_by_name(name=permission_name)
    if not permission:
        raise PermissionNotFoundError(f"Permission {permission_name} not found")

    roles.assign_permission_to_role(role_id=role.id, permission_id=permission.id)


def check_permission(
    *,
    roles: RoleAdapter,
    user_id: uuid.UUID,
    permission_name: str,
) -> bool:
    """
    Check if a user has a specific permission through any of their roles.

    Args:
        roles: Role adapter for database operations
        user_id: User's unique identifier
        permission_name: Name of the permission to check

    Returns:
        True if user has the permission, False otherwise
    """
    user_permissions = roles.get_user_permissions(user_id=user_id)

    return any(perm.name == permission_name for perm in user_permissions)


def get_user_roles(
    *,
    roles: RoleAdapter,
    user_id: uuid.UUID,
) -> list[Any]:
    """
    Get all roles assigned to a user.

    Args:
        roles: Role adapter for database operations
        user_id: User's unique identifier

    Returns:
        List of role objects
    """
    return roles.get_user_roles(user_id=user_id)


def get_user_permissions(
    *,
    roles: RoleAdapter,
    user_id: uuid.UUID,
) -> list[Any]:
    """
    Get all permissions for a user across all their roles.

    Args:
        roles: Role adapter for database operations
        user_id: User's unique identifier

    Returns:
        List of permission objects
    """
    return roles.get_user_permissions(user_id=user_id)


def get_role_permissions(
    *,
    roles: RoleAdapter,
    role_name: str,
) -> list[Any]:
    """
    Get all permissions assigned to a role.

    Args:
        roles: Role adapter for database operations
        role_name: Name of the role

    Returns:
        List of permission objects

    Raises:
        RoleNotFoundError: If the role does not exist
    """
    role = roles.get_role_by_name(name=role_name)

    if not role:
        raise RoleNotFoundError(f"Role {role_name} not found")

    return roles.get_role_permissions(role_id=role.id)
