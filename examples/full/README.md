# FastAuth — Full Example

Everything enabled: credentials + Google + GitHub OAuth, Redis-backed sessions, RBAC, SMTP email, and RS256 JWTs with a JWKS endpoint.

## What it demonstrates

- `CredentialsProvider`, `GoogleProvider`, `GitHubProvider`
- RS256 JWTs + JWKS endpoint
- Database sessions stored in Redis
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
| `OAUTH_REDIRECT_URL` | OAuth callback URL |
| `CORS_ORIGINS` | Comma-separated list of allowed origins |
| `DEBUG` | Set to `true` to enable debug mode |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register with email/password |
| `POST` | `/auth/login` | Login (credentials or OAuth) |
| `POST` | `/auth/logout` | Invalidate session |
| `POST` | `/auth/refresh` | Exchange refresh token |
| `GET` | `/auth/oauth/{provider}` | Start OAuth flow |
| `GET` | `/auth/oauth/callback` | OAuth redirect callback |
| `GET` | `/auth/verify-email` | Verify email |
| `POST` | `/auth/forgot-password` | Request password reset |
| `POST` | `/auth/reset-password` | Reset password |
| `GET` | `/.well-known/jwks.json` | JWKS public key set |
