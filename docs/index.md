<div class="hero" markdown>
# FastAuth
  
<p class="hero__tagline">
NextAuth-inspired pluggable authentication for FastAPI.
</p>

<p class="hero__desc">
Complete auth system - credentials, OAuth, email verification, password reset, RBAC, and JWT in minutes, without locking you into any database or ORM.
</p>

[Get Started](getting-started/installation.md){ .md-button .md-button--primary }
[GitHub](https://github.com/sreekarnv/fastauth){ .md-button }
</div>

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
**Multiple Providers**
Email/password, Google OAuth, and GitHub OAuth out of the box.
</div>

<div class="feature-card" markdown>
**Pluggable Adapters**
SQLAlchemy (SQLite, PostgreSQL, MySQL) or bring your own adapter.
</div>

<div class="feature-card" markdown>
**JWT & Sessions**

Stateless tokens or server-side database sessions -> your choice.
</div>

<div class="feature-card" markdown>
**Cookie Delivery**

HttpOnly, Secure, SameSite-strict cookies with zero extra config.
</div>

<div class="feature-card" markdown>
**Email Flows**

Verification and password reset with pluggable transports (SMTP, webhook, console).
</div>

<div class="feature-card" markdown>
**RBAC**

Roles and fine-grained permissions enforced on any route via `Depends`.
</div>

<div class="feature-card" markdown>
**Event Hooks**

Intercept sign-in, sign-up, and mutate JWT payloads via a single interface.
</div>

<div class="feature-card" markdown>
**RS256 / JWKS**

Rotate signing keys and expose a JWKS endpoint for microservice architectures.
</div>

</div>

---

## Install

=== "pip"

    ```bash
    pip install "sreekarnv-fastauth[standard]"
    ```

=== "uv"

    ```bash
    uv add "sreekarnv-fastauth[standard]"
    ```

=== "poetry"

    ```bash
    poetry add "sreekarnv-fastauth[standard]"
    ```

The `standard` extra includes FastAPI, JWT (joserfc + cryptography), SQLAlchemy, and Argon2. See [Installation](getting-started/installation.md) for the full extras table.

---

## Taste of the API

```python
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.api.deps import require_auth, require_role
from fastauth.providers.credentials import CredentialsProvider

adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

auth = FastAuth(FastAuthConfig(
    secret="change-me-in-production",   # fastauth generate-secret
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

@app.get("/admin")
async def admin(user=Depends(require_role("admin"))):
    return {"message": "welcome, admin"}
```

`auth.mount(app)` registers all auth endpoints automatically. Your routes just use `Depends(require_auth)`.


<div class="next-steps" markdown>

## Next steps

- [Installation](getting-started/installation.md) — extras, drivers, optional deps
- [Quick Start](getting-started/quick-start.md) — a minimal working app in 15 lines
- [Configuration](getting-started/configuration.md) — every config field explained
- [How it Works](concepts/how-it-works.md) — architecture overview with diagrams

</div>
