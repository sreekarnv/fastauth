# FastAuth — OAuth Example

Credentials + Google + GitHub OAuth with SQLite storage. OAuth state is kept in memory — swap for `RedisSessionBackend` in production.

## What it demonstrates

- `CredentialsProvider` — email/password auth
- `GoogleProvider` — Google OAuth 2.0 (OIDC)
- `GitHubProvider` — GitHub OAuth 2.0
- `MemorySessionBackend` for OAuth state tokens
- `SQLAlchemyAdapter` — SQLite via aiosqlite
- `token_delivery="cookie"` — tokens are issued as `HttpOnly` cookies, suitable for browser-based apps
- `oauth_redirect_url` — frontend URL FastAuth 302s to after a successful OAuth callback

## Setup

```bash
cp .env.example .env   # fill in your OAuth credentials
export SECRET=$(fastauth generate-secret)
pip install sreekarnv-fastauth[standard,oauth,email]
uvicorn main:app --reload
```

The app reads `SECRET`, the OAuth client IDs/secrets, and the optional `OAUTH_REDIRECT_URL` from the environment. The example does **not** call `load_dotenv()` for you — either `export` the variables in your shell or wrap `main.py` with `python-dotenv` yourself. `SECRET` must be at least 32 bytes; generate it with `fastauth generate-secret`.

## Cookie behavior on `http://localhost`

The example sets `token_delivery="cookie"` and `debug=True` so the `HttpOnly` cookies are issued without the `Secure` flag, which lets the browser keep them over `http://localhost`. For production remove `debug=True` (or set it to `False`) so the cookies are flagged `Secure` and only sent over HTTPS.

## Getting OAuth credentials

**Google**
1. Open [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. Create an OAuth 2.0 Client ID (Web application)
3. Add `http://localhost:8000/auth/oauth/google/callback` as an authorised redirect URI

**GitHub**
1. Open [GitHub Developer Settings](https://github.com/settings/developers) → OAuth Apps → New OAuth App
2. Set the callback URL to `http://localhost:8000/auth/oauth/github/callback`

The URLs above are the **provider callback** routes handled by FastAuth. The separate `OAUTH_REDIRECT_URL` (e.g. `http://localhost:3000/auth/callback`) is where FastAuth sends the user after a successful exchange — and where the tokens are set as `HttpOnly` cookies. Tokens are never placed in the redirect URL.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Create account with email/password |
| `POST` | `/auth/login` | Credentials login |
| `POST` | `/auth/logout` | Invalidate session |
| `POST` | `/auth/refresh` | Exchange refresh token |
| `GET` | `/auth/oauth/{provider}/authorize` | Start OAuth flow (`google` or `github`) |
| `GET` | `/auth/oauth/{provider}/callback` | OAuth redirect callback |
