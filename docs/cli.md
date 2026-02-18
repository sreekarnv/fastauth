# CLI Reference

FastAuth includes a CLI for scaffolding, secret generation, and dependency checking.

## Install

The CLI is available when the `cli` extra is installed:

```bash
pip install "sreekarnv-fastauth[cli]"
# or
pip install "sreekarnv-fastauth[all]"
```

## Commands

### `fastauth version`

Print the installed FastAuth version.

```bash
fastauth version
# FastAuth v0.3.0
```

---

### `fastauth generate-secret`

Generate a cryptographically secure random secret for use as `FastAuthConfig.secret`.

```bash
fastauth generate-secret
# → 64-byte URL-safe base64 string

fastauth generate-secret --length 32
# → shorter secret (bytes, not characters)
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--length`, `-l` | `64` | Byte length of the generated token |

Copy the output directly into your environment:

```bash
export FASTAUTH_SECRET=$(fastauth generate-secret)
```

---

### `fastauth check`

Display the installation status of all optional FastAuth dependencies.

```bash
fastauth check
```

Example output:

```
FastAuth v0.3.0 — Dependency Status
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Extra      ┃ Package        ┃ Status                                   ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ fastapi    │ fastapi        │ ✓  installed                             │
│ jwt        │ joserfc        │ ✓  installed                             │
│ jwt        │ cryptography   │ ✓  installed                             │
│ oauth      │ httpx          │ ✗  missing   pip install ...[oauth]      │
│ sqlalchemy │ sqlalchemy     │ ✓  installed                             │
│ redis      │ redis          │ ✗  missing   pip install ...[redis]      │
│ argon2     │ argon2-cffi    │ ✓  installed                             │
│ email      │ aiosmtplib     │ ✗  missing   pip install ...[email]      │
└────────────┴────────────────┴──────────────────────────────────────────┘
```

---

### `fastauth providers`

List all available authentication providers and their status.

```bash
fastauth providers
```

---

### `fastauth init [OUTPUT_DIR]`

Scaffold a new FastAuth project with template files.

```bash
fastauth init              # scaffold in current directory
fastauth init ./myapp      # scaffold in ./myapp/
fastauth init . --force    # overwrite existing files
```

Creates two files:

**`fastauth_config.py`** — pre-filled configuration with a placeholder secret:

```python
from fastauth import FastAuth, FastAuthConfig
from fastauth.providers.credentials import CredentialsProvider
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter

SECRET = "change-me-in-production"

adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

config = FastAuthConfig(
    secret=SECRET,
    providers=[CredentialsProvider()],
    adapter=adapter.user,
    token_adapter=adapter.token,
    base_url="http://localhost:8000",
)

auth = FastAuth(config)
```

**`main.py`** — a minimal FastAPI app that mounts FastAuth:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastauth_config import adapter, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    yield

app = FastAPI(lifespan=lifespan)
auth.mount(app)
```

**After `init`, the CLI prints next steps:**

```
Next steps:
  1. Replace SECRET in fastauth_config.py with:
       fastauth generate-secret
  2. Run your app:
       uvicorn main:app --reload
```

**Options:**

| Flag | Description |
|------|-------------|
| `--force`, `-f` | Overwrite files that already exist |
