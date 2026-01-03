# Core Concepts

Understanding how FastAuth works.

## Database Agnostic Architecture

FastAuth's core business logic has **zero dependencies** on any specific database. All database operations go through adapter interfaces.

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

### Using SQLAlchemy (Default)

```python
from fastauth.adapters.sqlalchemy import SQLAlchemyUserAdapter
from sqlmodel import Session

def get_user_by_email(email: str, session: Session):
    user_adapter = SQLAlchemyUserAdapter(session)
    return user_adapter.get_by_email(email)
```

### Implementing Custom Adapters

```python
from fastauth.adapters.base import UserAdapter

class MongoDBUserAdapter(UserAdapter):
    def get_by_email(self, email: str):
        return self.collection.find_one({"email": email})
```

## Dependency Injection

FastAuth uses FastAPI's dependency injection system for flexibility. Override dependencies to customize behavior.

```python
from fastauth.api import dependencies

# Override session dependency
app.dependency_overrides[dependencies.get_session] = get_session
```

## JWT Authentication

FastAuth uses JWT tokens for authentication:

- **Access Token**: Short-lived (default: 30 min), used for API requests
- **Refresh Token**: Long-lived (default: 7 days), used to get new access tokens

```python
from fastauth.security.jwt import create_access_token, decode_access_token

# Create token
token = create_access_token(subject=str(user_id))

# Decode token
payload = decode_access_token(token)
user_id = payload["sub"]
```

## Password Security

FastAuth uses **Argon2** for password hashing (OWASP recommended):

```python
from fastauth.security.password import hash_password, verify_password

# Hash password
hashed = hash_password("my-password")

# Verify password
is_valid = verify_password("my-password", hashed)
```

## Role-Based Access Control (RBAC)

FastAuth provides built-in RBAC with roles and permissions:

```python
from fastauth.api.dependencies import require_role, require_permission

# Require specific role
@app.get("/admin", dependencies=[Depends(require_role("admin"))])
def admin_route():
    return {"message": "Admin only"}

# Require specific permission
@app.delete("/users/{id}", dependencies=[Depends(require_permission("delete:users"))])
def delete_user(id: str):
    return {"message": "User deleted"}
```

## Session Management

Track user sessions across multiple devices:

```python
from fastauth.api.sessions import router as sessions_router

app.include_router(sessions_router)
```

Users can:
- List all active sessions
- Revoke specific sessions
- Revoke all sessions (logout everywhere)

## OAuth 2.0 Integration

FastAuth supports OAuth providers (Google, GitHub, etc.):

```python
from fastauth.providers.google import GoogleOAuthProvider
from fastauth.core.oauth import initiate_oauth_flow, complete_oauth_flow

# Initialize provider
provider = GoogleOAuthProvider(
    client_id="your-client-id",
    client_secret="your-client-secret",
)

# Start OAuth flow
auth_url, state, verifier = initiate_oauth_flow(
    states=state_adapter,
    provider=provider,
    redirect_uri="http://localhost:8000/callback",
)

# Complete OAuth flow
user, is_new = await complete_oauth_flow(
    states=state_adapter,
    oauth_accounts=oauth_adapter,
    users=user_adapter,
    provider=provider,
    code=code,
    state=state,
    code_verifier=verifier,
)
```

## Configuration

FastAuth uses environment variables for configuration:

```bash
# JWT Settings
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Settings
EMAIL_PROVIDER=console  # or smtp
REQUIRE_EMAIL_VERIFICATION=false

# Database
DATABASE_URL=sqlite:///./app.db
```

Generate secure keys:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Type Safety

FastAuth provides full type hints throughout:

```python
from fastauth.api.schemas import RegisterRequest, LoginResponse
from fastauth.adapters.sqlalchemy.models import User

@app.post("/register", response_model=LoginResponse)
def register(payload: RegisterRequest) -> LoginResponse:
    # All types are validated by Pydantic
    ...
```

## Next Steps

- **[Authentication Guide](../guides/authentication.md)** - Registration, login, password reset
- **[Protecting Routes](../guides/protecting-routes.md)** - Secure your endpoints
- **[RBAC Guide](../guides/rbac.md)** - Roles and permissions
- **[OAuth Guide](../guides/oauth.md)** - Social login integration
- **[Examples](../../examples/)** - Working example projects
