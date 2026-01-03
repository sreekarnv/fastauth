# Protecting Routes

Secure your FastAPI endpoints with authentication.

## Using HTTP Bearer

The simplest way to protect routes:

```python
from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fastauth.security.jwt import decode_access_token

app = FastAPI()
security = HTTPBearer()

@app.get("/protected")
def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_access_token(credentials.credentials)
    user_id = payload["sub"]
    return {"message": f"Hello user {user_id}"}
```

### Making Requests

```bash
curl -X GET "http://localhost:8000/protected" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Using get_current_user

Get the full user object:

```python
from fastapi import Depends
from fastauth.api.dependencies import get_current_user
from fastauth.adapters.sqlalchemy.models import User

@app.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "is_verified": current_user.is_verified,
    }
```

## Optional Authentication

Make authentication optional:

```python
from typing import Optional
from fastauth.api.dependencies import get_current_user_optional

@app.get("/posts")
def list_posts(current_user: Optional[User] = Depends(get_current_user_optional)):
    if current_user:
        # Show personalized content
        return {"posts": [...], "user_id": str(current_user.id)}
    else:
        # Show public content
        return {"posts": [...]}
```

## Require Email Verification

Ensure user has verified their email:

```python
from fastauth.api.dependencies import get_verified_user

@app.get("/verified-only")
def verified_route(current_user: User = Depends(get_verified_user)):
    return {"message": f"Hello verified user {current_user.email}"}
```

## Custom Dependency

Create your own authentication dependency:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from fastauth.security.jwt import decode_access_token
from fastauth.adapters.sqlalchemy import SQLAlchemyUserAdapter

security = HTTPBearer()

def get_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    payload = decode_access_token(credentials.credentials)
    user_id = payload["sub"]

    user_adapter = SQLAlchemyUserAdapter(session)
    user = user_adapter.get_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")

    return user

@app.get("/active-only")
def active_route(user: User = Depends(get_active_user)):
    return {"message": f"Hello {user.email}"}
```

## Protecting All Routes

Apply authentication globally:

```python
from fastapi import FastAPI, Depends
from fastauth.api.dependencies import get_current_user

app = FastAPI(dependencies=[Depends(get_current_user)])

# All routes now require authentication
@app.get("/route1")
def route1():
    return {"message": "Protected"}

@app.get("/route2")
def route2():
    return {"message": "Also protected"}
```

Exclude specific routes:

```python
from fastapi import FastAPI, Depends, Request
from fastauth.api.dependencies import get_current_user

app = FastAPI()

PUBLIC_ROUTES = {"/", "/health", "/docs", "/openapi.json"}

@app.middleware("http")
async def require_auth_middleware(request: Request, call_next):
    if request.url.path not in PUBLIC_ROUTES:
        # Require authentication
        credentials = await security(request)
        decode_access_token(credentials.credentials)

    response = await call_next(request)
    return response
```

## Error Handling

Handle authentication errors:

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from jose.exceptions import JWTError

app = FastAPI()

@app.exception_handler(JWTError)
async def jwt_exception_handler(request: Request, exc: JWTError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid or expired token"},
    )
```

## Testing Protected Routes

### With pytest

```python
def test_protected_route_without_token(client):
    response = client.get("/protected")
    assert response.status_code == 403

def test_protected_route_with_token(client, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 200
```

### Create Test Token

```python
from fastauth.security.jwt import create_access_token

def get_test_token(user_id: str) -> str:
    return create_access_token(subject=user_id)
```

## Next Steps

- **[RBAC Guide](rbac.md)** - Role-based access control
- **[Sessions](sessions.md)** - Track and manage user sessions
- **[Authentication](authentication.md)** - Login and registration
