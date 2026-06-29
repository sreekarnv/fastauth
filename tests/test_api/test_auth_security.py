from fastapi import FastAPI
from fastauth import FastAuth
from fastauth.adapters.memory import MemoryTokenAdapter, MemoryUserAdapter
from fastauth.config import FastAuthConfig, JWTConfig, PasswordConfig
from fastauth.email_transports.console import ConsoleTransport
from fastauth.providers.credentials import CredentialsProvider
from httpx import ASGITransport, AsyncClient

_STRICT = PasswordConfig(
    min_length=12,
    require_uppercase=True,
    require_lowercase=True,
    require_digit=True,
    require_special=True,
)


def _build_app(password: PasswordConfig | None = None, hooks=None):
    user_adapter = MemoryUserAdapter()
    token_adapter = MemoryTokenAdapter()
    config = FastAuthConfig(
        secret="this-is-a-test-secret-32-bytes!!",
        providers=[CredentialsProvider()],
        adapter=user_adapter,
        token_adapter=token_adapter,
        jwt=JWTConfig(algorithm="HS256"),
        password=password or PasswordConfig(),
        email_transport=ConsoleTransport(),
        base_url="http://localhost:8000",
        hooks=hooks,
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    return app, user_adapter, token_adapter


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _extract_token(capsys) -> str:
    out = capsys.readouterr().out
    for line in out.splitlines():
        if "token=" in line:
            tail = line.split("token=", 1)[1]
            raw = ""
            for ch in tail:
                if ch.isalnum() or ch in "-_.":
                    raw += ch
                else:
                    break
            if raw:
                return raw
    raise AssertionError(f"Could not find token= in console output:\n{out}")


async def test_change_password_revokes_old_refresh_jti():
    app, _, _ = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={"email": "sec@example.com", "password": "Pass123#", "name": "T"},
        )
        assert resp.status_code == 201
        access = resp.json()["access_token"]
        refresh = resp.json()["refresh_token"]

        resp = await c.post(
            "/auth/account/change-password",
            json={"current_password": "Pass123#", "new_password": "NewPass456#"},
            headers=_auth(access),
        )
        assert resp.status_code == 200

        resp = await c.post("/auth/refresh", json={"refresh_token": refresh})
        assert resp.status_code == 401


async def test_weak_password_on_change_rejected():
    app, _, _ = _build_app(password=_STRICT)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={
                "email": "wk@example.com",
                "password": "InitialPass123!@#",
                "name": "T",
            },
        )
        assert resp.status_code == 201
        access = resp.json()["access_token"]

        resp = await c.post(
            "/auth/account/change-password",
            json={
                "current_password": "InitialPass123!@#",
                "new_password": "short",
            },
            headers=_auth(access),
        )
        assert resp.status_code == 400


async def test_strong_password_on_change_succeeds():
    app, _, _ = _build_app(password=_STRICT)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={
                "email": "ok@example.com",
                "password": "InitialPass123!@#",
                "name": "T",
            },
        )
        assert resp.status_code == 201
        access = resp.json()["access_token"]

        resp = await c.post(
            "/auth/account/change-password",
            json={
                "current_password": "InitialPass123!@#",
                "new_password": "SuperSafe123!@#",
            },
            headers=_auth(access),
        )
        assert resp.status_code == 200


async def test_weak_password_on_reset_rejected(capsys):
    app, _, _ = _build_app(password=_STRICT)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post(
            "/auth/register",
            json={
                "email": "rst@example.com",
                "password": "InitialPass123!@#",
                "name": "T",
            },
        )
        await c.post("/auth/forgot-password", json={"email": "rst@example.com"})

        token = _extract_token(capsys)

        resp = await c.post(
            "/auth/reset-password",
            json={"token": token, "new_password": "short"},
        )
        assert resp.status_code == 400


