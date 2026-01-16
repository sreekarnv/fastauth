# FastAuth

> Production-ready authentication for FastAPI applications

FastAuth is a flexible, database-agnostic authentication library for FastAPI that provides secure user authentication, session management, and authorization out of the box.

[![CI](https://github.com/sreekarnv/fastauth/actions/workflows/ci.yml/badge.svg)](https://github.com/sreekarnv/fastauth/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/sreekarnv/fastauth/branch/main/graph/badge.svg)](https://codecov.io/gh/sreekarnv/fastauth)
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

## 🚀 Quick Start

### Install

```bash
pip install sreekarnv-fastauth
```

> **Note:** FastAPI is a peer dependency - your project must have FastAPI installed.

For OAuth providers (Google, GitHub, etc.):
```bash
pip install sreekarnv-fastauth[oauth]
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

## 📚 Documentation

- **[Getting Started](https://sreekarnv.github.io/fastauth/getting-started/installation/)** - Install and setup in 5 minutes
- **[Guides](https://sreekarnv.github.io/fastauth/guides/authentication/)** - Authentication, RBAC, sessions, OAuth
- **[API Reference](https://sreekarnv.github.io/fastauth/reference/api/)** - Complete API documentation
- **[Examples](./examples/)** - Working example applications

## 💡 Examples

Check out complete working examples:

- **[OAuth with Google](./examples/oauth-google/)** - Social login with PKCE
- **[RBAC Blog](./examples/rbac-blog/)** - Role-based access control
- **[Session Management](./examples/session-devices/)** - Multi-device tracking
- **[Basic App](./examples/basic/)** - Simple authentication

## 🔒 Security

FastAuth follows security best practices:

- ✅ Argon2 password hashing (OWASP recommended)
- ✅ JWT tokens with configurable expiration
- ✅ Rate limiting for authentication endpoints
- ✅ Refresh token rotation
- ✅ Session tracking and revocation

## 🏗️ Architecture

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

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

```bash
# Setup development environment
git clone https://github.com/sreekarnv/fastauth.git
cd fastauth
poetry install
poetry run pytest
```

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details.

## 🙏 Acknowledgments

Built with [FastAPI](https://fastapi.tiangolo.com/), [SQLModel](https://sqlmodel.tiangolo.com/), [Argon2](https://github.com/hynek/argon2-cffi), and [python-jose](https://github.com/mpdavis/python-jose).

---

⭐ **Star this repo** if you find it useful!

Made with ❤️ by [Sreekar Nutulapati](https://github.com/sreekarnv)
