# Guide: Testing

FastAuth provides an in-memory adapter that makes it easy to write fast, database-free tests for your application's auth flows.

## Setup

Install test dependencies:

```bash
pip install "sreekarnv-fastauth[standard]" pytest pytest-asyncio httpx
```

## Using the Memory adapter

`MemoryUserAdapter`, `MemoryTokenAdapter`, `MemoryRoleAdapter`, and `MemoryOAuthAccountAdapter` store everything in Python dicts — no database required.

```python title="tests/conftest.py"
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.memory import (
    MemoryTokenAdapter,
    MemoryUserAdapter,
)
from fastauth.email_transports.console import ConsoleTransport
from fastauth.providers.credentials import CredentialsProvider


def make_app() -> FastAPI:
    user_adapter = MemoryUserAdapter()
    token_adapter = MemoryTokenAdapter()

    config = FastAuthConfig(
        secret="test-secret-at-least-32-characters-long",
        providers=[CredentialsProvider()],
        adapter=user_adapter,
        token_adapter=token_adapter,
        email_transport=ConsoleTransport(),
        base_url="http://testserver",
    )

    auth = FastAuth(config)

    app = FastAPI()
    auth.mount(app)
    return app


@pytest.fixture
def app():
    return make_app()


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c
```

## Writing tests

### Test registration and login

```python title="tests/test_auth.py"
import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register
    res = await client.post("/auth/register", json={
        "email": "alice@example.com",
        "password": "s3cur3P@ss!",
    })
    assert res.status_code == 201
    assert "access_token" in res.json()
    assert res.json()["token_type"] == "bearer"

    # Login
    res = await client.post("/auth/login", json={
        "email": "alice@example.com",
        "password": "s3cur3P@ss!",
    })
    assert res.status_code == 200
    tokens = res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


@pytest.mark.asyncio
async def test_wrong_password(client):
    await client.post("/auth/register", json={
        "email": "bob@example.com",
        "password": "correct-pass",
    })

    res = await client.post("/auth/login", json={
        "email": "bob@example.com",
        "password": "wrong-pass",
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_email(client):
    payload = {"email": "carol@example.com", "password": "pass"}
    await client.post("/auth/register", json=payload)

    res = await client.post("/auth/register", json=payload)
    assert res.status_code == 409
```

### Test protected routes

```python
@pytest.mark.asyncio
async def test_protected_route(client, app):
    from fastapi import Depends
    from fastauth.api.deps import require_auth

    @app.get("/me-test")
    async def me_test(user=Depends(require_auth)):
        return {"email": user["email"]}

    # Without token → 401
    res = await client.get("/me-test")
    assert res.status_code == 401

    # Register and get token
    await client.post("/auth/register", json={
        "email": "dave@example.com", "password": "pass"
    })
    login = await client.post("/auth/login", json={
        "email": "dave@example.com", "password": "pass"
    })
    token = login.json()["access_token"]

    # With token → 200
    res = await client.get("/me-test", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "dave@example.com"
```

### Test token refresh

```python
@pytest.mark.asyncio
async def test_token_refresh(client):
    await client.post("/auth/register", json={
        "email": "eve@example.com", "password": "pass"
    })
    login = await client.post("/auth/login", json={
        "email": "eve@example.com", "password": "pass"
    })
    refresh_token = login.json()["refresh_token"]

    res = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    assert "access_token" in res.json()
```

### Test with RBAC

```python title="tests/test_rbac.py"
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.memory import MemoryRoleAdapter, MemoryTokenAdapter, MemoryUserAdapter
from fastauth.api.deps import require_role
from fastauth.providers.credentials import CredentialsProvider


@pytest.fixture
async def rbac_client():
    user_adapter = MemoryUserAdapter()
    token_adapter = MemoryTokenAdapter()
    role_adapter = MemoryRoleAdapter()

    config = FastAuthConfig(
        secret="test-secret-at-least-32-characters-long",
        providers=[CredentialsProvider()],
        adapter=user_adapter,
        token_adapter=token_adapter,
        roles=[{"name": "admin", "permissions": ["users:delete"]}],
    )

    auth = FastAuth(config)
    auth.role_adapter = role_adapter

    app = FastAPI()
    auth.mount(app)

    @app.get("/admin-only")
    async def admin_only(user=Depends(require_role("admin"))):
        return {"ok": True}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client, auth


@pytest.mark.asyncio
async def test_role_required(rbac_client):
    client, auth = rbac_client

    # Register a user
    res = await client.post("/auth/register", json={
        "email": "frank@example.com", "password": "pass"
    })
    token = res.json()["access_token"]

    # Without admin role → 403
    res = await client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
```

## Tips

- **Isolate state per test** — create a fresh `make_app()` in each test or fixture to avoid state leaking between tests.
- **Use `pytest-asyncio`** with `asyncio_mode = "auto"` in `pytest.ini` to avoid boilerplate `@pytest.mark.asyncio` decorators.
- **Check the `ConsoleTransport` output** — email verification tokens are printed to stdout during tests. Capture them with `capsys` if needed.
- **Switch to a real DB** for integration tests — swap `MemoryUserAdapter` for `SQLAlchemyAdapter` with an in-memory SQLite URL (`sqlite+aiosqlite:///:memory:`).