async def test_strong_password_on_reset_succeeds(capsys):
    app, _, _ = _build_app(password=_STRICT)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post(
            "/auth/register",
            json={
                "email": "rstok@example.com",
                "password": "InitialPass123!@#",
                "name": "T",
            },
        )
        await c.post("/auth/forgot-password", json={"email": "rstok@example.com"})

        token = _extract_token(capsys)

        resp = await c.post(
            "/auth/reset-password",
            json={"token": token, "new_password": "SuperSafe123!@#"},
        )
        assert resp.status_code == 200


async def test_reset_password_revokes_existing_refresh_jti(capsys):
    """Regression: after /auth/reset-password, an old refresh token (and any
    other outstanding refresh_jti) must be rejected."""
    app, _, _ = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={
                "email": "reset-revoke@example.com",
                "password": "InitialPass123!@#",
                "name": "T",
            },
        )
        assert resp.status_code == 201
        old_refresh = resp.json()["refresh_token"]

        await c.post(
            "/auth/forgot-password", json={"email": "reset-revoke@example.com"}
        )
        reset_token = _extract_token(capsys)
        resp = await c.post(
            "/auth/reset-password",
            json={"token": reset_token, "new_password": "BrandNewPass456!@#"},
        )
        assert resp.status_code == 200

        resp = await c.post("/auth/refresh", json={"refresh_token": old_refresh})
        assert resp.status_code == 401


async def test_credentials_login_blocked_by_allow_signin():
    from fastauth.core.protocols import EventHooks
    from fastauth.types import UserData

    class BlockingHooks(EventHooks):
        async def allow_signin(self, user: UserData, provider: str) -> bool:
            return False

    app, _, _ = _build_app(hooks=BlockingHooks())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post(
            "/auth/register",
            json={"email": "cred@example.com", "password": "Pass123#", "name": "T"},
        )
        resp = await c.post(
            "/auth/login",
            json={"email": "cred@example.com", "password": "Pass123#"},
        )
        assert resp.status_code == 403
        assert "access_token" not in resp.cookies
        body = resp.json()
        assert "access_token" not in body


async def test_credentials_login_proceeds_when_allow_signin_allows():
    from fastauth.core.protocols import EventHooks
    from fastauth.types import UserData

    class AllowHooks(EventHooks):
        async def allow_signin(self, user: UserData, provider: str) -> bool:
            return True

    app, _, _ = _build_app(hooks=AllowHooks())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post(
            "/auth/register",
            json={"email": "cred2@example.com", "password": "Pass123#", "name": "T"},
        )
        resp = await c.post(
            "/auth/login",
            json={"email": "cred2@example.com", "password": "Pass123#"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()


async def test_logout_revokes_refresh_jti():
    from fastauth.core.tokens import decode_token

    app, _, _ = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={"email": "lo@example.com", "password": "Pass123#", "name": "T"},
        )
        assert resp.status_code == 201
        refresh = resp.json()["refresh_token"]
        access = resp.json()["access_token"]

        resp = await c.post(
            "/auth/logout", headers={"Authorization": f"Bearer {access}"}
        )
        assert resp.status_code == 200

        claims = decode_token(
            refresh,
            app.state.fastauth.config,
            app.state.fastauth.jwks_manager,
        )
        jti = claims["jti"]
        stored = await app.state.fastauth.config.token_adapter.get_token(
            jti, "refresh_jti"
        )
        assert stored is None

        resp = await c.post("/auth/refresh", json={"refresh_token": refresh})
        assert resp.status_code == 401


async def test_refresh_replay_revokes_token_family():
    """Replay an already-used refresh token — the whole refresh-token family
    for the user must be revoked (a re-use of the rotated refresh token
    must also be rejected, since the first rotation already consumed the
    original JTI)."""

    app, _, _ = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={"email": "replay@example.com", "password": "Pass123#", "name": "T"},
        )
        assert resp.status_code == 201
        first_refresh = resp.json()["refresh_token"]

        # First rotation succeeds
        resp = await c.post("/auth/refresh", json={"refresh_token": first_refresh})
        assert resp.status_code == 200
        second_refresh = resp.json()["refresh_token"]
        assert second_refresh != first_refresh

        # Replaying the first (consumed) refresh token must fail AND
        # revoke the family so even the freshly issued token is invalidated.
        resp = await c.post("/auth/refresh", json={"refresh_token": first_refresh})
        assert resp.status_code == 401

        resp = await c.post("/auth/refresh", json={"refresh_token": second_refresh})
        assert resp.status_code == 401


