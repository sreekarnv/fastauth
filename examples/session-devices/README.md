# Session Management Example

This example demonstrates how to implement **multi-device session tracking and management** using FastAuth.

## 🎯 What This Example Demonstrates

- ✅ **Session Creation on Login** - Each login creates a unique session
- ✅ **Multi-Device Tracking** - Track sessions across different devices
- ✅ **Session Metadata** - IP address, user agent, device info, last active time
- ✅ **View All Sessions** - See all active sessions for the current user
- ✅ **Revoke Individual Sessions** - Remotely sign out from specific devices
- ✅ **Sign Out from All Devices** - Revoke all sessions except the current one
- ✅ **Session ID in JWT** - Embed session ID in access tokens for tracking

## 📋 Prerequisites

- Python 3.11+
- Basic understanding of session management concepts

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
# Navigate to this example directory
cd examples/session-devices

# Install FastAuth (FastAPI is a peer dependency)
pip install sreekarnv-fastauth

# Install FastAPI and uvicorn
pip install fastapi uvicorn[standard]

# OR install from parent directory (for development)
pip install -e ../..
pip install fastapi uvicorn[standard]

# OR install all dependencies from requirements.txt
pip install -r requirements.txt
```

> **Note:** FastAPI is a peer dependency and must be installed separately.

### Step 2: Set Up Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# (Optional) Edit .env and customize settings
```

Your `.env` should look like:
```bash
JWT_SECRET_KEY=your-strong-secret-key-here
DATABASE_URL=sqlite:///./sessions.db
REQUIRE_EMAIL_VERIFICATION=false
```

**🔐 Security Note:** Use a strong secret key in production! Generate one with:
```bash
openssl rand -hex 32
```

### Step 3: Run the Application

```bash
# Run the FastAPI app
uvicorn app.main:app --reload
```

The application will start at: **http://localhost:8000**

### Step 4: Test Session Management

1. **Open your browser:** http://localhost:8000
2. **Use the interactive API docs:** http://localhost:8000/docs
3. **Test the session flows** (see examples below)

## 📱 How It Works

### Session Creation

When a user logs in, a new session is created with:
- **Unique Session ID** - Stored in the database and embedded in JWT
- **Device Information** - Parsed from User-Agent header
- **IP Address** - Client's IP address
- **Timestamps** - Created at and last active time

```python
# On login, a session is created
user_session = create_session(
    sessions=session_adapter,
    users=user_adapter,
    user_id=user.id,
    device=parse_user_agent(request.headers.get("user-agent")),
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
)

# Session ID is embedded in the JWT access token
access_token = create_access_token(
    subject=str(user.id),
    extra_claims={"session_id": str(user_session.id)},
)
```

### Device Parsing

The example includes a simple user agent parser that extracts:
- **Operating System**: Windows, macOS, Linux, Android, iOS
- **Browser**: Chrome, Firefox, Safari, Edge

Example output: `"Chrome on Windows"`, `"Safari on iOS"`

### Session Metadata

Each session includes:
```json
{
  "id": "uuid",
  "device": "Chrome on Windows",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 ...",
  "last_active": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:00:00Z",
  "is_current": true
}
```

## 🔌 API Endpoints

### Authentication

```bash
# Register a new user
POST /register
{
  "email": "user@example.com",
  "password": "password123"
}

# Response includes access token with embedded session ID
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}

# Login (creates a new session)
POST /login
{
  "email": "user@example.com",
  "password": "password123"
}

# Get current user info
GET /me
Authorization: Bearer <access_token>
```

### Session Management

```bash
# List all active sessions
GET /sessions
Authorization: Bearer <access_token>

# Response
[
  {
    "id": "session-uuid",
    "device": "Chrome on Windows",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 ...",
    "last_active": "2024-01-15T10:30:00Z",
    "created_at": "2024-01-15T10:00:00Z",
    "is_current": true
  },
  {
    "id": "another-session-uuid",
    "device": "Safari on iOS",
    "ip_address": "192.168.1.101",
    "user_agent": "Mozilla/5.0 ...",
    "last_active": "2024-01-14T15:20:00Z",
    "created_at": "2024-01-14T15:00:00Z",
    "is_current": false
  }
]

# Revoke a specific session
DELETE /sessions/{session_id}
Authorization: Bearer <access_token>

# Sign out from all devices (except current)
POST /sessions/revoke-all?keep_current=true
Authorization: Bearer <access_token>

# Sign out from all devices (including current)
POST /sessions/revoke-all?keep_current=false
Authorization: Bearer <access_token>
```

