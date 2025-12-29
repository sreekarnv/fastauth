# Quick Start Guide

Get up and running with FastAuth in under 10 minutes. This guide covers installation, basic setup, and common use cases.

## Prerequisites

- Python 3.11 or higher
- Basic knowledge of FastAPI
- (Optional) PostgreSQL, MySQL, or SQLite for production

## Installation

### From PyPI (Recommended)

```bash
pip install sreekarnv-fastauth
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

## Basic Setup

### Step 1: Create FastAPI Application

Create `main.py`:

```python
from fastapi import FastAPI, Depends
from sqlmodel import Session, SQLModel, create_engine
from fastauth import auth_router, sessions_router, account_router
from fastauth.api import dependencies
from fastauth.adapters.sqlalchemy.models import User

# Database configuration
DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def init_db():
    """Initialize database tables"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Database session dependency"""
    with Session(engine) as session:
        yield session

# Create FastAPI app
app = FastAPI(title="My Auth App")

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Include FastAuth routers
app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(account_router)

# Override session dependency
app.dependency_overrides[dependencies.get_session] = get_session

# Health check endpoint
@app.get("/")
def root():
    return {"message": "Welcome to My Auth App"}

# Protected route example
from fastauth.api.dependencies import get_current_user

@app.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    return {
        "message": f"Hello {current_user.email}!",
        "user_id": str(current_user.id)
    }
```

### Step 2: Configure Environment Variables

Create `.env` file:

```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Configuration
EMAIL_PROVIDER=console
REQUIRE_EMAIL_VERIFICATION=false

# Database (optional, defaults to SQLite)
DATABASE_URL=sqlite:///./app.db
```

**Generate secure secret key:**

```bash
# Option 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: OpenSSL
openssl rand -hex 32
```

### Step 3: Install Dependencies

```bash
pip install fastapi uvicorn sqlmodel python-dotenv
```

### Step 4: Run the Application

```bash
uvicorn main:app --reload
```

Visit http://localhost:8000/docs to see the interactive API documentation.

## Common Use Cases

### 1. User Registration and Login

**Register a new user:**

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Login:**

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Accessing Protected Routes

```bash
curl -X GET "http://localhost:8000/protected" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Refresh Token

```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### 4. Logout

```bash
curl -X POST "http://localhost:8000/auth/logout" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### 5. Password Reset

**Request reset:**

```bash
curl -X POST "http://localhost:8000/auth/password-reset/request" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

**Confirm reset:**

```bash
curl -X POST "http://localhost:8000/auth/password-reset/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "RESET_TOKEN",
    "new_password": "newpassword123"
  }'
```

## Adding Email Verification

### Step 1: Update Environment Variables

```bash
# Enable email verification
REQUIRE_EMAIL_VERIFICATION=true

# Configure email provider (console for development)
EMAIL_PROVIDER=console
```

### Step 2: Verify Email Endpoint

**Request verification email:**

```bash
curl -X POST "http://localhost:8000/auth/email-verification/resend" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

**Confirm email:**

```bash
curl -X POST "http://localhost:8000/auth/email-verification/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "VERIFICATION_TOKEN"
  }'
```

## Adding Role-Based Access Control (RBAC)

### Step 1: Create Roles and Permissions

```python
from fastauth.core.roles import create_role, create_permission, assign_role, assign_permission_to_role
from fastauth.adapters.sqlalchemy import SQLAlchemyRoleAdapter

@app.on_event("startup")
def setup_roles():
    with Session(engine) as session:
        roles = SQLAlchemyRoleAdapter(session)

        # Create admin role
        admin_role = create_role(
            roles=roles,
            name="admin",
            description="Administrator role"
        )

        # Create permissions
        delete_users = create_permission(
            roles=roles,
            name="delete:users",
            description="Delete users"
        )

        # Assign permission to role
        assign_permission_to_role(
            roles=roles,
            role_name="admin",
            permission_name="delete:users"
        )

        session.commit()
```

### Step 2: Protect Routes with Roles

```python
from fastauth.api.dependencies import require_role, require_permission

# Require admin role
@app.get("/admin/dashboard", dependencies=[Depends(require_role("admin"))])
def admin_dashboard():
    return {"message": "Admin dashboard"}

# Require specific permission
@app.delete("/users/{user_id}", dependencies=[Depends(require_permission("delete:users"))])
def delete_user(user_id: str):
    return {"message": f"User {user_id} deleted"}
```

### Step 3: Assign Roles to Users

```python
from fastauth.core.roles import assign_role

@app.post("/admin/users/{user_id}/roles/{role_name}")
def assign_user_role(
    user_id: str,
    role_name: str,
    current_user: User = Depends(get_current_user)
):
    with Session(engine) as session:
        roles = SQLAlchemyRoleAdapter(session)
        assign_role(roles=roles, user_id=user_id, role_name=role_name)
        session.commit()
    return {"message": f"Role {role_name} assigned to user"}
```

## Adding OAuth 2.0 Authentication

### Step 1: Configure OAuth Provider

Add to `.env`:

