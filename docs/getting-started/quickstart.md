# Quick Start

Get a working authentication system in 5 minutes.

## Step 1: Install

```bash
pip install sreekarnv-fastauth
```

This installs FastAuth with SQLAlchemy adapters. See [Installation](installation.md) for more options.

> **Note:** FastAPI is a peer dependency - your project must have FastAPI installed.

## Step 2: Create Your App

Create `main.py`:

```python
from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, SQLModel, create_engine

from fastauth.api import dependencies
from fastauth.api.auth import router as auth_router
from fastauth.security.jwt import decode_access_token

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

init_db()

# Include auth router
app.include_router(auth_router)

# Override session dependency
app.dependency_overrides[dependencies.get_session] = get_session

# Protected route
security = HTTPBearer()

@app.get("/protected")
def protected(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_access_token(credentials.credentials)
    return {
        "message": "You are authenticated",
        "user_id": payload["sub"],
    }
```

## Step 3: Configure Environment

Create `.env`:

```bash
JWT_SECRET_KEY=your-super-secret-key-change-this
REQUIRE_EMAIL_VERIFICATION=false
EMAIL_PROVIDER=console
```

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 4: Run

```bash
uvicorn main:app --reload
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

## Try It Out

### Register a User

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}'
```

### Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}'
```

Response includes `access_token` and `refresh_token`.

### Access Protected Route

```bash
curl -X GET "http://localhost:8000/protected" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## What's Next?

- **[Core Concepts](core-concepts.md)** - Understand how FastAuth works
- **[Authentication Guide](../guides/authentication.md)** - Login, logout, tokens, password reset
- **[Protecting Routes](../guides/protecting-routes.md)** - Secure your endpoints
- **[RBAC Guide](../guides/rbac.md)** - Roles and permissions
- **[OAuth Guide](../guides/oauth.md)** - Social login with Google, GitHub
- **[Examples](https://github.com/sreekarnv/fastauth/tree/main/examples)** - Working example projects
