# FastAuth

> Production-ready authentication for FastAPI applications

FastAuth is a flexible, database-agnostic authentication library for FastAPI that provides secure user authentication, session management, and authorization out of the box.

[![CI](https://github.com/sreekarnv/fastauth/actions/workflows/ci.yml/badge.svg)](https://github.com/sreekarnv/fastauth/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Complete Authentication Flow** - Registration, login, logout, and token refresh
- **Role-Based Access Control (RBAC)** - Fine-grained authorization with roles and permissions
- **Email Verification** - Secure email verification with expiring tokens
- **Password Reset** - Self-service password reset via email
- **Refresh Tokens** - Long-lived refresh tokens with rotation support
- **Rate Limiting** - Built-in rate limiting for authentication endpoints
- **Database Agnostic** - Adapter pattern supports any database (SQLAlchemy included)
- **Type Safe** - Full type hints and Pydantic validation
- **Production Ready** - Secure defaults, comprehensive tests, and CI/CD pipeline

## Installation

### From PyPI (Coming Soon)

```bash
pip install fastauth
```

### From Source

```bash
git clone https://github.com/sreekarnv/fastauth.git
cd fastauth
pip install .
```

### With Poetry

```bash
poetry add fastauth
```

## Quick Start

Here's a complete authentication system in under 5 minutes:

### 1. Install FastAuth

```bash
pip install fastauth
```

### 2. Create Your Application

```python
from fastapi import FastAPI, Depends
from sqlmodel import Session, SQLModel, create_engine
from fastauth import auth_router
from fastauth.api import dependencies
from fastauth.adapters.sqlalchemy.models import User

# Database setup
DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# Create FastAPI app
app = FastAPI(title="My App")

# Initialize database
init_db()

# Include FastAuth router
app.include_router(auth_router)

# Override session dependency
app.dependency_overrides[dependencies.get_session] = get_session

# Protected route example
from fastauth.api.dependencies import get_current_user

@app.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}!"}
```

### 3. Configure Environment Variables

Create a `.env` file:

```bash
# JWT Settings
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Settings (optional - uses console by default)
EMAIL_PROVIDER=console  # or smtp, sendgrid, resend, ses
REQUIRE_EMAIL_VERIFICATION=false  # Set to true in production
```

### 4. Run Your Application

```bash
uvicorn main:app --reload
```

### 5. Try It Out

Visit `http://localhost:8000/docs` to see the auto-generated API documentation and try:

**Register a user:**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword123"}'
```

**Login:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword123"}'
```

**Access protected route:**
```bash
curl -X GET "http://localhost:8000/protected" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

That's it! You now have a working authentication system.

## API Endpoints

FastAuth automatically adds these endpoints to your application:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login with email and password |
| `POST` | `/auth/logout` | Logout and revoke refresh token |
| `POST` | `/auth/refresh` | Get new access token using refresh token |
| `POST` | `/auth/password-reset/request` | Request password reset email |
| `POST` | `/auth/password-reset/confirm` | Reset password with token |
| `POST` | `/auth/email-verification/request` | Request email verification |
| `POST` | `/auth/email-verification/confirm` | Verify email with token |
| `POST` | `/auth/email-verification/resend` | Resend verification email |

## Architecture

FastAuth uses a clean, layered architecture:

```
┌─────────────────────────────────────┐
│         FastAPI Routes              │  ← Your application
├─────────────────────────────────────┤
│         FastAuth API Layer          │  ← HTTP handlers
├─────────────────────────────────────┤
│         Core Business Logic         │  ← Database-agnostic
├─────────────────────────────────────┤
│         Adapter Interface           │  ← Abstract base classes
├─────────────────────────────────────┤
│    Adapter Implementation           │  ← SQLAlchemy, MongoDB, etc.
│    (SQLAlchemy, MongoDB, etc.)      │
└─────────────────────────────────────┘
```

**Key Principles:**

- **Database Agnostic Core** - Business logic has no database dependencies
- **Adapter Pattern** - Swap databases by implementing the adapter interface
- **Dependency Injection** - Easy to customize and test
- **Type Safety** - Full type hints throughout

## Configuration

FastAuth can be configured via environment variables or the `Settings` class:

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Configuration
EMAIL_PROVIDER=console  # console, smtp, sendgrid, resend, ses
REQUIRE_EMAIL_VERIFICATION=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourapp.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
LOGIN_RATE_LIMIT=5  # attempts per window
LOGIN_RATE_WINDOW=300  # seconds (5 minutes)
```

### Programmatic Configuration

```python
from fastauth import Settings

settings = Settings(
    jwt_secret_key="your-secret-key",
    access_token_expire_minutes=60,
    require_email_verification=True
)
```

## Usage Examples

### Protecting Routes

```python
from fastapi import Depends
from fastauth.api.dependencies import get_current_user
from fastauth.adapters.sqlalchemy.models import User

@app.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "verified": current_user.is_verified,
        "created_at": current_user.created_at
    }
```

### Custom User Model

```python
from sqlmodel import Field
from fastauth.adapters.sqlalchemy.models import User as BaseUser

class User(BaseUser, table=True):
    __tablename__ = "users"

    # Add custom fields
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
```

### Role-Based Access Control (RBAC)

Protect routes with roles and permissions for fine-grained authorization:

#### Creating Roles and Permissions

```python
from fastauth import create_role, create_permission, assign_permission_to_role, assign_role
from fastauth.adapters.sqlalchemy.roles import SQLAlchemyRoleAdapter

# Create roles
admin_role = create_role(roles=role_adapter, name="admin", description="Administrator")
moderator_role = create_role(roles=role_adapter, name="moderator", description="Moderator")
user_role = create_role(roles=role_adapter, name="user", description="Regular user")

# Create permissions
read_users = create_permission(roles=role_adapter, name="read:users")
write_users = create_permission(roles=role_adapter, name="write:users")
delete_users = create_permission(roles=role_adapter, name="delete:users")

# Assign permissions to roles
assign_permission_to_role(roles=role_adapter, role_name="admin", permission_name="read:users")
assign_permission_to_role(roles=role_adapter, role_name="admin", permission_name="write:users")
assign_permission_to_role(roles=role_adapter, role_name="admin", permission_name="delete:users")

# Assign role to user
assign_role(roles=role_adapter, user_id=user.id, role_name="admin")
```

#### Protecting Routes by Role

```python
from fastapi import Depends
from fastauth.api.dependencies import require_role

@app.get("/admin/dashboard", dependencies=[Depends(require_role("admin"))])
def admin_dashboard():
    return {"message": "Admin access granted"}

@app.get("/moderator/panel", dependencies=[Depends(require_role("moderator"))])
def moderator_panel():
    return {"message": "Moderator access granted"}
```

#### Protecting Routes by Permission

```python
from fastapi import Depends
from fastauth.api.dependencies import require_permission

@app.get("/users", dependencies=[Depends(require_permission("read:users"))])
def list_users():
    return {"users": [...]}

@app.delete("/users/{id}", dependencies=[Depends(require_permission("delete:users"))])
def delete_user(id: str):
    return {"message": "User deleted"}

@app.post("/users", dependencies=[Depends(require_permission("write:users"))])
def create_user(user_data: dict):
    return {"message": "User created"}
```

#### Checking Permissions Programmatically

```python
from fastauth import check_permission

# Check if user has specific permission
has_access = check_permission(
    roles=role_adapter,
    user_id=user.id,
    permission_name="delete:users"
)

if has_access:
    # Perform action
    pass
```

### Using Different Databases

FastAuth works with any database through adapters:

**SQLAlchemy (built-in):**
```python
from fastauth.adapters.sqlalchemy import SQLAlchemyUserAdapter
```

**MongoDB (install fastauth[mongodb]):**
```python
from fastauth.adapters.mongodb import MongoDBUserAdapter
```

**Custom adapter:**
```python
from fastauth.adapters.base import UserAdapter

class MyCustomAdapter(UserAdapter):
    def create_user(self, email: str, hashed_password: str):
        # Your implementation
        pass
```

## Advanced Features

### Email Verification

Enable email verification for new signups:

```python
# .env
REQUIRE_EMAIL_VERIFICATION=true
EMAIL_PROVIDER=smtp  # or sendgrid, resend, ses
```

Users must verify their email before logging in.

### Password Reset

Users can reset their password via email:

1. Request reset: `POST /auth/password-reset/request`
2. Receive email with reset link
3. Submit new password: `POST /auth/password-reset/confirm`

### Rate Limiting

Built-in rate limiting protects against brute force attacks:

- Login attempts: 5 per 5 minutes (configurable)
- Registration: 3 per 10 minutes
- Email verification: 3 per 10 minutes

### Refresh Token Rotation

Refresh tokens are automatically rotated on use for enhanced security:

```python
# Old refresh token is invalidated
# New refresh token is issued
response = await refresh_tokens(refresh_token)
```

## Examples

Check out the [examples](./examples) directory for complete applications:

- **[Basic Example](./examples/basic)** - Simple FastAPI app with FastAuth

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/sreekarnv/fastauth.git
cd fastauth

# Install dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Run tests
poetry run pytest

# Run linting
poetry run black .
poetry run ruff check .
```

### Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=fastauth --cov-report=html

# Specific test file
poetry run pytest tests/core/test_users.py

# Verbose output
poetry run pytest -v
```

### Project Structure

```
fastauth/
├── fastauth/           # Main package
│   ├── core/          # Business logic (database-agnostic)
│   ├── adapters/      # Database adapters
│   │   ├── base/     # Abstract interfaces
│   │   └── sqlalchemy/ # SQLAlchemy implementation
│   ├── api/          # FastAPI routes and dependencies
│   ├── security/     # JWT, hashing, rate limiting
│   ├── email/        # Email providers
│   └── settings.py   # Configuration
├── tests/            # Test suite
├── examples/         # Example applications
└── docs/            # Documentation
```

## Security

FastAuth follows security best practices:

- **Password Hashing** - Argon2 (OWASP recommended)
- **JWT Tokens** - Secure token generation and validation
- **Rate Limiting** - Protection against brute force
- **Token Expiration** - Configurable token lifetimes
- **Refresh Token Rotation** - Enhanced security
- **SQL Injection Protection** - Parameterized queries
- **XSS Protection** - Proper input validation

### Security Recommendations

For production deployments:

1. Use strong `JWT_SECRET_KEY` (min 32 characters)
2. Enable HTTPS/TLS
3. Enable email verification (`REQUIRE_EMAIL_VERIFICATION=true`)
4. Use secure email provider (not console)
5. Set appropriate token expiration times
6. Enable rate limiting
7. Monitor authentication logs
8. Keep dependencies updated

## Troubleshooting

### Common Issues

**Issue: "Invalid JWT secret key"**
```bash
# Solution: Set a strong secret key
JWT_SECRET_KEY=your-very-long-secret-key-min-32-characters
```

**Issue: "Email not being sent"**
```bash
# Solution: Check email provider configuration
EMAIL_PROVIDER=console  # For development
# Or configure SMTP settings for production
```

**Issue: "Database connection failed"**
```bash
# Solution: Verify database URL format
# SQLite: sqlite:///./app.db
# PostgreSQL: postgresql://user:pass@localhost/dbname
# MySQL: mysql://user:pass@localhost/dbname
```

**Issue: "Rate limit exceeded"**
```bash
# Solution: Adjust rate limit settings or wait for window to expire
LOGIN_RATE_LIMIT=10  # Increase limit
LOGIN_RATE_WINDOW=300  # 5 minutes
```

### Getting Help

- **Documentation**: [docs/](./docs)
- **Issues**: [GitHub Issues](https://github.com/sreekarnv/fastauth/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sreekarnv/fastauth/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Database ORM: [SQLModel](https://sqlmodel.tiangolo.com/)
- Password hashing: [Argon2](https://github.com/hynek/argon2-cffi)
- JWT tokens: [python-jose](https://github.com/mpdavis/python-jose)

## Support

If you find FastAuth useful, please consider:

- Starring the repository ⭐
- Reporting bugs and suggesting features
- Contributing code or documentation
- Sharing with others

---

Made with ❤️ by [Sreekar Nutulapati](https://github.com/sreekarnv)
