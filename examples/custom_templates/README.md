# Custom Email Templates Example

Demonstrates how to override FastAuth's built-in email templates with your own Jinja2 templates. Unrecognised templates fall back to the built-in defaults, so you only need to provide the files you want to change.

## Setup

```bash
pip install "sreekarnv-fastauth[standard,email]"
```

## Run

```bash
uvicorn main:app --reload
```

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

Because this example uses `ConsoleTransport`, rendered emails are printed to stdout — no SMTP server needed.

Register a user to see the welcome email:

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
