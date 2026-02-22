# Troubleshooting

Common issues and how to fix them.

---

## Authentication

### `401 Unauthorized` on every request

**Check 1 — Are you sending the token correctly?**

```bash
# JSON delivery — send the Authorization header
curl http://localhost:8000/dashboard \
  -H "Authorization: Bearer <access_token>"

# Cookie delivery — include cookies
curl http://localhost:8000/dashboard \
  --cookie "access_token=<token>"
```

**Check 2 — Has the access token expired?**

The default access token TTL is 15 minutes. Decode the token at [jwt.io](https://jwt.io) and check the `exp` claim. If expired, use `/auth/refresh` to get a new pair.

**Check 3 — Is the `secret` the same across restarts?**

If you restart the app with a different `secret`, all previously issued tokens are invalid. Fix by loading the secret from an environment variable that doesn't change.

---

### `401` after `/auth/login` with correct credentials

**Check 1 — Is `CredentialsProvider` in the providers list?**

```python
config = FastAuthConfig(
    providers=[CredentialsProvider()],  # must be present
    ...
)
```

**Check 2 — Is the password hashed correctly?**

If you seeded users manually, make sure their passwords are hashed with Argon2 or bcrypt. FastAuth will not be able to verify a plaintext password.

---

### `403 Forbidden` after OAuth sign-in

Your `allow_signin` hook is returning `False`. Check your hook implementation:

```python
class MyHooks(EventHooks):
    async def allow_signin(self, user: UserData, provider: str) -> bool:
        # Is there a condition here that might block the user?
        return not user.get("is_banned", False)
```

Note: `allow_signin` is only called for OAuth providers, not for credentials login.

---

## Cookies

### Cookies aren't being set

**Check 1 — Is `token_delivery="cookie"` set?**

```python
config = FastAuthConfig(
    ...,
    token_delivery="cookie",  # default is "json"
)
```

**Check 2 — Is `debug=True` set for local development?**

Without `debug=True`, cookies have `Secure=True` and won't be sent over plain `http://`. For local development:

```python
config = FastAuthConfig(
    ...,
    token_delivery="cookie",
    debug=True,  # allows cookies over http://localhost
)
```

**Check 3 — Cross-origin frontend?**

If your frontend is on a different domain (e.g. `localhost:3000` → `localhost:8000`), set `SameSite=none` and include credentials in your fetch calls:

```python
config = FastAuthConfig(
    ...,
    token_delivery="cookie",
    cookie_samesite="none",
    cookie_secure=True,
    cors_origins=["http://localhost:3000"],
    debug=False,
)
```

```javascript
// Frontend
fetch("http://localhost:8000/auth/login", {
  method: "POST",
  credentials: "include",   // required for cross-origin cookies
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({email, password}),
})
```

---

## Email

### Verification email isn't arriving

**Check 1 — Is `ConsoleTransport` in use?**

`ConsoleTransport` prints to stdout — check your server terminal for the verification link, not your inbox.

**Check 2 — Are `token_adapter` and `email_transport` both configured?**

Both are required for email flows:

```python
config = FastAuthConfig(
    ...,
    token_adapter=adapter.token,        # required
    email_transport=ConsoleTransport(), # or SMTPTransport
)
```

**Check 3 — SMTP credentials / firewall**

Test your SMTP connection outside FastAuth first:

```python
import asyncio, aiosmtplib

async def test():
    await aiosmtplib.send(
        message="Test",
        sender="from@example.com",
        recipients=["to@example.com"],
        hostname="smtp.example.com",
        port=587,
        username="user",
        password="pass",
        use_tls=True,
    )

asyncio.run(test())
```

---

## OAuth

### `400 Bad Request` — "oauth_state_store is not configured"

Set `oauth_state_store` in your config:

```python
from fastauth.session_backends.memory import MemorySessionBackend

config = FastAuthConfig(
    ...,
    oauth_state_store=MemorySessionBackend(),  # use Redis in production
)
```

### OAuth callback returns "state mismatch" or state not found

The OAuth state token is stored in `oauth_state_store` with a 10-minute TTL. This can fail when:

- **Multiple processes** — `MemorySessionBackend` is process-local. Use `RedisSessionBackend` in production.
- **State TTL expired** — The user took more than 10 minutes to complete the OAuth flow.
- **Redirect URI mismatch** — The `redirect_uri` passed to `/authorize` must exactly match what's registered with the provider.

### `404 Not Found` — "OAuth provider 'google' not found"

The provider ID in the URL must match. Google is `google`, GitHub is `github`:

```
GET /auth/oauth/google/authorize  ✓
GET /auth/oauth/Google/authorize  ✗ (case-sensitive)
```

---

## RBAC

### `403 Forbidden` — "RBAC is not configured"

Set `role_adapter` on the FastAuth instance:

```python
auth = FastAuth(config)
auth.role_adapter = adapter.role  # must be set before routes are called
```

### `require_role("admin")` returns 403 for all users

Check that the user actually has the `admin` role assigned. Use the `/auth/roles/me` endpoint while authenticated to inspect the current user's roles:

```bash
curl http://localhost:8000/auth/roles/me \
  -H "Authorization: Bearer <access_token>"
```

Use `/auth/roles/assign` to assign the role:

```bash
curl -X POST http://localhost:8000/auth/roles/assign \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "<user-id>", "role_name": "admin"}'
```

---

## Tables / Database

### `sqlalchemy.exc.OperationalError: no such table: users`

Call `await adapter.create_tables()` in your lifespan handler before the app starts serving requests:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()  # create tables on startup
    yield

app = FastAPI(lifespan=lifespan)
```

### Alembic doesn't detect FastAuth's tables

Import `Base` from FastAuth in your Alembic `env.py`:

```python
from fastauth.adapters.sqlalchemy.models import Base
target_metadata = Base.metadata
```

---

## JWT / Keys

### `RS256` — "private_key is required"

When using `RS256` or `RS512`, you must provide both keys:

```python
from pathlib import Path

JWTConfig(
    algorithm="RS256",
    private_key=Path("private.pem").read_text(),
    public_key=Path("public.pem").read_text(),
)
```

Generate a key pair:

```bash
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem
```

### JWKS endpoint returns 404

`initialize_jwks()` must be called in the lifespan handler **before** `auth.mount(app)`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await auth.initialize_jwks()  # must be called before mount
    await adapter.create_tables()
    yield

app = FastAPI(lifespan=lifespan)
auth.mount(app)
```

---

## Still stuck?

- Check the [Configuration reference](getting-started/configuration.md) — most issues are config-related.
- Run `fastauth check` to verify all optional dependencies are installed.
- Open an issue at [github.com/sreekarnv/fastauth](https://github.com/sreekarnv/fastauth/issues).
