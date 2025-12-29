# OAuth 2.0 Authentication Guide

FastAuth provides built-in OAuth 2.0 authentication support, allowing users to sign in with popular providers like Google. This guide covers setup, configuration, and usage of OAuth features.

## Overview

OAuth 2.0 enables users to:
- Sign in with existing accounts (Google, GitHub, etc.)
- Link multiple OAuth accounts to one user
- Manage connected accounts
- Use PKCE for enhanced security

### Supported Providers

Currently supported:
- **Google** ✅ (with PKCE support)

Coming soon:
- GitHub
- Microsoft
- Facebook
- Twitter/X

## Quick Start

### 1. Configure OAuth Provider

#### Google OAuth Setup

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable "Google+ API"

2. **Create OAuth 2.0 Credentials**:
   - Navigate to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Application type: "Web application"
   - Authorized redirect URIs:
     ```
     http://localhost:8000/auth/oauth/google/callback  # Development
     https://yourdomain.com/auth/oauth/google/callback  # Production
     ```

3. **Get Credentials**:
   - Copy **Client ID**
   - Copy **Client Secret**

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# OAuth Configuration
OAUTH_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
OAUTH_GOOGLE_CLIENT_SECRET=your-client-secret
OAUTH_GOOGLE_REDIRECT_URI=http://localhost:8000/auth/oauth/google/callback

# OAuth state token expiration (minutes)
OAUTH_STATE_EXPIRE_MINUTES=10
```

### 3. Include OAuth Router

```python
from fastapi import FastAPI
from fastauth import auth_router, oauth_router

app = FastAPI()

# Include OAuth router
app.include_router(oauth_router)
app.include_router(auth_router)
```

### 4. Test OAuth Flow

```bash
# Start your application
uvicorn main:app --reload

# Navigate to:
# http://localhost:8000/docs

# Test the OAuth endpoints:
# 1. POST /oauth/google/authorize
# 2. POST /oauth/google/callback
```

## OAuth Flow

### Authorization Flow Diagram

```
1. User clicks "Sign in with Google"
   ↓
2. Frontend: POST /oauth/google/authorize
   Backend: Generates state token (CSRF protection)
   Backend: Returns authorization URL
   ↓
3. Frontend: Redirect user to authorization URL
   ↓
4. User: Authenticates with Google
   User: Grants permissions
   ↓
5. Google: Redirects to callback URL with code and state
   ↓
6. Frontend: POST /oauth/google/callback with code and state
   Backend: Validates state token
   Backend: Exchanges code for access token
   Backend: Fetches user info from Google
   Backend: Creates/links user account
   Backend: Returns JWT tokens
   ↓
7. User is authenticated
```

### Security Features

**State Token (CSRF Protection)**:
- Random token generated per authorization request
- Stored server-side with expiration (default: 10 minutes)
- Validated on callback to prevent CSRF attacks

**PKCE (Proof Key for Code Exchange)**:
- Optional enhanced security for public clients
- Generates code verifier and challenge
- Prevents authorization code interception attacks

**Token Encryption**:
- OAuth access/refresh tokens encrypted before storage
- Prevents token theft from database

## API Endpoints

### Initiate OAuth Flow

**Endpoint**: `POST /oauth/{provider}/authorize`

**Request**:
```json
{
  "redirect_uri": "http://localhost:8000/auth/oauth/google/callback",
  "use_pkce": true  // Optional, recommended for mobile/SPA
}
```

**Response**:
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "random-state-token"
}
```

**Usage**:
```javascript
// Frontend (JavaScript example)
async function initiateOAuth() {
  const response = await fetch('/oauth/google/authorize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      redirect_uri: window.location.origin + '/auth/callback',
      use_pkce: true
    })
  });

  const { authorization_url } = await response.json();

  // Redirect user to Google
  window.location.href = authorization_url;
}
```

### Complete OAuth Flow

**Endpoint**: `POST /oauth/{provider}/callback`

**Request**:
```json
{
  "code": "authorization-code-from-provider",
  "state": "state-token-from-authorize"
}
```

