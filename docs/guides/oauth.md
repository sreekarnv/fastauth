# Guide: Adding OAuth

This guide extends the basic credentials app to add Google and GitHub social login, based on `examples/oauth`.

## Install

```bash
pip install "sreekarnv-fastauth[standard,oauth]"
```

## Setup providers

```python title="examples/oauth/main.py"
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.email_transports.console import ConsoleTransport
from fastauth.providers.credentials import CredentialsProvider
from fastauth.providers.github import GitHubProvider
from fastauth.providers.google import GoogleProvider
from fastauth.session_backends.memory import MemorySessionBackend

adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

config = FastAuthConfig(
    secret=os.environ["SECRET"],
    providers=[
        CredentialsProvider(),
        GoogleProvider(
            client_id=os.environ["GOOGLE_CLIENT_ID"],
            client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        ),
        GitHubProvider(
            client_id=os.environ["GITHUB_CLIENT_ID"],
            client_secret=os.environ["GITHUB_CLIENT_SECRET"],
        ),
    ],
    adapter=adapter.user,
    token_adapter=adapter.token,
    oauth_adapter=adapter.oauth,                      # stores linked accounts
    oauth_state_store=MemorySessionBackend(),          # CSRF state (use Redis in prod)
    oauth_redirect_url="http://localhost:3000/auth/callback",  # optional frontend redirect
    email_transport=ConsoleTransport(),
    base_url="http://localhost:8000",
)

auth = FastAuth(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    yield


app = FastAPI(title="FastAuth OAuth Example", lifespan=lifespan)
auth.mount(app)
```

## What's different from the basic app?

| Addition | Why |
|----------|-----|
| `GoogleProvider(...)` | Adds Google OAuth 2.0 |
| `GitHubProvider(...)` | Adds GitHub OAuth 2.0 |
| `oauth_adapter=adapter.oauth` | Persists the link between a provider account and a local user |
| `oauth_state_store=MemorySessionBackend()` | Stores the CSRF state token during the OAuth dance |
| `oauth_redirect_url="..."` | Where to redirect after a successful OAuth callback (with tokens in query params) |

## Register the redirect URL with providers

The callback URL that OAuth providers redirect to is:

```
http://localhost:8000/auth/oauth/{provider}/callback
```

### Google

1. Open [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Edit your OAuth 2.0 client
3. Add `http://localhost:8000/auth/oauth/google/callback` to **Authorized redirect URIs**

### GitHub

1. Open [GitHub Developer Settings → OAuth Apps](https://github.com/settings/developers)
2. Set **Authorization callback URL** to `http://localhost:8000/auth/oauth/github/callback`

## Trigger the OAuth flow

From your frontend, call the authorize endpoint to get the provider's URL:

```bash
curl "http://localhost:8000/auth/oauth/google/authorize?redirect_uri=http://localhost:8000/auth/oauth/google/callback"
```

Response:
```json
{"url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&state=..."}
```

Redirect the user's browser to that URL. FastAuth handles the rest — CSRF state, code exchange, user creation/linking, and token issuance.

After the OAuth flow completes, if `oauth_redirect_url` is set, FastAuth redirects to it with tokens as query parameters:

```
http://localhost:3000/auth/callback?access_token=eyJ...&refresh_token=eyJ...&token_type=bearer&expires_in=900
```

## Environment variables

```bash
export SECRET=$(fastauth generate-secret)
export GOOGLE_CLIENT_ID=...
export GOOGLE_CLIENT_SECRET=...
export GITHUB_CLIENT_ID=...
export GITHUB_CLIENT_SECRET=...
uvicorn main:app --reload
```

## Production notes

- Replace `MemorySessionBackend()` with `RedisSessionBackend(...)` so OAuth state survives across multiple processes.
- Use HTTPS callback URLs in production.
- Set `oauth_redirect_url` to your production frontend URL.
