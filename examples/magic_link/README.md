# Magic Link Example

A minimal FastAuth app that demonstrates passwordless sign-in with magic links.

## Prerequisites

- Python 3.11+
- An SMTP server (or [Mailpit](https://mailpit.axllent.org/) for local testing)

## Setup

```bash
pip install "sreekarnv-fastauth[standard,email]"
```

Set the required environment variables:

```bash
export SECRET=your-secret-key
export SMTP_HOST=localhost
export SMTP_PORT=1025
export SMTP_USER=
export SMTP_PASS=
export SMTP_FROM=no-reply@example.com
```

## Run

```bash
uvicorn main:app --reload
```

## Flow

1. `POST /auth/magic-links/login` with `{"email": "user@example.com"}` — sends a magic link to the email address
2. User clicks the link in their inbox
3. `GET /auth/magic-links/callback?token=<token>` — verifies the token and returns an access/refresh token pair

## Local email testing with Mailpit

```bash
# macOS
brew install mailpit
mailpit
```

Mailpit runs an SMTP server on port 1025 and a web UI at http://localhost:8025.

```bash
export SMTP_HOST=localhost
export SMTP_PORT=1025
export SMTP_USER=
export SMTP_PASS=
export SMTP_FROM=no-reply@example.com
```
