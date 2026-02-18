# FastAuth — OAuth Example

Credentials + Google + GitHub OAuth with SQLite storage. OAuth state is kept in memory — swap for `RedisSessionBackend` in production.

## What it demonstrates

- `CredentialsProvider` — email/password auth
- `GoogleProvider` — Google OAuth 2.0 (OIDC)
- `GitHubProvider` — GitHub OAuth 2.0
- `MemorySessionBackend` for OAuth state tokens
- `SQLAlchemyAdapter` — SQLite via aiosqlite

## Setup

```bash
cp .env.example .env   # fill in your OAuth credentials
pip install sreekarnv-fastauth[standard,oauth,email]
uvicorn main:app --reload
```

## Getting OAuth credentials

**Google**
1. Open [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. Create an OAuth 2.0 Client ID (Web application)
3. Add `http://localhost:8000/auth/oauth/callback` as an authorised redirect URI

**GitHub**
1. Open [GitHub Developer Settings](https://github.com/settings/developers) → OAuth Apps → New OAuth App
2. Set the callback URL to `http://localhost:8000/auth/oauth/callback`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Create account with email/password |
| `POST` | `/auth/login` | Credentials login |
| `POST` | `/auth/logout` | Invalidate session |
| `POST` | `/auth/refresh` | Exchange refresh token |
| `GET` | `/auth/oauth/{provider}` | Start OAuth flow (`google` or `github`) |
| `GET` | `/auth/oauth/callback` | OAuth redirect callback |
