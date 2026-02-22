# Google OAuth Provider

Authenticate users with their Google accounts via OAuth 2.0 / OIDC.

## Prerequisites

```bash
pip install "sreekarnv-fastauth[standard,oauth]"
```

Create a Google OAuth 2.0 client in the [Google Cloud Console](https://console.cloud.google.com/):

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth client ID**
3. Application type: **Web application**
4. Add an **Authorized redirect URI**: `https://your-domain.com/auth/oauth/google/callback`

## Setup

```python
import os
from fastauth.providers.google import GoogleProvider

config = FastAuthConfig(
    providers=[
        GoogleProvider(
            client_id=os.environ["GOOGLE_CLIENT_ID"],
            client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        ),
    ],
    oauth_adapter=adapter.oauth,
    oauth_state_store=MemorySessionBackend(),   # or RedisSessionBackend
    oauth_redirect_url="https://your-domain.com/auth/callback",  # optional frontend redirect
    ...
)
```

## Flow

1. **Frontend calls** `/auth/oauth/google/authorize?redirect_uri=...` — receives a `{"url": "..."}` response
2. **Frontend redirects** the user to that URL (Google's auth page)
3. Google redirects back to `/auth/oauth/google/callback` with `code` and `state`
4. FastAuth exchanges the code for tokens, fetches the user's Google profile, and either:
   - creates a new local user, or
   - links the Google account to an existing user with the same email
5. FastAuth issues an access + refresh token pair (or redirects to `oauth_redirect_url`)

```mermaid
sequenceDiagram
    participant U as User
    participant C as Client App
    participant FA as FastAuth
    participant G as Google

    C->>FA: GET /auth/oauth/google/authorize?redirect_uri=<callback_url>
    FA->>FA: generate state, store in oauth_state_store
    FA-->>C: {"url": "https://accounts.google.com/..."}

    U->>C: Client redirects user to Google URL
    U->>G: Approves permissions
    G-->>FA: 302 Redirect → /auth/oauth/google/callback?code=...&state=...

    FA->>FA: verify state (CSRF check)
    FA->>G: exchange code for tokens
    G-->>FA: {access_token, id_token, ...}
    FA->>G: fetch user profile
    G-->>FA: {email, name, picture, ...}
    FA->>FA: find or create local user
    FA-->>C: {access_token, refresh_token} or redirect to oauth_redirect_url
```

## Requested scopes

By default the Google provider requests `openid email profile`. This gives FastAuth the user's email address and basic profile information.

## Account linking

If a user with the same email already exists (e.g. they previously signed up with credentials), FastAuth links the Google account to the existing user rather than creating a duplicate.
