# JWT

FastAuth uses [joserfc](https://jose.authlib.org) for JWT creation and validation. Both symmetric (HS256) and asymmetric (RS256/RS512) algorithms are supported.

## Token lifetimes

FastAuth issues two tokens on sign-in: a short-lived **access token** and a longer-lived **refresh token**. The defaults are:

| Token | Default TTL | Config field |
|-------|-------------|--------------|
| Access token | 15 minutes | `JWTConfig.access_token_ttl` |
| Refresh token | 30 days | `JWTConfig.refresh_token_ttl` |
| Refresh token (remember me) | 90 days | `JWTConfig.remember_me_ttl` |

### Remember me

`POST /auth/login` accepts an optional `remember: true` field. When set, the issued refresh token uses `JWTConfig.remember_me_ttl` (default 90 days) instead of `JWTConfig.refresh_token_ttl` (default 30 days). The access-token TTL is unchanged.

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "s3cur3!", "remember": true}'
```

The same option is available in cookie delivery mode — the refresh-token cookie's `Max-Age` is extended to match. Register (`POST /auth/register`) and refresh (`POST /auth/refresh`) always use the regular `refresh_token_ttl`; they do not honour `remember`.

!!! tip "Trade-off"
    A longer refresh TTL means a stolen refresh token is usable for longer. Pair `remember: true` with `token_adapter` so the JTI allowlist still lets you revoke individual sessions, and consider revoking all sessions on sensitive actions (password change, account deletion) — FastAuth already does this.

## HS256 (default)

Uses a shared HMAC secret. Simple to set up, suitable for single-service deployments.

```python
from fastauth import FastAuthConfig
from fastauth.config import JWTConfig

config = FastAuthConfig(
    secret="REPLACE_WITH_OUTPUT_OF_fastauth_generate_secret",
    jwt=JWTConfig(algorithm="HS256"),  # default
    ...
)
```

Generate a secure secret:

```bash
fastauth generate-secret
# → 64-byte URL-safe base64 string
```

!!! warning
    The `secret` must be at least 32 bytes for HS256/HS384/HS512. Never hard-code it — use environment variables, and replace the placeholder above with the output of `fastauth generate-secret` before starting the app.

## RS256 / RS512

Uses a JWKS-backed RSA key pair. The private key signs tokens; the public key verifies them. This lets other services (microservices, CDNs) verify tokens without the private key.

### Generate keys

```bash
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem
```

Or use the helper script in the examples:

```bash
python examples/full/generate_keys.py
```

### Configure

```python
from pathlib import Path

config = FastAuthConfig(
    secret="still-required-for-the-config",
    jwt=JWTConfig(
        algorithm="RS256",
        private_key=Path("private.pem").read_text(),
        public_key=Path("public.pem").read_text(),
        jwks_enabled=True,
    ),
    ...
)
```

FastAuth only supports RSA signing through JWKS mode. Call `initialize_jwks()` before issuing tokens.

## JWKS (JSON Web Key Sets)

When `jwks_enabled=True`, FastAuth exposes a `/.well-known/jwks.json` endpoint that publishes the current public key(s). Other services can fetch this endpoint to verify tokens without you distributing the public key file.

```python
config = FastAuthConfig(
    secret="...",
    jwt=JWTConfig(
        algorithm="RS256",
        jwks_enabled=True,
        key_rotation_interval=86400,  # rotate keys every 24 hours
    ),
    ...
)
```

You must also call `initialize_jwks()` in your lifespan handler:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await auth.initialize_jwks()
    await adapter.create_tables()
    yield
```

## Token structure

A decoded FastAuth access token looks like:

```json
{
  "sub": "cuid2-user-id",
  "type": "access",
  "iat": 1700000000,
  "exp": 1700000900,
  "iss": "https://your-app.com",
  "aud": ["your-app"]
}
```

Refresh tokens use `"type": "refresh"` and have a longer `exp`.

## Custom claims

Use the `modify_jwt` hook to add custom claims:

```python
class MyHooks(EventHooks):
    async def modify_jwt(self, token: dict, user: UserData) -> dict:
        token["email"] = user["email"]
        token["plan"] = user.get("plan", "free")
        return token
```

See [Guides → Microservice JWT](../guides/microservice.md) for a full RS256 + JWKS microservice example.
