# Installation

FastAuth uses optional **extras** so you only install what you need.

## Requirements

- Python 3.11+
- An async-capable ASGI framework (FastAPI is included in `standard`)

## Extras

| Extra | What it adds | Install |
|-------|-------------|---------|
| `fastapi` | FastAPI + Uvicorn | `pip install "sreekarnv-fastauth[fastapi]"` |
| `jwt` | joserfc + cryptography (HS256/RS256 signing) | `pip install "sreekarnv-fastauth[jwt]"` |
| `oauth` | httpx (Google, GitHub OAuth clients) | `pip install "sreekarnv-fastauth[oauth]"` |
| `sqlalchemy` | SQLAlchemy + aiosqlite | `pip install "sreekarnv-fastauth[sqlalchemy]"` |
| `postgresql` | asyncpg driver | `pip install "sreekarnv-fastauth[postgresql]"` |
| `redis` | redis-py async client | `pip install "sreekarnv-fastauth[redis]"` |
| `argon2` | argon2-cffi (password hashing) | `pip install "sreekarnv-fastauth[argon2]"` |
| `email` | aiosmtplib + Jinja2 (SMTP transport) | `pip install "sreekarnv-fastauth[email]"` |
| `cli` | typer + rich (CLI tool) | `pip install "sreekarnv-fastauth[cli]"` |
| **`standard`** | fastapi + jwt + sqlalchemy + argon2 | `pip install "sreekarnv-fastauth[standard]"` |
| **`all`** | everything above | `pip install "sreekarnv-fastauth[all]"` |

## Common install combinations

=== "Basic (credentials only)"

    ```bash
    pip install "sreekarnv-fastauth[standard]"
    ```

=== "With OAuth"

    ```bash
    pip install "sreekarnv-fastauth[standard,oauth]"
    ```

=== "With PostgreSQL + Redis"

    ```bash
    pip install "sreekarnv-fastauth[standard,oauth,postgresql,redis,email]"
    ```

=== "Everything"

    ```bash
    pip install "sreekarnv-fastauth[all]"
    ```

## Verify your installation

The CLI `check` command prints the status of every optional dependency:

```bash
fastauth check
```

Example output:

```
FastAuth v0.3.0 — Dependency Status
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Extra      ┃ Package        ┃ Status                                ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ fastapi    │ fastapi        │ ✓  installed                          │
│ jwt        │ joserfc        │ ✓  installed                          │
│ oauth      │ httpx          │ ✗  missing   pip install ...[oauth]   │
...
```
