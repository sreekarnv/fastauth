# Tokens & Sessions

FastAuth always issues a JWT **access token** and **refresh token** pair on register, login, refresh, OAuth callback, magic-link callback, and passkey authentication. Token-based auth is the only mode wired through to `/auth/*` routes today.

## Session strategies

The `session_strategy` field on `FastAuthConfig` accepts `"jwt"` or `"database"`, but **only `"jwt"` is currently implemented**. Auth routes always issue JWT token pairs regardless of the configured value, and the `"database"` setting is reserved for a future server-side session model. The validator does require a `session_backend` when you set `session_strategy="database"`, but no auth route reads that backend today.

| Setting | Behaviour today |
|---------|-----------------|
| `session_strategy="jwt"` (default) | Auth routes issue JWT access + refresh tokens. `session_backend` is ignored. |
| `session_strategy="database"` | **Reserved / informational.** Auth routes still issue JWT token pairs; the `session_backend` is accepted but not wired through. Do not build production behaviour on top of this yet. |

If you want server-side session tracking today, see [User sessions](#user-sessions) below — that uses `FastAuth.session_adapter`, not `session_strategy`.

## Token lifetimes

Configure in `JWTConfig`:

```python
from fastauth.config import JWTConfig

jwt = JWTConfig(
    access_token_ttl=900,        # 15 minutes (default)
    refresh_token_ttl=2_592_000, # 30 days (default)
    remember_me_ttl=7_776_000,   # 90 days (default), used when login sends remember=True
)
```

| Token | Default TTL | Config field | Recommended range |
|-------|-------------|--------------|-------------------|
| Access | 15 minutes | `access_token_ttl` | 5 min – 1 hour |
| Refresh | 30 days | `refresh_token_ttl` | 1 day – 90 days |
| Refresh (remember me) | 90 days | `remember_me_ttl` | Use sparingly — longer means a stolen refresh token is usable for longer |

See [JWT → Remember me](../features/jwt.md#remember-me) for the login payload.

## Token delivery

| Mode | Response body | Where the tokens go | When to use |
|------|---------------|--------------------|-------------|
| `"json"` (default) | `{ access_token, refresh_token, ... }` | Body | SPAs, mobile apps, API clients |
| `"cookie"` | `{"message": "Authentication successful"}` — **no tokens** | `HttpOnly` cookies | Traditional web apps, same-origin frontends |

In cookie mode the response body intentionally never contains token material — see [Cookie Delivery](../features/cookies.md) for details.

```python
config = FastAuthConfig(
    ...,
    token_delivery="cookie",
    cookie_samesite="lax",
    cookie_secure=True,
)
```

## Refresh flow

When the access token expires, the client posts the refresh token to `/auth/refresh`:

```
POST /auth/refresh
Authorization: Bearer <refresh_token>

→ 200 OK
{ "access_token": "...", "refresh_token": "..." }
```

FastAuth validates the refresh token and **atomically consumes** its JTI from the `token_adapter` allowlist. The consume is a single read-and-delete operation (or, on row-locking databases, a `SELECT ... FOR UPDATE` followed by a rowcount-checked `DELETE`) so concurrent requests for the same refresh token can never both succeed.

A new pair is then issued and the new refresh JTI is recorded in the allowlist. The old refresh token is no longer valid.

### Replay detection

If `consume_token` returns `None` — meaning the JTI is missing or has already been consumed — FastAuth treats it as a replay attempt and revokes the entire refresh-token family for that user. All subsequent `/auth/refresh` calls for that user fail with `401` until the user signs in again.

## User sessions

User-session tracking (the kind that lets a user list and revoke their active sessions) is provided by a `SessionAdapter` assigned to the `FastAuth` instance, independent of `session_strategy`:

```python
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.session_backends.memory import MemorySessionBackend

adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")
auth = FastAuth(config)
auth.session_adapter = adapter.session     # ← this powers /auth/sessions
auth.session_backend = MemorySessionBackend()  # optional
```

`/auth/sessions` then exposes:

| Method | Path | Auth required | Description |
|--------|------|:---:|-------------|
| `GET` | `/auth/sessions` | Yes | List the caller's active sessions |
| `DELETE` | `/auth/sessions/{id}` | Yes | Revoke a single session |
| `DELETE` | `/auth/sessions/all` | Yes | Revoke all of the caller's sessions |

These endpoints are only mounted when a `session_adapter` is set; if it is `None` they return `400` with `detail: "Session management is not configured"`. This is **not** related to `session_strategy` — `session_strategy="database"` is not required to use `session_adapter`.

## Signing algorithms

| Algorithm | Key material | Use case |
|-----------|-------------|---------|
| `HS256` | Shared secret (`secret` field) | Single service |
| `RS256` | RSA private/public key pair | Microservices (verify without the private key) |
| `RS512` | RSA private/public key pair | Higher security RS variant |

See [JWT](../features/jwt.md) for RS256 setup and JWKS.
