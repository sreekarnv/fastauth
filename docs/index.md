# FastAuth

> Production-ready authentication for FastAPI applications

FastAuth is a flexible, database-agnostic authentication library for FastAPI that provides secure user authentication, session management, and authorization out of the box.

[![CI](https://github.com/sreekarnv/fastauth/actions/workflows/ci.yml/badge.svg)](https://github.com/sreekarnv/fastauth/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- **Complete Authentication** - Registration, login, logout, token refresh
- **Role-Based Access Control** - Fine-grained permissions and roles
- **Session Management** - Multi-device session tracking
- **OAuth Support** - Social login (Google, GitHub, etc.)
- **Email Verification** - Secure email verification with tokens
- **Password Reset** - Self-service password reset
- **Database Agnostic** - Works with any database via adapters
- **Type Safe** - Full type hints and validation

## Quick Start

### Install

```bash
pip install sreekarnv-fastauth
```

### Create Your App

```python
from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fastauth.api.auth import router as auth_router
from fastauth.security.jwt import decode_access_token

app = FastAPI()
app.include_router(auth_router)

security = HTTPBearer()

@app.get("/protected")
def protected(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_access_token(credentials.credentials)
    return {"user_id": payload["sub"]}
```

### Run

```bash
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` to see the auto-generated API documentation.

## Documentation

- **[Getting Started](getting-started/installation.md)** - Install and setup in 5 minutes
- **[Guides](guides/authentication.md)** - Authentication, RBAC, sessions, OAuth
- **[API Reference](reference/api.md)** - Complete API documentation
- **[Examples](../examples/)** - Working example applications

## Examples

Check out complete working examples:

- **[OAuth with Google](../examples/oauth-google/)** - Social login with PKCE
- **[RBAC Blog](../examples/rbac-blog/)** - Role-based access control
- **[Session Management](../examples/session-devices/)** - Multi-device tracking
- **[Basic App](../examples/basic/)** - Simple authentication

## Security

FastAuth follows security best practices:

- Argon2 password hashing (OWASP recommended)
- JWT tokens with configurable expiration
- Rate limiting for authentication endpoints
- Refresh token rotation
- Session tracking and revocation

## Architecture

```
┌─────────────────────────────────────┐
│         Your FastAPI App            │
├─────────────────────────────────────┤
│         FastAuth API Layer          │
├─────────────────────────────────────┤
│      Core Business Logic            │  ← Database-agnostic
├─────────────────────────────────────┤
│      Adapter Interface              │
├─────────────────────────────────────┤
│   Database Implementation           │  ← SQLAlchemy, MongoDB, etc.
└─────────────────────────────────────┘
```

**Key Principles:**
- Database-agnostic core
- Adapter pattern for flexibility
- Dependency injection
- Full type safety

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

```bash
# Setup development environment
git clone https://github.com/sreekarnv/fastauth.git
cd fastauth
poetry install
poetry run pytest
```

## License

MIT License - see [LICENSE](https://github.com/sreekarnv/fastauth/blob/main/LICENSE) for details.

## Links

- **[Changelog](https://github.com/sreekarnv/fastauth/blob/main/CHANGELOG.md)** - Version history and release notes
- **[Code of Conduct](https://github.com/sreekarnv/fastauth/blob/main/CODE_OF_CONDUCT.md)** - Community guidelines
- **[Contributing](contributing.md)** - How to contribute

## Acknowledgments

Built with [FastAPI](https://fastapi.tiangolo.com/), [SQLModel](https://sqlmodel.tiangolo.com/), [Argon2](https://github.com/hynek/argon2-cffi), and [python-jose](https://github.com/mpdavis/python-jose).

---

Made with by [Sreekar Nutulapati](https://github.com/sreekarnv)
