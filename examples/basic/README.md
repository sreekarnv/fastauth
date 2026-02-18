# FastAuth — Basic Example

Minimal credentials-only setup: email/password auth with SQLite storage and argon2 password hashing. Emails are printed to the console (no SMTP needed).

## What it demonstrates

- `CredentialsProvider` — register, login, logout, password reset, email verification
- `SQLAlchemyAdapter` — SQLite via aiosqlite
- `ConsoleTransport` — emails printed to stdout
- JWT sessions (HS256)
- `GET /auth/me` — fetch the currently logged-in user
- Protecting your own routes with `require_auth`, `require_role`, `require_permission`
- Cookie-based token delivery (opt-in)

## Setup

```bash
pip install sreekarnv-fastauth[standard,email]
uvicorn main:app --reload
```

Before running in production, replace the `secret` value with the output of:

```bash
fastauth generate-secret
```

## Fetching the logged-in user

FastAuth mounts a `GET /auth/me` endpoint automatically. It returns the current user or `401` if not authenticated.

```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

```json
{
  "id": "...",
  "email": "user@example.com",
  "name": null,
  "image": null,
  "email_verified": false,
  "is_active": true
}
```

## Protecting your own routes

Import the dependency helpers from `fastauth.api.deps`:

```python
from fastauth.api.deps import require_auth, require_role, require_permission

@app.get("/dashboard")
async def dashboard(user = Depends(require_auth)):
    return {"hello": user["email"]}

@app.get("/admin")
async def admin(user = Depends(require_role("admin"))):
    ...

@app.get("/reports")
async def reports(user = Depends(require_permission("reports:read"))):
    ...
```

## Cookie-based token delivery

By default tokens are returned in the JSON response body. To use `HttpOnly` cookies instead (recommended for browser-based apps), set `token_delivery="cookie"` in your config:

```python
config = FastAuthConfig(
    ...
    token_delivery="cookie",
    debug=True,          # sets cookie_secure=False for local dev automatically
    # cookie_samesite="lax",    # default
    # cookie_httponly=True,     # default
    # cookie_domain=None,       # default
)
```

With cookies enabled:
- `POST /auth/login` and `POST /auth/register` set `HttpOnly` cookies
- `POST /auth/logout` clears the cookies
- `POST /auth/refresh` reads the refresh token from the cookie (no request body needed)
- `GET /auth/me` and all protected routes read the access token from the cookie automatically

`cookie_secure` defaults to `True` in production (`debug=False`) and `False` in local dev (`debug=True`), so no manual change is needed when deploying.

## Endpoints

All FastAuth routes are mounted under `/auth`:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/auth/me` | Get the current logged-in user |
| `POST` | `/auth/register` | Create a new account |
| `POST` | `/auth/login` | Obtain access + refresh tokens |
| `POST` | `/auth/logout` | Invalidate session |
| `POST` | `/auth/refresh` | Exchange a refresh token |
| `GET` | `/auth/verify-email` | Verify email via token link |
| `POST` | `/auth/forgot-password` | Request a password reset email |
| `POST` | `/auth/reset-password` | Reset password with token |
