# GitHub OAuth Provider

Authenticate users with their GitHub accounts.

## Prerequisites

```bash
pip install "sreekarnv-fastauth[standard,oauth]"
```

Register a GitHub OAuth App at <https://github.com/settings/applications/new>:

- **Homepage URL**: `https://your-domain.com`
- **Authorization callback URL**: `https://your-domain.com/auth/oauth/github/callback`

Copy the **Client ID** and generate a **Client Secret**.

## Setup

```python
import os
from fastauth.providers.github import GitHubProvider

config = FastAuthConfig(
    providers=[
        GitHubProvider(
            client_id=os.environ["GITHUB_CLIENT_ID"],
            client_secret=os.environ["GITHUB_CLIENT_SECRET"],
        ),
    ],
    oauth_adapter=adapter.oauth,
    oauth_state_store=MemorySessionBackend(),
    oauth_redirect_url="https://your-domain.com/auth/callback",  # optional frontend redirect
    ...
)
```

## Email policy

GitHub accounts may have a private email address. FastAuth fetches the user's profile email when it is public, or falls back to the `/user/emails` endpoint when no public email is available.

FastAuth records GitHub email verification status separately. An unverified GitHub email can create a new unverified FastAuth user, but it will not be used to link to an existing local account or mark a local email as verified.

## Flow

The flow is the same as [Google OAuth](google.md) — call `/authorize`, redirect the user, handle the callback. The provider ID is `github`:

```
GET /auth/oauth/github/authorize?redirect_uri=<callback_url>
GET /auth/oauth/github/callback?code=...&state=...
```
