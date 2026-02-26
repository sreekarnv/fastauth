# Guide: Magic Links

This guide walks through the `examples/magic_link` application — a minimal FastAPI app with passwordless sign-in using magic links.

## What we're building

- Magic link sign-in (no password required)
- Auto-registration on first login
- SQLite database via SQLAlchemy
- SMTP email delivery

## Full server source

```python title="examples/magic_link/main.py"
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.email_transports.smtp import SMTPTransport
from fastauth.providers.magic_links import MagicLinksProvider

adapter = SQLAlchemyAdapter(
    engine_url=os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./magic_links.db")
)

email_transport = SMTPTransport(
    host=os.environ["SMTP_HOST"],
    port=int(os.environ.get("SMTP_PORT", "587")),
    username=os.environ["SMTP_USER"],
    password=os.environ["SMTP_PASS"],
    from_email=os.environ["SMTP_FROM"],
    use_tls=False,
)

config = FastAuthConfig(
    secret=os.environ["SECRET"],
    providers=[MagicLinksProvider()],
    adapter=adapter.user,
    token_adapter=adapter.token,
    email_transport=email_transport,
)

auth = FastAuth(config=config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    yield


app = FastAPI(lifespan=lifespan)
auth.mount(app)
```

## Install dependencies

```bash
pip install "sreekarnv-fastauth[standard,email]"
```

## Environment variables

| Variable | Example | Description |
|----------|---------|-------------|
| `SECRET` | `change-me` | JWT signing secret |
| `SMTP_HOST` | `localhost` | SMTP server host |
| `SMTP_PORT` | `1025` | SMTP server port |
| `SMTP_USER` | _(empty)_ | SMTP username |
| `SMTP_PASS` | _(empty)_ | SMTP password |
| `SMTP_FROM` | `no-reply@example.com` | Sender address |
| `DATABASE_URL` | `sqlite+aiosqlite:///./magic_links.db` | Database URL |

## Local development with Mailpit

[Mailpit](https://mailpit.axllent.org/) runs a local SMTP server and provides a web UI to inspect sent emails — ideal for testing magic links without a real mail server.

=== "macOS"

    ```bash
    brew install mailpit
    mailpit
    ```

=== "Docker"

    ```bash
    docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit
    ```

Then set:

```bash
export SECRET=dev-secret
export SMTP_HOST=localhost
export SMTP_PORT=1025
export SMTP_USER=
export SMTP_PASS=
export SMTP_FROM=no-reply@example.com
```

Start the app:

```bash
uvicorn main:app --reload
```

Open `http://localhost:8025` to see incoming emails.

## Testing the flow

### 1 — Request a magic link

```bash
curl -X POST http://localhost:8000/auth/magic-links/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com"}'
```

Response:

```json
{"message": "Magic link sent — check your email"}
```

The email appears in Mailpit at `http://localhost:8025`. It contains a link like:

```
http://localhost:8000/auth/magic-links/callback?token=<cuid>
```

### 2 — Exchange the token

Open the link in a browser, or call it directly:

```bash
curl "http://localhost:8000/auth/magic-links/callback?token=<token-from-email>"
```

Response:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

The link is one-time use. Clicking it again returns `401`.

### 3 — Access a protected route

```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## Auto-registration

If the email is not in the database, FastAuth creates the user automatically (with no password). Subsequent logins with the same email sign in to that account. No separate registration endpoint is needed.

## Token lifetime

The default is 15 minutes. Change it when configuring the provider:

```python
MagicLinksProvider(max_age=30 * 60)  # 30 minutes
```

## Production notes

- Set `SECRET` to a long random string (e.g. `openssl rand -hex 32`).
- Use a real SMTP service — [Resend](https://resend.com), [SendGrid](https://sendgrid.com), or [Postmark](https://postmark.com) all work via `SMTPTransport`.
- Use a persistent database (`DATABASE_URL` pointing to PostgreSQL) so tokens survive restarts.
- Set `base_url` in `FastAuthConfig` to your production domain so callback links point to the right host.
- Enable `use_tls=True` in `SMTPTransport` for production SMTP servers.

## Further reading

- [Magic Links feature reference](../features/magic-links.md)
- [Magic Links provider reference](../providers/magic-links.md)
- [Email Verification](../features/email-verification.md) — same token/transport infrastructure
