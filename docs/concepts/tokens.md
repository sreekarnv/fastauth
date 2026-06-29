# Tokens & Sessions

FastAuth issues two types of tokens on sign-in: an **access token** (short-lived) and a **refresh token** (long-lived). It supports two session strategies: stateless JWTs and server-side database sessions.

## Session strategies

### JWT (default)

Both tokens are signed JWTs. The server is stateless — no database lookup is needed to validate a request. The access token embeds the user's ID, and `require_auth` decodes and verifies it on every request.

```python
config = FastAuthConfig(
    ...,
    session_strategy="jwt",   # default
)
```

**Pros:** Fast (no DB hit per request), easy to scale horizontally.
**Cons:** Tokens cannot be revoked before they expire (use short TTLs).

### Database sessions

The server generates an opaque session ID, stores the session data in a `SessionBackend` (Redis, in-memory, or database), and returns the session ID in a cookie or JSON response.

```python
from fastauth.session_backends.redis import RedisSessionBackend

config = FastAuthConfig(
    ...,
    session_strategy="database",
    session_backend=RedisSessionBackend(url="redis://localhost:6379"),
)
```

**Pros:** Sessions can be revoked instantly (e.g. on logout or ban).
**Cons:** Every authenticated request hits the session store.

## Token lifetimes

Configure in `JWTConfig`:

```python
from fastauth.config import JWTConfig

jwt = JWTConfig(
    access_token_ttl=900,        # 15 minutes (default)
    refresh_token_ttl=2_592_000, # 30 days (default)
)
```

| Token | Default TTL | Recommended range |
|-------|-------------|-------------------|
| Access | 15 minutes | 5 min – 1 hour |
| Refresh | 30 days | 1 day – 90 days |

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

## Signing algorithms

| Algorithm | Key material | Use case |
|-----------|-------------|---------|
| `HS256` | Shared secret (`secret` field) | Single service |
| `RS256` | RSA private/public key pair | Microservices (verify without the private key) |
| `RS512` | RSA private/public key pair | Higher security RS variant |

See [JWT](../features/jwt.md) for RS256 setup and JWKS.
