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

## Session storage

- [ ] **Use Redis** for `oauth_state_store` and `session_backend` — memory backends don't survive restarts or scale across instances

```python
from fastauth.session_backends.redis import RedisSessionBackend

backend = RedisSessionBackend(url=os.environ["REDIS_URL"])
config = FastAuthConfig(
    ...,
    oauth_state_store=backend,
    session_backend=backend,  # if using database sessions
)
```

## Cookies

- [ ] **Set `cookie_secure=True`** (default when not in debug mode)
- [ ] **Set `cookie_httponly=True`** (default) — prevents JS access
- [ ] **Review `cookie_samesite`** — `"lax"` for same-origin apps, `"none"` for cross-origin SPAs
- [ ] **Set `cookie_domain`** if you share cookies across subdomains

## Token lifetimes

- [ ] **Short access token TTL** — 15 minutes (default) is a good baseline
- [ ] **Consider shorter TTLs** for high-security applications (5 minutes)
- [ ] **Rotate refresh tokens** on every refresh (FastAuth does this automatically)

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
    hostname=os.environ["SMTP_HOST"],
    port=587,
    username=os.environ["SMTP_USER"],
    password=os.environ["SMTP_PASS"],
    use_tls=True,
    sender="noreply@example.com",
)
```

## Rate limiting

FastAuth does not include built-in rate limiting. Add it at the infrastructure level:

- **Reverse proxy**: nginx rate limiting, Caddy's rate-limit plugin
- **API gateway**: AWS API Gateway, Kong, Traefik
- **Application**: `slowapi` (FastAPI-compatible rate limiter)

Consider rate limiting these endpoints in particular:
- `POST /auth/signin` — prevent brute-force attacks
- `POST /auth/password/forgot` — prevent email flooding
- `POST /auth/signup` — prevent account spam

## Monitoring

- [ ] Hook into `on_signin`, `on_signup` to emit metrics or audit logs
- [ ] Monitor failed sign-in rates for anomaly detection
- [ ] Set up alerts for database connection pool exhaustion
