from fastapi import FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import (
    MemoryRoleAdapter,
    MemoryTokenAdapter,
    MemoryUserAdapter,
)
from fastauth.config import FastAuthConfig, JWTConfig
from fastauth.providers.credentials import CredentialsProvider
from fastauth.providers.magic_links import MagicLinksProvider
from httpx import ASGITransport, AsyncClient


def _make_config(**kwargs):
    return FastAuthConfig(
        secret="test-secret",
        providers=[CredentialsProvider()],
        adapter=MemoryUserAdapter(),
        **kwargs,
    )


async def test_initialize_roles_seeds_roles():
    role_adapter = MemoryRoleAdapter()
    auth = FastAuth(
        _make_config(
            roles=[
                {"name": "admin", "permissions": ["read", "write"]},
                {"name": "member", "permissions": []},
            ]
        )
    )
    auth.role_adapter = role_adapter

    await auth.initialize_roles()

    admin = await role_adapter.get_role("admin")
    assert admin is not None
    assert set(admin["permissions"]) == {"read", "write"}

    member = await role_adapter.get_role("member")
    assert member is not None
    assert member["permissions"] == []


async def test_initialize_roles_no_op_without_role_adapter():
    auth = FastAuth(_make_config(roles=[{"name": "admin", "permissions": []}]))
    # role_adapter is None — must not raise
    await auth.initialize_roles()


async def test_initialize_roles_no_op_without_roles_config():
    role_adapter = MemoryRoleAdapter()
    auth = FastAuth(_make_config())
    auth.role_adapter = role_adapter

    await auth.initialize_roles()

    roles = await role_adapter.list_roles()
    assert roles == []


async def test_initialize_roles_idempotent():
    role_adapter = MemoryRoleAdapter()
    auth = FastAuth(_make_config(roles=[{"name": "admin", "permissions": []}]))
    auth.role_adapter = role_adapter

    await auth.initialize_roles()
    await auth.initialize_roles()

    roles = await role_adapter.list_roles()
    assert len([r for r in roles if r["name"] == "admin"]) == 1


async def test_jwks_route_registered_when_mount_called_before_initialize_jwks():
    """The bug: mount() checked self.jwks_manager (None at mount time).
    Fix: mount() checks config.jwt.jwks_enabled so the route is always
    registered when enabled, regardless of initialization order."""
    config = FastAuthConfig(
        secret="not-used-for-rs256",
        providers=[CredentialsProvider()],
        adapter=MemoryUserAdapter(),
        jwt=JWTConfig(algorithm="RS256", jwks_enabled=True),
    )
    auth = FastAuth(config)
    app = FastAPI()

    # mount FIRST (simulates real-world module-load-time usage)
    auth.mount(app)
    # initialize AFTER (simulates lifespan startup)
    await auth.initialize_jwks()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.get("/.well-known/jwks.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "keys" in data
        assert len(data["keys"]) >= 1


async def test_jwks_route_not_registered_when_disabled():
    config = FastAuthConfig(
        secret="test-secret",
        providers=[CredentialsProvider()],
        adapter=MemoryUserAdapter(),
        jwt=JWTConfig(algorithm="HS256", jwks_enabled=False),
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.get("/.well-known/jwks.json")
        assert resp.status_code == 404


async def test_register_assigns_default_role():
    user_adapter = MemoryUserAdapter()
    role_adapter = MemoryRoleAdapter()
    await role_adapter.create_role(name="member", permissions=[])

    auth = FastAuth(
        FastAuthConfig(
            secret="test-secret",
            providers=[CredentialsProvider()],
            adapter=user_adapter,
            default_role="member",
        )
    )
    auth.role_adapter = role_adapter

    app = FastAPI()
    auth.mount(app)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={"email": "new@example.com", "password": "Password123!"},
        )
        assert resp.status_code == 201

    user = await user_adapter.get_user_by_email("new@example.com")
    assert user is not None
    roles = await role_adapter.get_user_roles(user["id"])
    assert "member" in roles


async def test_register_no_role_assigned_without_default_role():
    user_adapter = MemoryUserAdapter()
    role_adapter = MemoryRoleAdapter()

    auth = FastAuth(
        FastAuthConfig(
            secret="test-secret",
            providers=[CredentialsProvider()],
            adapter=user_adapter,
            # default_role not set
        )
    )
    auth.role_adapter = role_adapter

    app = FastAPI()
    auth.mount(app)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={"email": "new@example.com", "password": "Password123!"},
        )
        assert resp.status_code == 201

    user = await user_adapter.get_user_by_email("new@example.com")
    assert user is not None
    roles = await role_adapter.get_user_roles(user["id"])
    assert roles == []


async def test_register_no_role_assigned_without_role_adapter():
    user_adapter = MemoryUserAdapter()

    auth = FastAuth(
        FastAuthConfig(
            secret="test-secret",
            providers=[CredentialsProvider()],
            adapter=user_adapter,
            default_role="member",
            # role_adapter not set on auth instance
        )
    )

    app = FastAPI()
    auth.mount(app)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={"email": "new@example.com", "password": "Password123!"},
        )
        # should succeed without error even though role_adapter is absent
        assert resp.status_code == 201


async def test_magic_link_signup_assigns_default_role():
    user_adapter = MemoryUserAdapter()
    token_adapter = MemoryTokenAdapter()
    role_adapter = MemoryRoleAdapter()
    await role_adapter.create_role(name="member", permissions=[])

    config = FastAuthConfig(
        secret="test-secret",
        providers=[MagicLinksProvider()],
        adapter=user_adapter,
        token_adapter=token_adapter,
        default_role="member",
    )
    auth = FastAuth(config)
    auth.role_adapter = role_adapter

    app = FastAPI()
    auth.mount(app)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/magic-links/login", json={"email": "new@example.com"}
        )
        assert resp.status_code == 200

    user = await user_adapter.get_user_by_email("new@example.com")
    assert user is not None
    roles = await role_adapter.get_user_roles(user["id"])
    assert "member" in roles