## 🧪 Testing Session Flows

### Example 1: Multi-Device Login

```bash
# 1. Register a user
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Save the access token
TOKEN1="<access_token_from_response>"

# 2. Login from another "device" (different user agent)
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)" \
  -d '{"email": "test@example.com", "password": "password123"}'

TOKEN2="<access_token_from_response>"

# 3. View all sessions (from first device)
curl -X GET http://localhost:8000/sessions \
  -H "Authorization: Bearer $TOKEN1"

# You should see 2 sessions:
# - Chrome on Windows (current)
# - Safari on iOS
```

### Example 2: Revoke Specific Session

```bash
# 1. List sessions and note the IDs
curl -X GET http://localhost:8000/sessions \
  -H "Authorization: Bearer $TOKEN1"

# 2. Revoke the iOS session
curl -X DELETE http://localhost:8000/sessions/{session_id} \
  -H "Authorization: Bearer $TOKEN1"

# 3. Verify the session is revoked
curl -X GET http://localhost:8000/sessions \
  -H "Authorization: Bearer $TOKEN1"
# Should now show only 1 session

# 4. Try using the revoked token (should fail for session-dependent operations)
curl -X GET http://localhost:8000/sessions \
  -H "Authorization: Bearer $TOKEN2"
# Token is still valid but session is revoked
```

### Example 3: Sign Out from All Devices

```bash
# 1. Create multiple sessions by logging in 3 times
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
# Repeat 2 more times with different User-Agents

# 2. From one device, revoke all other sessions
curl -X POST "http://localhost:8000/sessions/revoke-all?keep_current=true" \
  -H "Authorization: Bearer $TOKEN1"

# 3. Verify only current session remains
curl -X GET http://localhost:8000/sessions \
  -H "Authorization: Bearer $TOKEN1"
# Should show only 1 session (the current one)
```

## 💻 Code Walkthrough

### Embedding Session ID in JWT

```python
@app.post("/login")
def login(request: Request, payload: LoginRequest, session: Session = Depends(get_session)):
    # Authenticate user
    user = authenticate_user(users=user_adapter, email=payload.email, password=payload.password)

    # Create session
    user_session = create_session(
        sessions=session_adapter,
        users=user_adapter,
        user_id=user.id,
        device=parse_user_agent(request.headers.get("user-agent")),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    # Create access token with session ID
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"session_id": str(user_session.id)},  # 👈 Session ID embedded
    )

    return TokenResponse(access_token=access_token)
```

### Identifying Current Session

```python
def get_session_id_from_token(token: str) -> uuid.UUID | None:
    """Extract session ID from JWT token if present."""
    try:
        payload = decode_access_token(token)
        session_id_str = payload.get("session_id")
        if session_id_str:
            return uuid.UUID(session_id_str)
    except Exception:
        pass
    return None

@app.get("/sessions")
def list_sessions(request: Request, current_user: User = Depends(get_current_user)):
    # Get current session from token
    auth_header = request.headers.get("authorization", "")
    current_session_id = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        current_session_id = get_session_id_from_token(token)

    # Mark current session in response
    for session in sessions:
        session.is_current = (session.id == current_session_id)
```

### Device Information Parsing

```python
def parse_user_agent(user_agent: str | None) -> str:
    """Parse user agent string to extract device/browser info."""
    if not user_agent:
        return "Unknown Device"

    ua_lower = user_agent.lower()

    # Detect OS
    if "windows" in ua_lower:
        os = "Windows"
    elif "mac" in ua_lower:
        os = "macOS"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        os = "iOS"
    # ... etc

    # Detect browser
    if "chrome" in ua_lower:
        browser = "Chrome"
    elif "firefox" in ua_lower:
        browser = "Firefox"
    # ... etc

    return f"{browser} on {os}"
```

## 🔒 Security Features

### Session Isolation
- Each session has a unique ID
- Revoking a session doesn't invalidate the JWT (stateless)
- Session checks must be performed server-side for critical operations

