# FastAuth

[![PyPI](https://img.shields.io/pypi/v/sreekarnv-fastauth)](https://pypi.org/project/sreekarnv-fastauth/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/sreekarnv/fastauth/actions/workflows/ci.yml/badge.svg)](https://github.com/sreekarnv/fastauth/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/sreekarnv/fastauth/branch/main/graph/badge.svg)](https://codecov.io/gh/sreekarnv/fastauth)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)

**NextAuth-inspired pluggable authentication for FastAPI.**

FastAuth gives you a complete auth system — credentials, OAuth, passkeys (WebAuthn), magic links, email verification, password reset, RBAC, and JWT — without locking you into any particular database or ORM.

---

## Features

- **Multiple providers** — email/password, magic links, Google OAuth, GitHub OAuth, passkeys (WebAuthn)
- **Pluggable adapters** — SQLAlchemy (SQLite, PostgreSQL, MySQL) or bring your own
- **JWT & database sessions** — stateless tokens or server-side sessions
- **Cookie delivery** — HttpOnly, Secure, SameSite out of the box
- **Email flows** — verification, password reset, and magic links with customizable transports
- **Custom email templates** — drop Jinja2 templates into any directory; unoverridden templates fall back to built-ins
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
| `webauthn` | py-webauthn (passkeys / FIDO2) |
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
auth.mount(app)  # registers /auth/register, /auth/login, /auth/logout, …

@app.get("/dashboard")
async def dashboard(user=Depends(require_auth)):
    return {"hello": user["email"]}
```

```bash
uvicorn main:app --reload
```

---

## Magic Links

Passwordless sign-in with a one-time link sent to the user's email. No password required — unknown emails are auto-registered on first use.

```python
from fastauth.providers.magic_links import MagicLinksProvider
from fastauth.email_transports.smtp import SMTPTransport

auth = FastAuth(FastAuthConfig(
    ...
    providers=[MagicLinksProvider()],
    token_adapter=adapter.token,
    email_transport=SMTPTransport(...),
    base_url="https://your-app.com",
))
```

```bash
pip install "sreekarnv-fastauth[standard,email]"
```

See the [Magic Links guide](https://sreekarnv.github.io/fastauth/guides/magic-links/) and [example app](./examples/magic_link/).

---

## Passkeys (WebAuthn)

Add Touch ID, Face ID, and Windows Hello sign-in with one extra import:

```python
from fastauth.providers.passkey import PasskeyProvider
from fastauth.session_backends.memory import MemorySessionBackend

auth = FastAuth(FastAuthConfig(
    ...
    providers=[
        CredentialsProvider(),
        PasskeyProvider(rp_id="example.com", rp_name="My App", origin="https://example.com"),
    ],
    passkey_adapter=adapter.passkey,
    passkey_state_store=MemorySessionBackend(),
))
```

```bash
pip install "sreekarnv-fastauth[standard,webauthn]"
```

See the [Passkeys guide](https://sreekarnv.github.io/fastauth/guides/passkeys/) and [example app](./examples/passkeys/).

---

## Custom Email Templates

Drop Jinja2 templates into any directory to override FastAuth's built-in emails. Only the files you provide are replaced — everything else falls back to the defaults automatically.

```python
from pathlib import Path

auth = FastAuth(FastAuthConfig(
    ...
    email_template_dir=Path("my_templates/"),
))
```

| Template file | Sent when | Variables |
|---|---|---|
| `welcome.jinja2` | User registers | `name` |
| `verification.jinja2` | Email verification | `name`, `url`, `expires_in_minutes` |
| `password_reset.jinja2` | Password reset | `name`, `url`, `expires_in_minutes` |
| `email_change.jinja2` | Email change | `name`, `new_email`, `url`, `expires_in_minutes` |
| `magic_link_login.jinja2` | Magic link sign-in | `name`, `url` |

See the [example app](./examples/custom_templates/).

---

## Documentation

Full documentation at **[sreekarnv.github.io/fastauth](https://sreekarnv.github.io/fastauth)**

- [Installation](https://sreekarnv.github.io/fastauth/getting-started/installation/)
- [Quick Start](https://sreekarnv.github.io/fastauth/getting-started/quick-start/)
- [Configuration](https://sreekarnv.github.io/fastauth/getting-started/configuration/)
- [How it Works](https://sreekarnv.github.io/fastauth/concepts/how-it-works/)
- [Magic Links](https://sreekarnv.github.io/fastauth/features/magic-links/)
- [Passkeys (WebAuthn)](https://sreekarnv.github.io/fastauth/features/passkeys/)
- [Guides](https://sreekarnv.github.io/fastauth/guides/basic/)
- [API Reference](https://sreekarnv.github.io/fastauth/reference/fastauth/)

---

## License

MIT License - see [LICENSE](./LICENSE) for details.
