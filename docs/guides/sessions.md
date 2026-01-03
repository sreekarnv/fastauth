# Session Management

Track and manage user sessions across multiple devices.

## Overview

FastAuth provides session management to:
- Track user logins across multiple devices
- Monitor session activity (IP, device, last active)
- Allow users to revoke specific sessions
- Sign out from all devices remotely

## Basic Setup

### Step 1: Include Session Router

```python
from fastapi import FastAPI
from fastauth.api.sessions import router as sessions_router

app = FastAPI()
app.include_router(sessions_router)
```

This adds session management endpoints:
- `GET /sessions` - List all active sessions
- `DELETE /sessions/{session_id}` - Revoke specific session
- `DELETE /sessions/all` - Revoke all sessions

### Step 2: Create Sessions on Login

Sessions are automatically created when using the built-in auth router. For custom login:

```python
from fastapi import Depends, Request
from fastauth.core.sessions import create_session
from fastauth.adapters.sqlalchemy import SQLAlchemySessionAdapter, SQLAlchemyUserAdapter
from fastauth.security.jwt import create_access_token

@app.post("/login")
def login(
    request: Request,
    email: str,
    password: str,
    session: Session = Depends(get_session),
):
    user_adapter = SQLAlchemyUserAdapter(session)
    session_adapter = SQLAlchemySessionAdapter(session)

    # Authenticate user
    user = authenticate_user(users=user_adapter, email=email, password=password)

    # Create session with device info
    user_session = create_session(
        sessions=session_adapter,
        users=user_adapter,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        device="Web Browser",  # Can parse from user-agent
    )

    # Include session_id in token
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"session_id": str(user_session.id)},
    )

    return {"access_token": access_token}
```

## Session Operations

### List Active Sessions

```python
from fastauth.core.sessions import get_user_sessions

@app.get("/sessions")
def list_sessions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    session_adapter = SQLAlchemySessionAdapter(session)

    user_sessions = get_user_sessions(
        sessions=session_adapter,
        user_id=current_user.id,
    )

    return {
        "sessions": [
            {
                "id": str(s.id),
                "device": s.device,
                "ip_address": s.ip_address,
                "last_active": s.last_active,
                "created_at": s.created_at,
            }
            for s in user_sessions
        ]
    }
```

### Revoke Specific Session

```python
from fastauth.core.sessions import delete_session

@app.delete("/sessions/{session_id}")
def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    session_adapter = SQLAlchemySessionAdapter(session)

    delete_session(
        sessions=session_adapter,
        session_id=uuid.UUID(session_id),
        user_id=current_user.id,
    )

    return {"message": "Session revoked"}
```

### Revoke All Sessions

```python
from fastauth.core.sessions import delete_all_user_sessions

@app.post("/sessions/revoke-all")
def revoke_all_sessions(
    keep_current: bool = True,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    session_adapter = SQLAlchemySessionAdapter(session)

    # Get current session ID from token if keeping current
    current_session_id = None
    if keep_current:
        # Extract from JWT token claims
        current_session_id = get_current_session_id()  # Implement this

    delete_all_user_sessions(
        sessions=session_adapter,
        user_id=current_user.id,
        except_session_id=current_session_id,
    )

    return {"message": "All other sessions revoked"}
```

## Device Tracking

Parse user agent to get device information:

```python
def parse_user_agent(user_agent: str) -> str:
    """Parse user agent string to get device type."""
    if not user_agent:
        return "Unknown Device"

    ua_lower = user_agent.lower()

    # Mobile devices
    if "mobile" in ua_lower or "android" in ua_lower:
        if "android" in ua_lower:
            return "Android Device"
        if "iphone" in ua_lower:
            return "iPhone"
        if "ipad" in ua_lower:
            return "iPad"
        return "Mobile Device"

    # Desktop browsers
    if "chrome" in ua_lower:
        return "Chrome Browser"
    if "firefox" in ua_lower:
        return "Firefox Browser"
    if "safari" in ua_lower:
        return "Safari Browser"
    if "edge" in ua_lower:
        return "Edge Browser"

    return "Web Browser"

@app.post("/login")
def login(request: Request, ...):
    device = parse_user_agent(request.headers.get("user-agent"))

    user_session = create_session(
        sessions=session_adapter,
        users=user_adapter,
        user_id=user.id,
        device=device,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )
    ...
```

