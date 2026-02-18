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
    oauth_redirect_url="http://localhost:8000/auth/oauth/callback",
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
| `oauth_redirect_url="..."` | The callback URL that providers redirect to |

## Register the redirect URL

### Google

1. Open [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Edit your OAuth 2.0 client
3. Add `http://localhost:8000/auth/oauth/callback` to **Authorized redirect URIs**

### GitHub

1. Open [GitHub Developer Settings → OAuth Apps](https://github.com/settings/developers)
2. Set **Authorization callback URL** to `http://localhost:8000/auth/oauth/callback`

## Trigger the OAuth flow

From your frontend, redirect the user to:

```
GET /auth/oauth/authorize?provider=google
GET /auth/oauth/authorize?provider=github
```

FastAuth handles the rest — CSRF state, code exchange, user creation/linking, and token issuance.

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
- Use HTTPS for `oauth_redirect_url` in production.
