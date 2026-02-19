from fastauth.adapters.memory import MemoryRoleAdapter
from fastauth.core.rbac import (
    assign_default_role,
    check_user_permission,
    check_user_role,
    seed_roles,
)


async def test_seed_roles():
    adapter = MemoryRoleAdapter()
    roles = [
        {"name": "admin", "permissions": ["users:read", "users:delete"]},
        {"name": "user", "permissions": ["profile:read"]},
    ]
    await seed_roles(adapter, roles)

    assert await adapter.get_role("admin") is not None
    assert await adapter.get_role("user") is not None


async def test_seed_roles_no_duplicates():
    adapter = MemoryRoleAdapter()
    await adapter.create_role("admin", ["existing:perm"])
    await seed_roles(adapter, [{"name": "admin", "permissions": ["new:perm"]}])

    role = await adapter.get_role("admin")
    assert role is not None
    assert role["permissions"] == ["existing:perm"]


async def test_assign_default_role():
    adapter = MemoryRoleAdapter()
    await adapter.create_role("user")
    await assign_default_role(adapter, "u1", "user")

    roles = await adapter.get_user_roles("u1")
    assert "user" in roles


async def test_check_user_role():
    adapter = MemoryRoleAdapter()
    await adapter.create_role("admin")
    await adapter.assign_role("u1", "admin")

    assert await check_user_role(adapter, "u1", "admin") is True
    assert await check_user_role(adapter, "u1", "editor") is False


async def test_check_user_permission():
    adapter = MemoryRoleAdapter()
    await adapter.create_role("admin", ["users:read", "users:delete"])
    await adapter.assign_role("u1", "admin")

    assert await check_user_permission(adapter, "u1", "users:read") is True
    assert await check_user_permission(adapter, "u1", "posts:write") is False
