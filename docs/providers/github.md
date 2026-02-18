# GitHub OAuth Provider

Authenticate users with their GitHub accounts.

## Prerequisites

```bash
pip install "sreekarnv-fastauth[standard,oauth]"
```

Register a GitHub OAuth App at <https://github.com/settings/applications/new>:

- **Homepage URL**: `https://your-domain.com`
- **Authorization callback URL**: `https://your-domain.com/auth/oauth/callback`

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
    oauth_redirect_url="https://your-domain.com/auth/oauth/callback",
    ...
)
```

## Email policy

GitHub accounts may have a private email address. FastAuth fetches the user's primary, verified email from the GitHub API. If no public email is available it falls back to the verified primary email from the `/user/emails` endpoint.

!!! note
    Users without a verified email on GitHub cannot sign in until they add and verify one.

## Flow

The flow is the same as [Google OAuth](google.md) — authorize → callback → token pair. The provider ID for the `authorize` endpoint is `github`:

```
GET /auth/oauth/authorize?provider=github
```