### Session Tracking
- IP address and user agent logged for audit trail
- Last active timestamp helps identify inactive sessions
- Device information helps users recognize their sessions

### Remote Revocation
- Users can remotely sign out suspicious sessions
- "Sign out from all devices" provides account security
- Current session can be preserved for convenience

## 🎓 Use Cases

### 1. Security Notifications
Notify users when a new login occurs from an unrecognized device:

```python
@app.post("/login")
def login(...):
    # After creating session
    user_sessions = get_user_sessions(sessions=session_adapter, user_id=user.id)

    if len(user_sessions) == 1:
        # First session, no notification needed
        pass
    else:
        # New session from potentially new device
        send_security_notification(
            user_email=user.email,
            device=user_session.device,
            ip_address=user_session.ip_address,
        )
```

### 2. Session Limit Enforcement
Limit users to a maximum number of concurrent sessions:

```python
@app.post("/login")
def login(...):
    # Before creating new session
    user_sessions = get_user_sessions(sessions=session_adapter, user_id=user.id)

    MAX_SESSIONS = 5
    if len(user_sessions) >= MAX_SESSIONS:
        # Revoke oldest session
        oldest_session = min(user_sessions, key=lambda s: s.last_active)
        delete_session(sessions=session_adapter, session_id=oldest_session.id, user_id=user.id)
```

### 3. Suspicious Activity Detection
Detect and flag suspicious login patterns:

```python
def detect_suspicious_activity(user_id, new_ip, new_device):
    recent_sessions = get_user_sessions(sessions=session_adapter, user_id=user_id)

    # Check for rapid location changes
    for session in recent_sessions:
        if session.ip_address != new_ip:
            if is_geographically_distant(session.ip_address, new_ip):
                # Flag for review or require 2FA
                return True

    return False
```

## 🛠️ Customization

### Add Session Names

Allow users to name their sessions for easier identification:

```python
class Session(SQLModel, table=True):
    # ... existing fields ...
    session_name: str | None = None  # "My iPhone", "Work Laptop", etc.

@app.patch("/sessions/{session_id}/name")
def update_session_name(session_id: str, name: str, current_user: User = Depends(get_current_user)):
    # Update session name
    ...
```

### Track Additional Metadata

Add more tracking information:

```python
def create_session(...):
    session = sessions.create_session(
        user_id=user_id,
        device=parse_user_agent(user_agent),
        ip_address=ip_address,
        user_agent=user_agent,

        # Additional metadata
        country=get_country_from_ip(ip_address),
        city=get_city_from_ip(ip_address),
        is_mobile=is_mobile_device(user_agent),
    )
```

### Implement Session Expiry

Automatically clean up inactive sessions:

```python
from fastauth.core.sessions import cleanup_inactive_sessions

# Run as a scheduled task
@app.on_event("startup")
def schedule_cleanup():
    import threading

    def cleanup_job():
        while True:
            with Session(engine) as session:
                session_adapter = SQLAlchemySessionAdapter(session)
                cleanup_inactive_sessions(
                    sessions=session_adapter,
                    inactive_days=30,
                )
            time.sleep(86400)  # Run daily

    thread = threading.Thread(target=cleanup_job, daemon=True)
    thread.start()
```

## 🐛 Troubleshooting

### Sessions not showing up

**Check:**
1. Session is being created on login: Check database
2. Session ID is in JWT token: Decode token and verify `session_id` claim
3. User is authenticated: Verify bearer token is valid

### "Session not found" when revoking

**Possible causes:**
1. Session ID doesn't exist in database
2. Session doesn't belong to the current user
3. Session was already revoked

### Current session not marked correctly

**Check:**
1. Bearer token is properly extracted from Authorization header
2. Session ID in token matches session ID in database
3. Token hasn't expired

## 📚 Next Steps

After understanding this example, you can:

1. **Add to OAuth Example**: Track OAuth logins as separate sessions
2. **Combine with RBAC**: Show admin users all system sessions
3. **Build Activity Log**: Track user actions per session
4. **Implement 2FA**: Require 2FA for sensitive session operations
5. **Create Admin Dashboard**: Monitor all active sessions system-wide

## 🤝 Contributing

Found an issue or have a suggestion? Please open an issue or PR in the main FastAuth repository.

## 📄 License

This example is part of the FastAuth project and follows the same license.
