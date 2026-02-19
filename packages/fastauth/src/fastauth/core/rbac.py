from __future__ import annotations

from fastauth.core.protocols import RoleAdapter


async def seed_roles(role_adapter: RoleAdapter, roles: list[dict]) -> None:
    for role_def in roles:
        existing = await role_adapter.get_role(role_def["name"])
        if not existing:
            await role_adapter.create_role(
                name=role_def["name"],
                permissions=role_def.get("permissions", []),
            )


async def assign_default_role(
    role_adapter: RoleAdapter, user_id: str, default_role: str
) -> None:
    await role_adapter.assign_role(user_id, default_role)


async def check_user_role(role_adapter: RoleAdapter, user_id: str, role: str) -> bool:
    roles = await role_adapter.get_user_roles(user_id)
    return role in roles


async def check_user_permission(
    role_adapter: RoleAdapter, user_id: str, permission: str
) -> bool:
    permissions = await role_adapter.get_user_permissions(user_id)
    return permission in permissions
