# OAuth Flow

FastAuth implements the OAuth 2.0 Authorization Code flow with CSRF protection via a random `state` parameter.

## How it works

```mermaid
sequenceDiagram
    participant U as User
    participant C as Client App
    participant FA as FastAuth
    participant SS as State Store
    participant P as OAuth Provider (Google/GitHub)

    C->>FA: GET /auth/oauth/authorize?provider=google
    FA->>FA: generate random state
    FA->>SS: write(state_id, {state}, ttl=600)
    FA-->>C: 302 Redirect → provider auth URL (with state param)

    U->>P: Approves requested permissions
    P-->>C: 302 Redirect → oauth_redirect_url?code=AUTH_CODE&state=STATE

    C->>FA: GET /auth/oauth/callback?code=AUTH_CODE&state=STATE
    FA->>SS: read(state_id) — CSRF check
    FA->>P: POST token endpoint (exchange code)
    P-->>FA: {access_token, refresh_token, id_token}
    FA->>P: GET /user (fetch profile)
    P-->>FA: {email, name, avatar, ...}

    FA->>FA: find existing user by email or OAuth account
    alt new user
        FA->>FA: create_user(email, ...)
        FA->>FA: create_oauth_account(provider, account_id, user_id)
        FA->>FA: hooks.on_signup(user)
    else existing user
        FA->>FA: hooks.on_oauth_link(user, provider) if new account
    end

    FA->>FA: hooks.allow_signin(user, provider)
    FA->>FA: issue access + refresh tokens
    FA-->>C: {access_token, refresh_token}
```

## Configuration

```python
from fastauth.session_backends.memory import MemorySessionBackend
from fastauth.providers.google import GoogleProvider
from fastauth.providers.github import GitHubProvider

config = FastAuthConfig(
    providers=[
        GoogleProvider(client_id="...", client_secret="..."),
        GitHubProvider(client_id="...", client_secret="..."),
    ],
    oauth_adapter=adapter.oauth,           # persist linked accounts
    oauth_state_store=MemorySessionBackend(),  # store CSRF state
    oauth_redirect_url="https://your-app.com/auth/oauth/callback",
    ...
)
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/auth/oauth/authorize?provider=<id>` | Start the OAuth flow (redirects to provider) |
| `GET` | `/auth/oauth/callback?code=...&state=...` | Handle the provider callback |

## CSRF protection

FastAuth generates a cryptographically random `state` value before each OAuth redirect, stores it in `oauth_state_store` with a 10-minute TTL, and verifies it when the provider redirects back. If the state is missing or doesn't match, the request is rejected with 400.

Use `RedisSessionBackend` in production so state survives across multiple app instances:

```python
from fastauth.session_backends.redis import RedisSessionBackend

config = FastAuthConfig(
    ...,
    oauth_state_store=RedisSessionBackend(url="redis://localhost:6379"),
)
```

## Account linking

When a user logs in via OAuth and a local user with the same email already exists, FastAuth links the OAuth account to the existing user and calls `hooks.on_oauth_link`. No duplicate user is created.