**Response**:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "is_verified": true,
    "is_active": true
  }
}
```

**Usage**:
```javascript
// Frontend callback handler
async function handleOAuthCallback() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const state = params.get('state');

  const response = await fetch('/oauth/google/callback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, state })
  });

  const { access_token, user } = await response.json();

  // Store token and redirect to app
  localStorage.setItem('token', access_token);
  window.location.href = '/dashboard';
}
```

### List Linked Accounts

**Endpoint**: `GET /oauth/accounts`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "accounts": [
    {
      "id": "uuid",
      "provider": "google",
      "provider_user_id": "google_user_123",
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

### Unlink OAuth Account

**Endpoint**: `DELETE /oauth/accounts/{account_id}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "message": "OAuth account unlinked successfully"
}
```

## Advanced Usage

### Linking OAuth to Existing Account

If a user is already logged in and wants to link an OAuth provider:

```python
# Include user_id in state data
from fastauth.api.dependencies import get_current_user

@app.post("/oauth/google/link")
async def link_google_account(
    current_user: User = Depends(get_current_user)
):
    # Initiate OAuth with user context
    result = initiate_oauth_flow(
        oauth_states=oauth_state_adapter,
        provider=google_provider,
        redirect_uri="http://localhost:8000/auth/oauth/google/callback",
        state_data={"link_user_id": str(current_user.id)},
        use_pkce=True
    )

    return result
```

During callback, the account will be linked to the existing user instead of creating a new one.

### Custom OAuth Providers

FastAuth supports custom OAuth providers. Implement the `OAuthProvider` interface:

```python
from fastauth.providers.base import OAuthProvider
import httpx

class GitHubOAuthProvider(OAuthProvider):
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_url = "https://github.com/login/oauth/authorize"
        self.token_url = "https://github.com/login/oauth/access_token"
        self.user_info_url = "https://api.github.com/user"

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        code_challenge: str | None = None
    ) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "user:email"
        }
        return f"{self.authorization_url}?{urlencode(params)}"

    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: str | None = None
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri
                },
                headers={"Accept": "application/json"}
            )
            return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.user_info_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_data = response.json()

            return {
                "provider_user_id": str(user_data["id"]),
                "email": user_data["email"],
                "name": user_data["name"]
            }
```

## Configuration

### Settings

All OAuth settings are configurable via environment variables:

```python
from fastauth import Settings

settings = Settings(
    # Google OAuth
    oauth_google_client_id="your-client-id",
    oauth_google_client_secret="your-client-secret",
    oauth_google_redirect_uri="http://localhost:8000/auth/oauth/google/callback",

    # OAuth state expiration
    oauth_state_expire_minutes=10,  # Default: 10 minutes

    # Other FastAuth settings
    jwt_secret_key="your-secret-key",
    require_email_verification=False  # OAuth emails are pre-verified
)
```

### PKCE Configuration

PKCE (Proof Key for Code Exchange) is recommended for:
- Single Page Applications (SPAs)
- Mobile applications
- Any public client that cannot securely store secrets

Enable PKCE per request:

```json
{
  "redirect_uri": "...",
  "use_pkce": true
}
```

## Database Schema

### OAuthAccount Model

```python
class OAuthAccount(SQLModel, table=True):
    id: UUID
    user_id: UUID              # Foreign key to User
    provider: str              # "google", "github", etc.
    provider_user_id: str      # User ID from OAuth provider
    access_token: str          # Encrypted access token
    refresh_token: str | None  # Encrypted refresh token
    expires_at: datetime | None
    created_at: datetime
```

### OAuthState Model

```python
class OAuthState(SQLModel, table=True):
    id: UUID
    state_hash: str            # Hashed state token
    provider: str
    redirect_uri: str
    code_verifier: str | None  # For PKCE
    state_data: dict | None    # Additional state (e.g., link_user_id)
    expires_at: datetime
    created_at: datetime
