# Installation

FastAuth can be installed via pip or Poetry.

## Requirements

- Python 3.11 or higher
- FastAPI (peer dependency - must be installed in your project)

## Installation

### Standard Installation (Recommended)

```bash
pip install sreekarnv-fastauth
```

This installs FastAuth with SQLAlchemy adapters - everything you need for most applications.

### With OAuth Providers

If you need OAuth support (Google, GitHub, etc.):

```bash
pip install sreekarnv-fastauth[oauth]
```

### All Features

```bash
pip install sreekarnv-fastauth[all]
```

## Peer Dependency: FastAPI

FastAuth is designed for FastAPI applications. FastAPI is a **peer dependency**, meaning:

- FastAuth does **not** install FastAPI automatically
- Your project must have FastAPI installed
- FastAuth works with whatever FastAPI version you have

This approach avoids version conflicts when FastAuth is added to existing FastAPI projects.

```bash
# Your project should already have FastAPI
pip install fastapi

# Then add FastAuth
pip install sreekarnv-fastauth
```

## Install with Poetry

```bash
# Standard installation
poetry add sreekarnv-fastauth

# With OAuth providers
poetry add sreekarnv-fastauth[oauth]
```

## What's Included

| Package | Dependencies | Features |
|---------|--------------|----------|
| Default | argon2-cffi, python-jose, pydantic-settings, sqlmodel | Password hashing, JWT, settings, SQLAlchemy adapters |
| `[oauth]` | + httpx | OAuth providers (Google, GitHub, etc.) |
| `[all]` | All of the above | All features |

**Peer dependency:** FastAPI (not installed automatically)

## Verify Installation

```python
import fastauth
print(fastauth.__version__)

# Check available features
from fastauth._compat import HAS_FASTAPI, HAS_HTTPX
print(f"FastAPI: {HAS_FASTAPI}")
print(f"OAuth: {HAS_HTTPX}")
```

## Troubleshooting

### FastAPI Not Found

If you see:
```
'fastapi' is required for this feature. FastAPI is a peer dependency. Install it with: pip install fastapi
```

Install FastAPI in your project:
```bash
pip install fastapi
```

### OAuth Providers Not Available

If you need OAuth providers but they're not available:
```bash
pip install sreekarnv-fastauth[oauth]
```

## Next Steps

- [Quick Start](quickstart.md) - Build your first app with FastAuth
- [Core Concepts](core-concepts.md) - Understand how FastAuth works
