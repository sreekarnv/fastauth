# Production Checklist

A checklist of everything you should review before deploying FastAuth to production.

## Secrets

- [ ] **Generate a strong secret**: `fastauth generate-secret` — use the output, don't make one up
- [ ] **Store secrets in environment variables** — never commit secrets to source control
- [ ] **Use different secrets per environment** (dev, staging, prod)
- [ ] **For RS256**: keep the private key in a secrets manager (AWS Secrets Manager, Vault, etc.)

```python
import os

config = FastAuthConfig(
    secret=os.environ["FASTAUTH_SECRET"],
    ...
)
```

## HTTPS

- [ ] **All traffic over HTTPS** — never serve auth endpoints over plain HTTP in production
- [ ] **Set `cookie_secure=True`** (it defaults to `True` when `debug=False`)
- [ ] **Update `base_url`** to your HTTPS domain for correct email links

```python
config = FastAuthConfig(
    ...,
    base_url="https://api.example.com",
    debug=False,  # default — ensures Secure cookies
)
```

## Database

- [ ] **Use PostgreSQL** (or another production DB) instead of SQLite
- [ ] **Use Alembic for migrations** instead of `create_tables()` in production
- [ ] **Set up connection pooling** (`pool_size`, `max_overflow` on `create_async_engine`)

```python
from sqlalchemy.ext.asyncio import create_async_engine
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter

engine = create_async_engine(
    os.environ["DATABASE_URL"],
    pool_size=10,
    max_overflow=20,
)
adapter = SQLAlchemyAdapter(engine=engine)
```

## Ephemeral storage

- [ ] **Use Redis** for `oauth_state_store` — memory backends don't survive restarts or scale across instances
- [ ] **Treat `session_backend` as reserved** — `session_strategy="database"` is not wired into auth routes today, which always issue JWT token pairs

```python
from fastauth.session_backends.redis import RedisSessionBackend

backend = RedisSessionBackend(url=os.environ["REDIS_URL"])
config = FastAuthConfig(
    ...,
    oauth_state_store=backend,
    # session_backend=backend,  # reserved for future database-session auth
)
```

For user-visible session listing and revocation, configure `auth.session_adapter` instead; this powers `/auth/sessions` and is independent of `session_strategy`.

## Cookies

- [ ] **Set `cookie_secure=True`** (default when not in debug mode)
- [ ] **Set `cookie_httponly=True`** (default) — prevents JS access
- [ ] **Review `cookie_samesite`** — `"lax"` for same-origin apps, `"none"` for cross-origin SPAs
- [ ] **Set `cookie_domain`** if you share cookies across subdomains
- [ ] **Keep `csrf_enabled=True`** for cookie delivery — browser clients must send the readable `csrf_token` cookie value as `X-CSRF-Token` on `POST`, `PUT`, `PATCH`, and `DELETE`

Cookie mode is protected by a double-submit CSRF token. FastAuth sets `access_token` and `refresh_token` as HttpOnly cookies, plus a readable `csrf_token` cookie. Your frontend should include credentials and copy that cookie into the `X-CSRF-Token` header for unsafe requests:

```javascript
await fetch("https://api.example.com/auth/account/profile", {
  method: "PUT",
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
    "X-CSRF-Token": csrfTokenFromCookie,
  },
  body: JSON.stringify({name}),
})
```

Requests authenticated with `Authorization: Bearer <token>` are checked before cookies and do not require a CSRF header.

## Token lifetimes

- [ ] **Short access token TTL** — 15 minutes (default) is a good baseline
- [ ] **Consider shorter TTLs** for high-security applications (5 minutes)
- [ ] **Rotate refresh tokens** on every refresh — FastAuth records each refresh token JTI in `token_adapter` and rejects reused JTIs. Configure `token_adapter` for refresh-token rotation; without it, refresh tokens are stateless and remain valid until expiry.

## CORS

- [ ] **Set `cors_origins`** to only the domains that need access

```python
config = FastAuthConfig(
    ...,
    cors_origins=["https://app.example.com"],
)
```

## Email

- [ ] **Use SMTP or a transactional email service** (SendGrid, AWS SES, Postmark)
- [ ] **Never use `ConsoleTransport` in production**
- [ ] **Test email delivery** before going live

```python
from fastauth.email_transports.smtp import SMTPTransport

transport = SMTPTransport(
    host=os.environ["SMTP_HOST"],
    port=587,
    username=os.environ["SMTP_USER"],
    password=os.environ["SMTP_PASS"],
    use_tls=True,
    from_email="noreply@example.com",
)
```

## Rate limiting

FastAuth does not include built-in rate limiting. Add it at the infrastructure level:

- **Reverse proxy**: nginx rate limiting, Caddy's rate-limit plugin
- **API gateway**: AWS API Gateway, Kong, Traefik
- **Application**: `slowapi` (FastAPI-compatible rate limiter)

Consider rate limiting these endpoints in particular:
- `POST /auth/login` — prevent brute-force attacks
- `POST /auth/forgot-password` — prevent email flooding
- `POST /auth/register` — prevent account spam

## Monitoring

- [ ] Hook into `on_signin`, `on_signup` to emit metrics or audit logs
- [ ] Monitor failed sign-in rates for anomaly detection
- [ ] Set up alerts for database connection pool exhaustion

## Release checklist (for maintainers)

When cutting a new release of FastAuth itself:

- [ ] **Update `CHANGELOG.md`** — move the `[Unreleased]` section into a dated `[X.Y.Z]` block and start a fresh `[Unreleased]`.
- [ ] **Bump the version** in `packages/fastauth/pyproject.toml` and `packages/fastauth/src/fastauth/__init__.py` (`__version__`).
- [ ] **Refresh stale docs and examples** — `README.md`, `packages/fastauth/README.md`, `docs/index.md`, the bug-report placeholder, and the `docs/getting-started/installation.md` example output. See [`docs/guides/production.md` → Release checklist](#release-checklist-for-maintainers).
- [ ] **Run the full CI gate locally**:
    - `uv run pytest tests/ -q`
    - `uv run ruff check .`
    - `uv run ruff format --check .`
    - `uv run mkdocs build`
    - `uv build --package sreekarnv-fastauth --out-dir dist` and confirm both `sdist` and `wheel` include `LICENSE`.
- [ ] **Smoke-install the wheel** in a clean venv and import `fastauth` to confirm `__version__` matches the new release (the CI `package-smoke` job does this on every PR that touches packaging files).
- [ ] **Tag the release** on the default branch and let the publish workflow upload to PyPI.
