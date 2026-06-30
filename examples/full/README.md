# FastAuth — Full Example

Everything enabled: credentials + Google + GitHub OAuth, RS256 JWTs with JWKS, Redis-backed OAuth state, RBAC, SMTP email, and cookie-based token delivery.

## What it demonstrates

- `CredentialsProvider`, `GoogleProvider`, `GitHubProvider`
- RS256 JWTs + JWKS endpoint
- `token_delivery="cookie"` — tokens set as `HttpOnly` cookies
- `/auth/sessions` user-session tracking (via `auth.session_adapter = adapter.session`)
- OAuth state stored in Redis
- SMTP email transport (verification, password reset, welcome)
- RBAC — `admin` and `user` roles with permissions
- CORS configuration

## Requirements

- A running Redis instance (`redis://localhost:6379`)
- An SMTP server (or use [Mailtrap](https://mailtrap.io) / [Resend](https://resend.com) for testing)
- Google and GitHub OAuth app credentials

## Setup

```bash
cp .env.example .env
python generate_keys.py
pip install sreekarnv-fastauth[all]
uvicorn main:app --reload
```

## Environment variables

| Variable | Description |
|----------|-------------|
| `SECRET` | App secret — generate with `fastauth generate-secret` |
| `DATABASE_URL` | Async SQLAlchemy URL (default: SQLite) |
| `REDIS_URL` | Redis connection URL |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth credentials |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | GitHub OAuth credentials |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `SMTP_FROM` | SMTP config |
| `BASE_URL` | Public base URL of this service |
| `OAUTH_REDIRECT_URL` | Frontend URL FastAuth 302s to after a successful OAuth callback. Tokens are set as `HttpOnly` cookies on the response. This is **not** the provider callback URL — that is the FastAPI route (e.g. `http://localhost:8000/auth/oauth/google/callback`) registered with the provider. |
| `CORS_ORIGINS` | Comma-separated list of allowed origins |
| `DEBUG` | Set to `true` to enable debug mode |

## Cookie mode and CSRF

`main.py` sets `token_delivery="cookie"`, so `POST /auth/login`, `POST /auth/register`, `POST /auth/refresh`, OAuth callbacks, magic-link callbacks, and passkey authentication all return a tokenless `{"message": "..."}` body and set the tokens as `HttpOnly` cookies on the response. The browser then sends the access and refresh cookies automatically on every request.

A readable `csrf_token` cookie is also set so browser clients can protect unsafe requests. After sign-in, the frontend must read the `csrf_token` cookie and echo it in the `X-CSRF-Token` header on every `POST`, `PUT`, `PATCH`, and `DELETE` request that authenticates via cookies:

```javascript
function readCookie(name) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

await fetch("/auth/logout", {
  method: "POST",
  credentials: "include",
  headers: {
    "X-CSRF-Token": decodeURIComponent(readCookie("csrf_token") ?? ""),
  },
});
```

Requests authenticated with `Authorization: Bearer …` do not need the CSRF header, and `GET` / `HEAD` / `OPTIONS` are exempt. Missing or mismatched CSRF tokens return `403 Forbidden`. See [`docs/features/cookies.md`](https://sreekarnv.github.io/fastauth/features/cookies/) for the full reference.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register with email/password |
| `POST` | `/auth/login` | Login (credentials or OAuth) |
| `POST` | `/auth/logout` | Invalidate session |
| `POST` | `/auth/refresh` | Exchange refresh token |
| `GET` | `/auth/oauth/{provider}/authorize` | Start OAuth flow |
| `GET` | `/auth/oauth/{provider}/callback` | OAuth redirect callback |
| `GET` | `/auth/verify-email` | Verify email |
| `POST` | `/auth/forgot-password` | Request password reset |
| `POST` | `/auth/reset-password` | Reset password |
| `GET` | `/auth/sessions` | List the caller's active sessions |
| `DELETE` | `/auth/sessions/{id}` | Revoke a single session |
| `DELETE` | `/auth/sessions/all` | Revoke all of the caller's sessions |
| `GET` | `/.well-known/jwks.json` | JWKS public key set |
