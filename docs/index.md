<div class="fa-hero" markdown>

<p class="fa-hero__eyebrow">v0.5.2 &nbsp;·&nbsp; Python 3.11+ &nbsp;·&nbsp; FastAPI</p>

# FastAuth

<p class="fa-hero__tagline">NextAuth-inspired pluggable authentication for FastAPI.</p>

<p class="fa-hero__desc">Complete auth — credentials, OAuth, email verification, password reset, RBAC, and JWT in minutes. No ORM lock-in.</p>

<div class="fa-hero__cta">
<a href="getting-started/installation" class="fa-btn fa-btn--primary">Get started →</a>
<a href="https://github.com/sreekarnv/fastauth" class="fa-btn fa-btn--ghost"><svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 0C5.37 0 0 5.373 0 12c0 5.303 3.438 9.8 8.207 11.387.6.113.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/></svg>GitHub</a>
</div>

</div>

<div class="fa-features">

<div class="fa-feature">
<span class="fa-feature__num">01</span>
<p class="fa-feature__name">Multiple Providers</p>
<p class="fa-feature__desc">Email/password, Google OAuth, and GitHub OAuth out of the box.</p>
</div>

<div class="fa-feature">
<span class="fa-feature__num">02</span>
<p class="fa-feature__name">Pluggable Adapters</p>
<p class="fa-feature__desc">SQLAlchemy (SQLite, PostgreSQL, MySQL) or bring your own.</p>
</div>

<div class="fa-feature">
<span class="fa-feature__num">03</span>
<p class="fa-feature__name">JWT & Sessions</p>
<p class="fa-feature__desc">Stateless tokens or server-side sessions — your choice.</p>
</div>

<div class="fa-feature">
<span class="fa-feature__num">04</span>
<p class="fa-feature__name">Cookie Delivery</p>
<p class="fa-feature__desc">HttpOnly, Secure, SameSite cookies with zero extra config.</p>
</div>

<div class="fa-feature">
<span class="fa-feature__num">05</span>
<p class="fa-feature__name">Email Flows</p>
<p class="fa-feature__desc">Verification and password reset with pluggable transports.</p>
</div>

<div class="fa-feature">
<span class="fa-feature__num">06</span>
<p class="fa-feature__name">RBAC</p>
<p class="fa-feature__desc">Roles and permissions enforced on any route via <code>Depends</code>.</p>
</div>

<div class="fa-feature">
<span class="fa-feature__num">07</span>
<p class="fa-feature__name">Event Hooks</p>
<p class="fa-feature__desc">Intercept sign-in, sign-up, and mutate JWT payloads.</p>
</div>

<div class="fa-feature">
<span class="fa-feature__num">08</span>
<p class="fa-feature__name">RS256 / JWKS</p>
<p class="fa-feature__desc">Rotate signing keys, expose a JWKS endpoint for microservices.</p>
</div>

</div>


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
auth.mount(app)  # registers /auth/register, /auth/login, /auth/logout, …

@app.get("/dashboard")
async def dashboard(user=Depends(require_auth)):
    return {"hello": user["email"]}

@app.get("/admin")
async def admin(user=Depends(require_role("admin"))):
    return {"message": "welcome, admin"}
```

`auth.mount(app)` registers all auth endpoints automatically. Your routes just use `Depends(require_auth)`.

<div class="fa-next-steps" markdown>

---

## Next steps

- [Installation](getting-started/installation.md) — extras, drivers, optional deps
- [Quick Start](getting-started/quick-start.md) — a minimal working app in 15 lines
- [Configuration](getting-started/configuration.md) — every config field explained
- [How it Works](concepts/how-it-works.md) — architecture overview with diagrams

</div>
