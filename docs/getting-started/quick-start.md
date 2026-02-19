# Quick Start

This page walks you through a minimal working FastAuth application — email/password sign-up and sign-in with a SQLite database.

## Prerequisites

```bash
pip install "sreekarnv-fastauth[standard]"
```

## The code

```python title="main.py"
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.api.deps import require_auth
from fastauth.providers.credentials import CredentialsProvider
from fastauth.types import UserData

# 1. Create the adapter (manages database tables)
adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

# 2. Configure FastAuth
auth = FastAuth(FastAuthConfig(
    secret="change-me-in-production",  # generate with: fastauth generate-secret
    providers=[CredentialsProvider()],
    adapter=adapter.user,
    token_adapter=adapter.token,       # needed for email verification tokens
))

# 3. Create the FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()      # creates tables on startup
    yield

app = FastAPI(lifespan=lifespan)

# 4. Mount FastAuth — this registers all /auth/* routes
auth.mount(app)

# 5. Protect your own routes
@app.get("/me")
async def me(user: UserData = Depends(require_auth)):
    return user
```

Run it:

```bash
uvicorn main:app --reload
```

## What routes are registered?

After `auth.mount(app)`, the following endpoints are available at `/auth`:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/signup` | Register a new user |
| `POST` | `/auth/signin` | Sign in, receive access + refresh tokens |
| `POST` | `/auth/signout` | Invalidate the current session |
| `POST` | `/auth/refresh` | Exchange a refresh token for a new access token |
| `GET`  | `/auth/me` | Return the current authenticated user |

## Try it out

```bash
# Sign up
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "s3cur3!"}'

# Sign in — note the access_token in the response
curl -X POST http://localhost:8000/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "s3cur3!"}'

# Call a protected route
curl http://localhost:8000/me \
  -H "Authorization: Bearer <your_access_token>"
```

## Next steps

- [Configuration](configuration.md) — learn every config option
- [Providers](../providers/credentials.md) — customise the credentials provider
- [Features → Cookie Delivery](../features/cookies.md) — use HttpOnly cookies instead of JSON tokens
- [Guides → Basic App](../guides/basic.md) — a full walkthrough with RBAC and email verification
