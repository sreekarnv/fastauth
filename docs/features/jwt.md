# JWT

FastAuth uses [joserfc](https://joserfc.readthedocs.io/) for JWT creation and validation. Both symmetric (HS256) and asymmetric (RS256/RS512) algorithms are supported.

## HS256 (default)

Uses a shared HMAC secret. Simple to set up, suitable for single-service deployments.

```python
from fastauth import FastAuthConfig
from fastauth.config import JWTConfig

config = FastAuthConfig(
    secret="my-secret-key",   # must be long and random
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
    The `secret` must be at least 32 characters for HS256. Never hard-code it — use environment variables.

## RS256 / RS512

Uses an RSA key pair. The private key signs tokens; the public key verifies them. This lets other services (microservices, CDNs) verify tokens without the private key.

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
    ),
    ...
)
```

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