## Session Metadata

Session objects include:

```python
class Session:
    id: UUID
    user_id: UUID
    device: str              # "Chrome Browser", "iPhone", etc.
    ip_address: str          # "192.168.1.1"
    user_agent: str          # Full user agent string
    last_active: datetime    # Auto-updated
    created_at: datetime     # Session creation time
```

## Frontend Integration

### List Sessions UI

```javascript
// Fetch active sessions
async function fetchSessions() {
  const response = await fetch('http://localhost:8000/sessions', {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  const data = await response.json();
  return data.sessions;
}

// Display sessions
sessions.forEach(session => {
  console.log(`${session.device} - Last active: ${session.last_active}`);
});
```

### Revoke Session

```javascript
async function revokeSession(sessionId) {
  await fetch(`http://localhost:8000/sessions/${sessionId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
}
```

### Sign Out All Devices

```javascript
async function signOutAllDevices() {
  await fetch('http://localhost:8000/sessions/revoke-all', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ keep_current: true })
  });
}
```

## Using Built-in Session Router

The easiest way to add session management:

```python
from fastapi import FastAPI
from fastauth.api.sessions import router as sessions_router
from fastauth.api.auth import router as auth_router

app = FastAPI()

# Sessions are automatically created on login
app.include_router(auth_router)
app.include_router(sessions_router)
```

Built-in endpoints:
- `GET /sessions` - List user's active sessions
- `DELETE /sessions/{session_id}` - Revoke specific session
- `DELETE /sessions/all` - Revoke all sessions (keeps current by default)

## Session Security

### Update Last Active

Sessions should track last activity:

```python
from fastauth.core.sessions import update_session_last_active

@app.middleware("http")
async def update_session_activity(request: Request, call_next):
    # Extract session_id from JWT token
    session_id = get_session_id_from_request(request)

    if session_id:
        with Session(engine) as session:
            session_adapter = SQLAlchemySessionAdapter(session)
            update_session_last_active(
                sessions=session_adapter,
                session_id=session_id,
            )

    response = await call_next(request)
    return response
```

### Session Expiration

Configure session lifetime:

```bash
# .env
SESSION_EXPIRE_DAYS=30
```

Clean up expired sessions periodically:

```python
from datetime import datetime, timedelta

def cleanup_expired_sessions():
    """Remove sessions older than 30 days."""
    with Session(engine) as session:
        session_adapter = SQLAlchemySessionAdapter(session)
        cutoff = datetime.utcnow() - timedelta(days=30)

        # Implement in adapter
        session_adapter.delete_inactive_since(cutoff)
```

## Example: Session Dashboard

```python
@app.get("/me/sessions")
def get_session_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    session_adapter = SQLAlchemySessionAdapter(session)
    user_sessions = get_user_sessions(
        sessions=session_adapter,
        user_id=current_user.id,
    )

    # Get current session ID from token
    current_session_id = get_session_id_from_token(
        request.headers.get("authorization", "").replace("Bearer ", "")
    )

    sessions_data = []
    for s in user_sessions:
        sessions_data.append({
            "id": str(s.id),
            "device": s.device,
            "ip_address": s.ip_address,
            "location": get_location_from_ip(s.ip_address),  # Optional
            "last_active": s.last_active,
            "is_current": s.id == current_session_id,
        })

    # Sort by last active
    sessions_data.sort(key=lambda x: x["last_active"], reverse=True)

    return {
        "total_sessions": len(sessions_data),
        "sessions": sessions_data,
    }
```

## Complete Example

See the [Session Devices Example](../../examples/session-devices/) for a full implementation with:
- Session creation on login/register
- Device detection from user agent
- Session listing with current session indicator
- Individual and bulk session revocation
- HTML/JavaScript frontend

## Next Steps

- **[Authentication](authentication.md)** - User login and registration
- **[Protecting Routes](protecting-routes.md)** - Secure endpoints
- **[Session Example](../../examples/session-devices/)** - Complete working example
