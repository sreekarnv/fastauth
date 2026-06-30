# Configuration

All FastAuth behaviour is controlled by two dataclasses: `FastAuthConfig` (main settings) and `JWTConfig` (token settings).

## FastAuthConfig

```python
from fastauth import FastAuthConfig
from fastauth.config import JWTConfig

config = FastAuthConfig(
    secret="...",
    providers=[...],
    adapter=adapter.user,
)
```

### Required fields

| Field | Type | Description |
|-------|------|-------------|
| `secret` | `str` | HMAC secret for HS256 signing. Generate with `fastauth generate-secret`. |
| `providers` | `list` | One or more provider instances (e.g. `CredentialsProvider()`). |
| `adapter` | `UserAdapter` | Storage adapter for user records. |

### Token delivery

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `token_delivery` | `"json"` \| `"cookie"` | `"json"` | How tokens are returned to the client. |
| `cookie_name_access` | `str` | `"access_token"` | Access-token cookie name. |
| `cookie_name_refresh` | `str` | `"refresh_token"` | Refresh-token cookie name. |
| `cookie_secure` | `bool \| None` | `None` | `Secure` flag override; defaults to `not debug`. |
| `cookie_httponly` | `bool` | `True` | Set the `HttpOnly` flag. |
| `cookie_samesite` | `"lax"` \| `"strict"` \| `"none"` | `"lax"` | `SameSite` policy. |
| `cookie_domain` | `str \| None` | `None` | Optional domain scope. |
| `csrf_enabled` | `bool` | `True` | Require a matching CSRF cookie/header for cookie-authenticated unsafe requests. |
| `csrf_cookie_name` | `str` | `"csrf_token"` | Readable CSRF cookie name. |
| `csrf_header_name` | `str` | `"X-CSRF-Token"` | Header that must match the CSRF cookie. |

### Session strategy

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `session_strategy` | `"jwt"` \| `"database"` | `"jwt"` | Currently informational only. Auth routes always issue JWT token pairs. `"database"` is reserved for a future server-side session model and is not yet wired through. |
| `session_backend` | `SessionBackend \| None` | `None` | Reserved for the future `"database"` session strategy. Not used by auth routes today. |

User session management for the `/auth/sessions` endpoints is provided by a `SessionAdapter` assigned to the `FastAuth` instance (`auth.session_adapter = ...`), independent of `session_strategy`.

### OAuth

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `oauth_adapter` | `OAuthAccountAdapter \| None` | `None` | Persists linked OAuth accounts. |
| `oauth_state_store` | `SessionBackend \| None` | `None` | Stores OAuth CSRF state. |
| `oauth_redirect_url` | `str \| None` | `None` | Frontend URL FastAuth 302s to after a successful OAuth callback. Tokens are set as `HttpOnly` cookies on the response — they are never placed in the URL. This is **not** the provider callback URL; see [OAuth → redirect_uri vs oauth_redirect_url](../features/oauth.md#redirect_uri-vs-oauth_redirect_url). |

### Email & tokens

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `email_transport` | `EmailTransport \| None` | `None` | Transport for verification/reset emails. |
| `token_adapter` | `TokenAdapter \| None` | `None` | Persists one-time verification tokens. |
| `base_url` | `str` | `"http://localhost:8000"` | Public app URL used in email links. |

### RBAC

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `roles` | `list[dict] \| None` | `None` | Seed role definitions. |
| `default_role` | `str \| None` | `None` | Automatically assigned to new users. |

### Misc

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `route_prefix` | `str` | `"/auth"` | URL prefix for all FastAuth routes. |
| `hooks` | `EventHooks \| None` | `None` | Lifecycle hook callbacks. |
| `cors_origins` | `list[str] \| None` | `None` | Allowed CORS origins. |
| `debug` | `bool` | `False` | Relaxes cookie security. Never enable in production. |

---

## JWTConfig

Pass a `JWTConfig` instance as `FastAuthConfig.jwt`:

```python
from fastauth.config import JWTConfig

config = FastAuthConfig(
    ...,
    jwt=JWTConfig(
        algorithm="HS256",
        access_token_ttl=900,    # 15 minutes
        refresh_token_ttl=86400, # 1 day
    ),
)
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `algorithm` | `str` | `"HS256"` | Signing algorithm: `"HS256"`, `"RS256"`, `"RS512"`. |
| `access_token_ttl` | `int` | `900` | Access token lifetime in seconds. |
| `refresh_token_ttl` | `int` | `2_592_000` | Refresh token lifetime in seconds (30 days). |
| `remember_me_ttl` | `int` | `7_776_000` | Refresh token lifetime in seconds (90 days) when `POST /auth/login` is called with `remember: true`. |
| `issuer` | `str \| None` | `None` | `iss` claim added to every token. |
| `audience` | `list[str] \| None` | `None` | `aud` claim; validated on decode. |
| `jwks_enabled` | `bool` | `False` | Required for RS256/RS512. Exposes `/.well-known/jwks.json` and rotates keys. |
| `key_rotation_interval` | `int \| None` | `None` | Seconds between RSA key rotations. |
| `private_key` | `str \| None` | `None` | PEM RSA private key (RS256/RS512). |
| `public_key` | `str \| None` | `None` | PEM RSA public key (RS256/RS512). |

!!! tip "RS256 keys"
    Generate an RSA key pair with:
    ```bash
    openssl genrsa -out private.pem 2048
    openssl rsa -in private.pem -pubout -out public.pem
    ```
    Then load them into `JWTConfig`:
    ```python
    JWTConfig(
        algorithm="RS256",
        private_key=Path("private.pem").read_text(),
        public_key=Path("public.pem").read_text(),
        jwks_enabled=True,
    )
    ```
    Call `auth.initialize_jwks()` before issuing tokens.
