# FastAuth

[![PyPI](https://img.shields.io/pypi/v/sreekarnv-fastauth)](https://pypi.org/project/sreekarnv-fastauth/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/sreekarnv/fastauth/actions/workflows/ci.yml/badge.svg)](https://github.com/sreekarnv/fastauth/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/sreekarnv/fastauth/branch/main/graph/badge.svg)](https://codecov.io/gh/sreekarnv/fastauth)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)

**NextAuth-inspired pluggable authentication for FastAPI.**

FastAuth gives you a complete auth system — credentials, OAuth, email verification, password reset, RBAC, and JWT — without locking you into any particular database or ORM.

---

## Features

- **Multiple providers** — email/password, Google OAuth, GitHub OAuth
- **Pluggable adapters** — SQLAlchemy (SQLite, PostgreSQL, MySQL) or bring your own
- **JWT & database sessions** — stateless tokens or server-side sessions
- **Cookie delivery** — HttpOnly, Secure, SameSite out of the box
- **Email flows** — verification and password reset with customizable transports
- **RBAC** — roles and fine-grained permissions on any route
- **Event hooks** — intercept sign-in/sign-up and modify JWT payloads
- **RS256 / JWKS** — rotate keys and expose a JWKS endpoint for microservices
- **CLI** — scaffold a project, check dependencies, generate secrets

---

## Install

```bash
pip install "sreekarnv-fastauth[standard]"
```

| Extra | Includes |
|-------|----------|
| `standard` | FastAPI, JWT (joserfc), SQLAlchemy, Argon2 |
| `oauth` | httpx (Google, GitHub OAuth) |
| `email` | aiosmtplib, Jinja2 |
| `redis` | redis-py async |
| `postgresql` | asyncpg |
| `cli` | typer, rich |
| `all` | everything |

---

## Quick start

```python
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.api.deps import require_auth
from fastauth.providers.credentials import CredentialsProvider

adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

auth = FastAuth(FastAuthConfig(
    secret="change-me",           # fastauth generate-secret
    providers=[CredentialsProvider()],
    adapter=adapter.user,
    token_adapter=adapter.token,
))

@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    yield

app = FastAPI(lifespan=lifespan)
auth.mount(app)  # registers /auth/signup, /auth/signin, /auth/signout, …

@app.get("/dashboard")
async def dashboard(user=Depends(require_auth)):
    return {"hello": user["email"]}
```

```bash
uvicorn main:app --reload
```

---

## Documentation

Full documentation at **[sreekarnv.github.io/fastauth](https://sreekarnv.github.io/fastauth)**

- [Installation](https://sreekarnv.github.io/fastauth/getting-started/installation/)
- [Quick Start](https://sreekarnv.github.io/fastauth/getting-started/quick-start/)
- [Configuration](https://sreekarnv.github.io/fastauth/getting-started/configuration/)
- [How it Works](https://sreekarnv.github.io/fastauth/concepts/how-it-works/)
- [Guides](https://sreekarnv.github.io/fastauth/guides/basic/)
- [API Reference](https://sreekarnv.github.io/fastauth/api/fastauth/)

---

## License

MIT