```

## Security Best Practices

### 1. Always Use HTTPS in Production

```python
# Production
oauth_google_redirect_uri="https://yourdomain.com/auth/oauth/google/callback"

# Never use HTTP in production
oauth_google_redirect_uri="http://yourdomain.com/..."  # ❌ Insecure
```

### 2. Validate Redirect URIs

Only use pre-configured redirect URIs:

```python
# Register exact URIs with OAuth provider
ALLOWED_REDIRECT_URIS = [
    "http://localhost:8000/auth/oauth/google/callback",  # Dev
    "https://yourdomain.com/auth/oauth/google/callback"  # Prod
]
```

### 3. Short State Token Expiration

Keep state tokens short-lived:

```python
# Default: 10 minutes (recommended)
oauth_state_expire_minutes=10

# Too long (security risk)
oauth_state_expire_minutes=60  # ❌ Not recommended
```

### 4. Store Secrets Securely

Never commit OAuth credentials:

```bash
# .gitignore
.env
.env.local
*.env
```

Use environment-specific configurations:

```python
# Development
OAUTH_GOOGLE_CLIENT_ID=dev-client-id

# Production (from secrets manager)
OAUTH_GOOGLE_CLIENT_ID=$(aws secretsmanager get-secret-value...)
```

### 5. Use PKCE for Public Clients

For SPAs and mobile apps, always use PKCE:

```javascript
// Frontend
const response = await fetch('/oauth/google/authorize', {
  method: 'POST',
  body: JSON.stringify({
    redirect_uri: window.location.origin + '/callback',
    use_pkce: true  // Always true for SPAs
  })
});
```

## Troubleshooting

### "Invalid state token"

**Cause**: State token expired or already used.

**Solution**: State tokens expire after 10 minutes. Ensure user completes OAuth flow quickly.

### "Redirect URI mismatch"

**Cause**: Redirect URI doesn't match what's registered with OAuth provider.

**Solution**: Ensure exact match (including protocol, domain, port, path):

```python
# Google Cloud Console
http://localhost:8000/auth/oauth/google/callback

# Your .env
OAUTH_GOOGLE_REDIRECT_URI=http://localhost:8000/auth/oauth/google/callback
```

### "Email already exists"

**Cause**: User already registered with email/password using the same email.

**Solution**: Prompt user to log in with password first, then link OAuth account.

### "OAuth provider not configured"

**Cause**: Missing OAuth credentials in environment.

**Solution**: Set required environment variables:

```bash
OAUTH_GOOGLE_CLIENT_ID=...
OAUTH_GOOGLE_CLIENT_SECRET=...
OAUTH_GOOGLE_REDIRECT_URI=...
```

## Testing OAuth

### Manual Testing

1. Start application with OAuth configured
2. Navigate to `/docs` (Swagger UI)
3. Test `POST /oauth/google/authorize`
4. Copy `authorization_url` and open in browser
5. Complete OAuth flow
6. Copy `code` and `state` from redirect
7. Test `POST /oauth/google/callback`

### Automated Testing

FastAuth includes comprehensive OAuth tests. See `tests/core/test_oauth.py` for examples:

```python
@pytest.mark.asyncio
async def test_complete_oauth_flow_new_user(session):
    # Setup
    oauth_states = SQLAlchemyOAuthStateAdapter(session)
    oauth_accounts = SQLAlchemyOAuthAccountAdapter(session)
    users = SQLAlchemyUserAdapter(session)

    # Initiate flow
    result = initiate_oauth_flow(
        oauth_states=oauth_states,
        provider=mock_provider,
        redirect_uri="http://localhost/callback",
        use_pkce=True
    )

    # Complete flow
    user, is_new = await complete_oauth_flow(
        oauth_states=oauth_states,
        oauth_accounts=oauth_accounts,
        users=users,
        provider=mock_provider,
        code="mock-code",
        state=result["state"]
    )

    assert is_new is True
    assert user.email == "oauth@example.com"
```

## Additional Resources

- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [PKCE RFC 7636](https://tools.ietf.org/html/rfc7636)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [OAuth Security Best Practices](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)
