# Magic Links Provider

Passwordless email-based sign-in. Users request a link, click it in their inbox, and receive a token pair — no password involved.

## Setup

```python
from fastauth import FastAuth, FastAuthConfig
from fastauth.providers.magic_links import MagicLinksProvider

auth = FastAuth(FastAuthConfig(
    secret="...",
    providers=[MagicLinksProvider()],
    adapter=...,
    token_adapter=...,       # required — stores one-time tokens
    email_transport=...,     # required — delivers the link
    base_url="https://your-app.com",
))
```

## Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_age` | `int` | `900` | Token lifetime in seconds (default: 15 minutes) |

```python
MagicLinksProvider(max_age=30 * 60)  # 30-minute links
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/magic-links/login` | Send a magic link to the given email |
| `GET`  | `/auth/magic-links/callback?token=<token>` | Verify token, return access + refresh tokens |

Both endpoints are public (no authentication required).

## Combining with other providers

```python
providers=[
    CredentialsProvider(),
    MagicLinksProvider(),
]
```

## Further reading

- [Magic Links feature reference](../features/magic-links.md) — full flow, hooks, security notes
- [Guide: Magic Links](../guides/magic-links.md) — step-by-step walkthrough with example app
