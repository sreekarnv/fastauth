# Custom Email Templates Example

Demonstrates how to override FastAuth's built-in email templates with your own Jinja2 templates. Unrecognised templates fall back to the built-in defaults, so you only need to provide the files you want to change.

## Setup

```bash
pip install "sreekarnv-fastauth[standard,email]"
```

## Run

```bash
export SECRET=$(fastauth generate-secret)
export SMTP_HOST=localhost
export SMTP_PORT=1025
export SMTP_USER=
export SMTP_PASS=
export SMTP_FROM=no-reply@example.com
uvicorn main:app --reload
```

The example wires `SMTPTransport(...)` directly in `main.py` using the `host`/`from_email` constructor fields, so you need a local SMTP catcher to actually receive the rendered emails. The easiest way is [Mailpit](https://mailpit.axllent.org/):

```bash
# macOS
brew install mailpit && mailpit

# Docker
docker run -d -p 1025:1025 -p 8025:8025 axllent/mailpit
```

The web UI is then at <http://localhost:8025>. If you would rather avoid running SMTP, swap the `SMTPTransport(...)` call in `main.py` for `ConsoleTransport()` — the templates will then be printed to stdout.

## What this example shows

`main.py` passes `email_template_dir` pointing at the local `templates/` directory:

```python
from pathlib import Path
from fastauth import FastAuth, FastAuthConfig

TEMPLATES_DIR = Path(__file__).parent / "templates"

config = FastAuthConfig(
    ...
    email_template_dir=TEMPLATES_DIR,
)
```

Any template file placed in that directory overrides the corresponding built-in. Files not present there fall back to FastAuth's defaults automatically — you don't have to copy every template to replace just one.

## Template files

| File | Sent when | Available variables |
|------|-----------|---------------------|
| `welcome.jinja2` | User registers | `name` |
| `verification.jinja2` | Email verification requested | `name`, `url`, `expires_in_minutes` |
| `password_reset.jinja2` | Password reset requested | `name`, `url`, `expires_in_minutes` |
| `email_change.jinja2` | Email change requested | `name`, `new_email`, `url`, `expires_in_minutes` |
| `magic_link_login.jinja2` | Magic link sign-in requested | `name`, `url` |

## Try it

With SMTP running and the environment variables above set, register a user to see the welcome email:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "Pass123#"}'
```

Request a magic link to see that template:

```bash
curl -X POST http://localhost:8000/auth/magic-links/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com"}'
```

Request a password reset:

```bash
curl -X POST http://localhost:8000/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com"}'
```
