# Guide: Basic App

This guide walks through the full `examples/basic` application — a FastAPI app with email/password authentication, email verification, and RBAC.

## What we're building

- Email + password sign-up and sign-in
- Email verification (printed to console in dev)
- Protected routes requiring authentication, roles, and permissions
- SQLite database via SQLAlchemy

## Full source

```python title="examples/basic/main.py"
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.api.deps import require_auth, require_permission, require_role
from fastauth.email_transports.console import ConsoleTransport
from fastauth.providers.credentials import CredentialsProvider
from fastauth.types import UserData

adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

config = FastAuthConfig(
    secret="super-secret-change-me-in-production",
    providers=[CredentialsProvider()],
    adapter=adapter.user,
    token_adapter=adapter.token,
    email_transport=ConsoleTransport(),
    base_url="http://localhost:8000",
)

auth = FastAuth(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    yield


app = FastAPI(title="FastAuth Basic Example", lifespan=lifespan)
auth.mount(app)


@app.get("/dashboard")
async def dashboard(user: UserData = Depends(require_auth)):
    return {"message": f"Hello, {user['email']}", "user": user}


@app.get("/admin")
async def admin_area(user: UserData = Depends(require_role("admin"))):
    return {"message": "Welcome, admin", "user_id": user["id"]}


@app.get("/reports")
async def reports(user: UserData = Depends(require_permission("reports:read"))):
    return {"message": "Here are your reports", "user_id": user["id"]}
```

## Step-by-step walkthrough

### 1. Create the adapter

```python
adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")
```

`SQLAlchemyAdapter` wraps an async SQLAlchemy engine. We use SQLite here — swap the URL for PostgreSQL in production. The `.user` and `.token` properties return the adapter implementations we need.

### 2. Configure FastAuth

```python
config = FastAuthConfig(
    secret="...",                         # HMAC signing secret
    providers=[CredentialsProvider()],    # email + password
    adapter=adapter.user,                 # reads/writes users
    token_adapter=adapter.token,          # stores verification tokens
    email_transport=ConsoleTransport(),   # prints emails to stdout
    base_url="http://localhost:8000",     # used in email links
)
```

`ConsoleTransport` is great for development — it prints the verification link to the terminal instead of sending an email.

### 3. Mount routes

```python
auth.mount(app)
```

This registers all `/auth/*` endpoints. Open `/docs` after starting the app to see the interactive documentation.

### 4. Protect your own routes

```python
@app.get("/dashboard")
async def dashboard(user: UserData = Depends(require_auth)):
    return {"message": f"Hello, {user['email']}"}
```

`require_auth` extracts and validates the JWT from the `Authorization` header (or cookie). If there's no valid token, it returns HTTP 401.

```python
@app.get("/admin")
async def admin_area(user: UserData = Depends(require_role("admin"))):
    ...
```

`require_role("admin")` first calls `require_auth`, then checks that the user has the `admin` role.

## Run it

```bash
pip install "sreekarnv-fastauth[standard]"
uvicorn main:app --reload
```

Then visit `http://localhost:8000/docs`.

## Generating a production secret

```bash
fastauth generate-secret
```

Paste the output into your environment variables, never into source code.
