import pytest
from fastapi import FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import (
    MemoryRoleAdapter,
    MemoryUserAdapter,
)
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.providers.credentials import CredentialsProvider
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def rbac_app():
    adapter = MemoryUserAdapter()
    role_adapter = MemoryRoleAdapter()
    config = FastAuthConfig(
        secret="test-secret-for-rbac",
        providers=[CredentialsProvider()],
        adapter=adapter,
        jwt=JWTConfig(algorithm="HS256"),
    )
    auth = FastAuth(config)
    auth.role_adapter = role_adapter

    app = FastAPI()
    auth.mount(app)
    return app, role_adapter, adapter


@pytest.fixture
async def rbac_client(rbac_app):
    app, _, _ = rbac_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    """Register a user and return (access_token, user_email)."""
    email = "admin@example.com"
    await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "name": "Admin",
        },
    )
    resp = await client.post(
        "/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return resp.json()["access_token"], email


async def _make_admin(rbac_app, user_email: str) -> None:
    """Assign admin role to the user."""
    _, role_adapter, user_adapter = rbac_app
    await role_adapter.create_role("admin", ["users:read", "users:delete"])
    user = await user_adapter.get_user_by_email(user_email)
    await role_adapter.assign_role(user["id"], "admin")


async def test_list_roles(rbac_client, rbac_app):
    token, email = await _register_and_login(rbac_client)
    await _make_admin(rbac_app, email)

    resp = await rbac_client.get(
        "/auth/roles",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    roles = resp.json()
    assert len(roles) == 1
    assert roles[0]["name"] == "admin"


async def test_list_roles_forbidden(rbac_client):
    token, _ = await _register_and_login(rbac_client)
    resp = await rbac_client.get(
        "/auth/roles",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_create_role(rbac_client, rbac_app):
    token, email = await _register_and_login(rbac_client)
    await _make_admin(rbac_app, email)

    resp = await rbac_client.post(
        "/auth/roles",
        json={"name": "editor", "permissions": ["posts:write"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "editor"
    assert resp.json()["permissions"] == ["posts:write"]


async def test_create_role_duplicate(rbac_client, rbac_app):
    token, email = await _register_and_login(rbac_client)
    await _make_admin(rbac_app, email)

    resp = await rbac_client.post(
        "/auth/roles",
        json={"name": "admin", "permissions": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


async def test_delete_role(rbac_client, rbac_app):
    token, email = await _register_and_login(rbac_client)
    await _make_admin(rbac_app, email)

    _, role_adapter, _ = rbac_app
    await role_adapter.create_role("editor")

    resp = await rbac_client.delete(
        "/auth/roles/editor",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Role deleted"


async def test_delete_role_not_found(rbac_client, rbac_app):
    token, email = await _register_and_login(rbac_client)
    await _make_admin(rbac_app, email)

    resp = await rbac_client.delete(
        "/auth/roles/nonexistent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_assign_and_get_user_roles(rbac_client, rbac_app):
    token, email = await _register_and_login(rbac_client)
    await _make_admin(rbac_app, email)

    _, role_adapter, user_adapter = rbac_app
    await role_adapter.create_role("editor", ["posts:write"])
    user = await user_adapter.get_user_by_email(email)

    resp = await rbac_client.post(
        "/auth/roles/assign",
        json={"user_id": user["id"], "role_name": "editor"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    resp = await rbac_client.get(
        f"/auth/roles/user/{user['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "editor" in data["roles"]
    assert "posts:write" in data["permissions"]


async def test_revoke_role(rbac_client, rbac_app):
    token, email = await _register_and_login(rbac_client)
    await _make_admin(rbac_app, email)

    _, role_adapter, user_adapter = rbac_app
    await role_adapter.create_role("editor")
    user = await user_adapter.get_user_by_email(email)
    await role_adapter.assign_role(user["id"], "editor")

    resp = await rbac_client.post(
        "/auth/roles/revoke",
        json={"user_id": user["id"], "role_name": "editor"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Role revoked"


async def test_get_my_roles(rbac_client, rbac_app):
    token, email = await _register_and_login(rbac_client)
    await _make_admin(rbac_app, email)

    resp = await rbac_client.get(
        "/auth/roles/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "admin" in data["roles"]


async def test_add_permissions(rbac_client, rbac_app):
    token, email = await _register_and_login(rbac_client)
    await _make_admin(rbac_app, email)

    _, role_adapter, _ = rbac_app
    await role_adapter.create_role("editor", ["posts:read"])

    resp = await rbac_client.post(
        "/auth/roles/editor/permissions",
        json={"permissions": ["posts:write"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    role = await role_adapter.get_role("editor")
    assert "posts:write" in role["permissions"]


async def test_remove_permissions(rbac_client, rbac_app):
    token, email = await _register_and_login(rbac_client)
    await _make_admin(rbac_app, email)

    _, role_adapter, _ = rbac_app
    await role_adapter.create_role("editor", ["posts:read", "posts:write"])

    # httpx delete() doesn't support json=, so use request()
    resp = await rbac_client.request(
        "DELETE",
        "/auth/roles/editor/permissions",
        json={"permissions": ["posts:write"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    role = await role_adapter.get_role("editor")
    assert "posts:write" not in role["permissions"]
    assert "posts:read" in role["permissions"]


async def test_unauthenticated(rbac_client):
    resp = await rbac_client.get("/auth/roles")
    assert resp.status_code == 401
