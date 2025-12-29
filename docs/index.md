# FastAuth

> Production-ready authentication for FastAPI applications

FastAuth is a flexible, database-agnostic authentication library for FastAPI that provides secure user authentication, session management, role-based access control, and OAuth 2.0 integration out of the box.

[![CI](https://github.com/sreekarnv/fastauth/actions/workflows/ci.yml/badge.svg)](https://github.com/sreekarnv/fastauth/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](https://github.com/sreekarnv/fastauth)

## Features

### 🔐 Authentication
- **Complete Auth Flow** - Registration, login, logout, token refresh
- **Email Verification** - Secure email verification with expiring tokens
- **Password Reset** - Self-service password reset via email
- **Refresh Tokens** - Long-lived refresh tokens with automatic rotation
- **OAuth 2.0** - Third-party authentication (Google, GitHub, etc.)

### 👥 Authorization
- **RBAC** - Role-Based Access Control with permissions
- **Route Protection** - Decorator-based route protection
- **Flexible Permissions** - Fine-grained permission system

### 🔧 Session Management
- **Multi-Device Support** - Track sessions across devices
- **Device Fingerprinting** - IP, user agent, device tracking
- **Session Revocation** - Individual or bulk session termination
- **Inactive Cleanup** - Automatic cleanup of stale sessions

### 👤 Account Management
- **Password Change** - Secure password updates
- **Email Change** - Verified email change flow
- **Account Deletion** - Soft delete (deactivation) or hard delete
- **OAuth Linking** - Link/unlink OAuth accounts

### 🛡️ Security
- **Argon2 Hashing** - Industry-standard password hashing
- **JWT Tokens** - Secure, stateless authentication
- **Rate Limiting** - Built-in brute-force protection
- **CSRF Protection** - OAuth state tokens
- **PKCE Support** - Enhanced OAuth security

### 🗄️ Database Support
- **Database Agnostic** - Adapter pattern for any database
- **SQLAlchemy** - Full SQLAlchemy adapter included
- **Custom Adapters** - Easy to implement for MongoDB, etc.

## Quick Start

### Installation

```bash
pip install sreekarnv-fastauth
```

### Basic Setup

```python
from fastapi import FastAPI, Depends
from sqlmodel import Session, SQLModel, create_engine
from fastauth import auth_router, sessions_router
from fastauth.api import dependencies
from fastauth.adapters.sqlalchemy.models import User

# Database setup
DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# Create app
app = FastAPI(title="My Auth App")

# Initialize database
@app.on_event("startup")
def on_startup():
    init_db()

# Include routers
app.include_router(auth_router)
app.include_router(sessions_router)

# Override dependencies
app.dependency_overrides[dependencies.get_session] = get_session

# Protected route
from fastauth.api.dependencies import get_current_user

@app.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}!"}
```

### Environment Variables

Create `.env`:

```bash
JWT_SECRET_KEY=your-secret-key
REQUIRE_EMAIL_VERIFICATION=false
EMAIL_PROVIDER=console
```

### Run the Application

```bash
uvicorn main:app --reload
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) to see the interactive API documentation.

## What's Next?

<div class="grid cards" markdown>

-   :material-clock-fast:{ .lg .middle } __Quick Start Guide__

    ---

    Get up and running in 10 minutes with our comprehensive quick start guide.

    [:octicons-arrow-right-24: Quick Start](quickstart.md)

-   :material-book-open-variant:{ .lg .middle } __Architecture__

    ---

    Understand FastAuth's design principles and architecture.

    [:octicons-arrow-right-24: Architecture](architecture.md)

-   :material-google:{ .lg .middle } __OAuth Integration__

    ---

    Add Google, GitHub, and other OAuth providers to your application.

    [:octicons-arrow-right-24: OAuth Guide](oauth.md)

-   :material-api:{ .lg .middle } __API Reference__

    ---

    Complete API documentation auto-generated from code.

    [:octicons-arrow-right-24: API Reference](reference/index.md)

</div>

## Key Concepts

### Database Agnostic

FastAuth's core business logic has **zero dependencies** on any specific database. All database operations go through abstract adapter interfaces, making it easy to swap databases or implement custom storage solutions.

```python
# Use SQLAlchemy
from fastauth.adapters.sqlalchemy import SQLAlchemyUserAdapter

# Or implement your own
class MongoDBUserAdapter(UserAdapter):
    def get_by_email(self, email: str):
        return self.collection.find_one({"email": email})
```

### Dependency Injection

Built on FastAPI's dependency injection system for maximum flexibility:

```python
from fastapi import Depends
from fastauth.api.dependencies import get_current_user

@app.get("/profile")
def get_profile(user = Depends(get_current_user)):
    return {"email": user.email}
```

### Type Safety

Full type hints and Pydantic validation throughout:

```python
from fastauth.api.schemas import RegisterRequest

@app.post("/register")
def register(payload: RegisterRequest):
    # payload.email and payload.password are validated
    ...
```

## Why FastAuth?

- **Production Ready**: 85% test coverage, comprehensive error handling, security best practices
- **Flexible**: Database-agnostic core, customizable adapters, extensible architecture
- **Complete**: Authentication, authorization, sessions, account management, OAuth - all included
- **Modern**: Built for FastAPI, uses latest Python features, async-ready
- **Well Documented**: Auto-generated API docs, comprehensive guides, real-world examples

## Statistics

<div class="grid" markdown>

=== "Tests"

    - **195 tests** passing
    - **85% coverage**
    - **CI/CD** with GitHub Actions
    - **Multiple Python versions** (3.11, 3.12, 3.13)

=== "Features"

    - **8 auth endpoints**
    - **4 session endpoints**
    - **4 account endpoints**
    - **4 OAuth endpoints**
    - **RBAC** with roles & permissions

=== "Code Quality"

    - **Type hints** throughout
    - **Linted** with Ruff
    - **Formatted** with Black
    - **Pre-commit hooks** configured

</div>

## Community

- **GitHub**: [sreekarnv/fastauth](https://github.com/sreekarnv/fastauth)
- **Issues**: [Report bugs or request features](https://github.com/sreekarnv/fastauth/issues)
- **Discussions**: [Ask questions or share ideas](https://github.com/sreekarnv/fastauth/discussions)
- **PyPI**: [fastauth](https://pypi.org/project/fastauth/)

## License

FastAuth is released under the [MIT License](https://opensource.org/licenses/MIT).

---

**Ready to get started?** Head over to the [Quick Start Guide](quickstart.md) →
