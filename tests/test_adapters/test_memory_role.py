from fastauth.adapters.memory import MemoryRoleAdapter


async def test_create_and_get_role():
    adapter = MemoryRoleAdapter()
    role = await adapter.create_role("admin", ["users:read", "users:delete"])
    assert role["name"] == "admin"
    assert role["permissions"] == ["users:read", "users:delete"]

    fetched = await adapter.get_role("admin")
    assert fetched is not None
    assert fetched["name"] == "admin"


async def test_get_nonexistent_role():
    adapter = MemoryRoleAdapter()
    assert await adapter.get_role("missing") is None


async def test_list_roles():
    adapter = MemoryRoleAdapter()
    await adapter.create_role("admin")
    await adapter.create_role("user")
    roles = await adapter.list_roles()
    assert len(roles) == 2
    names = {r["name"] for r in roles}
    assert names == {"admin", "user"}


async def test_delete_role():
    adapter = MemoryRoleAdapter()
    await adapter.create_role("admin")
    await adapter.assign_role("u1", "admin")

    await adapter.delete_role("admin")
    assert await adapter.get_role("admin") is None
    assert "admin" not in await adapter.get_user_roles("u1")


async def test_add_and_remove_permissions():
    adapter = MemoryRoleAdapter()
    await adapter.create_role("editor", ["posts:read"])
    await adapter.add_permissions("editor", ["posts:write", "posts:delete"])

    role = await adapter.get_role("editor")
    assert set(role["permissions"]) == {
        "posts:read",
        "posts:write",
        "posts:delete",
    }

    await adapter.remove_permissions("editor", ["posts:delete"])
    role = await adapter.get_role("editor")
    assert "posts:delete" not in role["permissions"]


async def test_assign_and_get_user_roles():
    adapter = MemoryRoleAdapter()
    await adapter.create_role("admin")
    await adapter.create_role("editor")

    await adapter.assign_role("u1", "admin")
    await adapter.assign_role("u1", "editor")

    roles = await adapter.get_user_roles("u1")
    assert set(roles) == {"admin", "editor"}


async def test_revoke_role():
    adapter = MemoryRoleAdapter()
    await adapter.create_role("admin")
    await adapter.assign_role("u1", "admin")
    await adapter.revoke_role("u1", "admin")

    roles = await adapter.get_user_roles("u1")
    assert "admin" not in roles


async def test_get_user_permissions():
    adapter = MemoryRoleAdapter()
    await adapter.create_role("admin", ["users:read", "users:delete"])
    await adapter.create_role("editor", ["posts:read", "posts:write"])

    await adapter.assign_role("u1", "admin")
    await adapter.assign_role("u1", "editor")

    perms = await adapter.get_user_permissions("u1")
    assert perms == {
        "users:read",
        "users:delete",
        "posts:read",
        "posts:write",
    }


async def test_get_user_permissions_no_roles():
    adapter = MemoryRoleAdapter()
    perms = await adapter.get_user_permissions("u1")
    assert perms == set()