async def test_refresh_concurrent_only_one_wins():
    """Two concurrent refresh requests for the same token — only one
    consumer should succeed, the other should be treated as a replay and
    rejected."""
    import asyncio

    app, _, _ = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={"email": "race@example.com", "password": "Pass123#", "name": "T"},
        )
        assert resp.status_code == 201
        refresh = resp.json()["refresh_token"]

        async def attempt():
            return await c.post("/auth/refresh", json={"refresh_token": refresh})

        results = await asyncio.gather(attempt(), attempt(), attempt())
        statuses = sorted(r.status_code for r in results)
        # Exactly one rotation must succeed; the others are rejected as
        # either invalid-replay or already-revoked.
        assert statuses[0] == 200
        assert all(s == 401 for s in statuses[1:])


async def test_logout_without_token_adapter_succeeds():
    from fastapi import FastAPI as _FastAPI
    from fastauth import FastAuth as _FastAuth
    from fastauth.adapters.memory import MemoryUserAdapter

    user_adapter = MemoryUserAdapter()
    config = FastAuthConfig(
        secret="this-is-a-test-secret-32-bytes!!",
        providers=[CredentialsProvider()],
        adapter=user_adapter,
        jwt=JWTConfig(algorithm="HS256"),
    )
    auth = _FastAuth(config)
    app = _FastAPI()
    auth.mount(app)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={"email": "nta@example.com", "password": "Pass123#", "name": "T"},
        )
        assert resp.status_code == 201
        access = resp.json()["access_token"]
        resp = await c.post(
            "/auth/logout", headers={"Authorization": f"Bearer {access}"}
        )
        assert resp.status_code == 200


async def test_register_weak_password_returns_400():
    from fastauth.config import SecurityConfig

    user_adapter = MemoryUserAdapter()
    token_adapter = MemoryTokenAdapter()
    config = FastAuthConfig(
        secret="this-is-a-test-secret-32-bytes!!",
        providers=[CredentialsProvider()],
        adapter=user_adapter,
        token_adapter=token_adapter,
        jwt=JWTConfig(algorithm="HS256"),
        security=SecurityConfig(max_login_attempts=5, lockout_duration=300),
        password=PasswordConfig(
            min_length=12,
            require_uppercase=True,
            require_lowercase=True,
            require_digit=True,
            require_special=True,
        ),
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post(
            "/auth/register",
            json={"email": "weak@example.com", "password": "short", "name": "T"},
        )
        assert resp.status_code == 400


async def test_security_config_used_for_lockout():
    from fastauth.config import SecurityConfig

    user_adapter = MemoryUserAdapter()
    token_adapter = MemoryTokenAdapter()
    config = FastAuthConfig(
        secret="this-is-a-test-secret-32-bytes!!",
        providers=[CredentialsProvider()],
        adapter=user_adapter,
        token_adapter=token_adapter,
        jwt=JWTConfig(algorithm="HS256"),
        security=SecurityConfig(max_login_attempts=2, lockout_duration=60),
    )
    auth = FastAuth(config)
    app = FastAPI()
    auth.mount(app)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        await c.post(
            "/auth/register",
            json={"email": "lock@example.com", "password": "Pass123#", "name": "T"},
        )
        for _ in range(2):
            resp = await c.post(
                "/auth/login",
                json={"email": "lock@example.com", "password": "wrong"},
            )
            assert resp.status_code == 401
        resp = await c.post(
            "/auth/login",
            json={"email": "lock@example.com", "password": "Pass123#"},
        )
        assert resp.status_code == 401