```bash
# Google OAuth
OAUTH_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
OAUTH_GOOGLE_CLIENT_SECRET=your-client-secret
OAUTH_GOOGLE_REDIRECT_URI=http://localhost:8000/auth/oauth/google/callback
```

### Step 2: Include OAuth Router

```python
from fastauth import oauth_router

app.include_router(oauth_router)
```

### Step 3: Test OAuth Flow

Visit http://localhost:8000/docs and test:
1. `POST /oauth/google/authorize` - Get authorization URL
2. Visit the URL and complete OAuth
3. `POST /oauth/google/callback` - Exchange code for tokens

See [OAuth Guide](oauth.md) for detailed setup.

## Session Management

### List Active Sessions

```bash
curl -X GET "http://localhost:8000/sessions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Delete Specific Session

```bash
curl -X DELETE "http://localhost:8000/sessions/SESSION_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Delete All Sessions

```bash
curl -X DELETE "http://localhost:8000/sessions/all" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Account Management

### Change Password

```bash
curl -X POST "http://localhost:8000/account/change-password" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "oldpassword123",
    "new_password": "newpassword456"
  }'
```

### Request Email Change

```bash
curl -X POST "http://localhost:8000/account/request-email-change" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_email": "newemail@example.com"
  }'
```

### Delete Account

```bash
# Soft delete (deactivate)
curl -X DELETE "http://localhost:8000/account/delete" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "userpassword",
    "hard_delete": false
  }'

# Hard delete (permanent)
curl -X DELETE "http://localhost:8000/account/delete" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "userpassword",
    "hard_delete": true
  }'
```

## Frontend Integration

### React Example

```javascript
// Auth service
class AuthService {
  async register(email, password) {
    const response = await fetch('http://localhost:8000/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    return response.json();
  }

  async login(email, password) {
    const response = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await response.json();

    // Store tokens
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    return data;
  }

  async getProtectedData() {
    const token = localStorage.getItem('access_token');
    const response = await fetch('http://localhost:8000/protected', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  }

  async refreshToken() {
    const refresh_token = localStorage.getItem('refresh_token');
    const response = await fetch('http://localhost:8000/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token })
    });
    const data = await response.json();

    // Update tokens
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    return data;
  }

  logout() {
    const refresh_token = localStorage.getItem('refresh_token');
    fetch('http://localhost:8000/auth/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token })
    });

    // Clear tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
}

export default new AuthService();
```

### Vue.js Example

```javascript
// composables/useAuth.js
import { ref } from 'vue';

export function useAuth() {
  const user = ref(null);
  const token = ref(localStorage.getItem('access_token'));

  async function login(email, password) {
    const response = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();
    token.value = data.access_token;
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    return data;
  }

  async function fetchProtected(url) {
    return fetch(url, {
      headers: { 'Authorization': `Bearer ${token.value}` }
    });
  }

  function logout() {
    token.value = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  return { user, token, login, fetchProtected, logout };
}
```

## Testing

Run the test suite:

```bash
# Install dev dependencies
poetry install

# Run all tests
poetry run pytest

# Run with coverage
poetry run test-cov

# Open coverage report
open test-results/$(ls -t test-results | head -1)/htmlcov/index.html
```

See [Testing Guide](testing.md) for detailed information.

## Next Steps

- **[Architecture Guide](architecture.md)** - Understand FastAuth's design
- **[API Reference](api-reference.md)** - Detailed API documentation
- **[OAuth Guide](oauth.md)** - Set up OAuth 2.0 authentication
- **[Deployment Guide](deployment.md)** - Deploy to production
- **[Testing Guide](testing.md)** - Write and run tests

## Common Issues

### "Invalid credentials"

**Cause**: Wrong email or password.

**Solution**: Verify credentials or use password reset flow.

### "Email not verified"

**Cause**: Email verification is enabled but user hasn't verified.

**Solution**: Either:
- Disable verification: `REQUIRE_EMAIL_VERIFICATION=false`
- Send verification email: `POST /auth/email-verification/resend`

### "Token expired"

**Cause**: Access token has expired (default: 30 minutes).

**Solution**: Use refresh token to get new access token: `POST /auth/refresh`

### Database connection errors

**Cause**: Database not initialized or connection string incorrect.

**Solution**:
- Verify `DATABASE_URL` in `.env`
- Ensure `init_db()` is called on startup
- Check database server is running (for PostgreSQL/MySQL)

## Getting Help

- **Documentation**: https://github.com/sreekarnv/fastauth/tree/main/docs
- **Issues**: https://github.com/sreekarnv/fastauth/issues
- **Discussions**: https://github.com/sreekarnv/fastauth/discussions

## Example Projects

Check out example implementations:

- **Basic Auth**: `examples/basic/` - Minimal setup
- **With RBAC**: `examples/rbac/` - Role-based access control
- **With OAuth**: `examples/oauth/` - Google OAuth integration
- **Full Stack**: `examples/fullstack/` - React + FastAuth

---

**Congratulations!** You now have a fully functional authentication system. 🎉
