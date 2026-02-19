# Providers

A **provider** is the piece of FastAuth that knows *how* to authenticate a user. It doesn't store anything — that's the adapter's job — it just validates credentials or orchestrates an OAuth handshake and returns a user record.

## Provider types

| Type | `auth_type` | What it does |
|------|-------------|--------------|
| `CredentialsProvider` | `"credentials"` | Verifies an email + password pair |
| `GoogleProvider` | `"oauth"` | Handles Google OAuth 2.0 / OIDC |
| `GitHubProvider` | `"oauth"` | Handles GitHub OAuth 2.0 |

## Multiple providers at once

You can mix any number of providers:

```python
from fastauth.providers.credentials import CredentialsProvider
from fastauth.providers.google import GoogleProvider
from fastauth.providers.github import GitHubProvider

config = FastAuthConfig(
    ...,
    providers=[
        CredentialsProvider(),
        GoogleProvider(client_id="...", client_secret="..."),
        GitHubProvider(client_id="...", client_secret="..."),
    ],
)
```

FastAuth routes requests to the right provider based on the endpoint called:

- `POST /auth/signin` → CredentialsProvider
- `GET /auth/oauth/authorize?provider=google` → GoogleProvider
- `GET /auth/oauth/authorize?provider=github` → GitHubProvider

## When to use each provider

**CredentialsProvider** — the right default. Email + password with bcrypt/argon2 hashing, email verification, and password reset built in.

**GoogleProvider / GitHubProvider** — when you want social login. Users authenticate on the provider's site and are redirected back with an OAuth code. FastAuth exchanges the code, fetches the user's profile, and creates (or links) a local user record.

See the individual provider pages for setup details:

- [Credentials](../providers/credentials.md)
- [Google OAuth](../providers/google.md)
- [GitHub OAuth](../providers/github.md)
