# OAuth Guide

Integrate social login with Google, GitHub, and other OAuth providers.

!!! note "Installation"
    OAuth providers require the `oauth` extra:
    ```bash
    pip install sreekarnv-fastauth[oauth]
    ```

## Overview

FastAuth supports OAuth 2.0 authentication with PKCE for enhanced security. Users can:
- Sign in with existing accounts (Google, GitHub, etc.)
- Link multiple OAuth accounts to one user
- Manage connected accounts

### Supported Providers

- **Google** ✅ (with PKCE support)
- GitHub (coming soon)
- Microsoft (coming soon)

## Google OAuth Setup

### Step 1: Get Google Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Navigate to "APIs & Services" → "Credentials"
4. Click "Create Credentials" → "OAuth 2.0 Client ID"
5. Application type: "Web application"
6. Authorized redirect URIs:
   ```
   http://localhost:8000/oauth/google/callback
   ```
7. Copy your **Client ID** and **Client Secret**

### Step 2: Configure Environment

Add to `.env`:

```bash
OAUTH_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
OAUTH_GOOGLE_CLIENT_SECRET=your-client-secret
OAUTH_GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/google/callback
```

### Step 3: Setup Application

```python
from fastapi import FastAPI, Depends, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from starlette.middleware.sessions import SessionMiddleware

from fastauth.providers.google import GoogleOAuthProvider
from fastauth.core.oauth import initiate_oauth_flow, complete_oauth_flow
from fastauth.adapters.sqlalchemy import (
    SQLAlchemyUserAdapter,
    SQLAlchemyOAuthAccountAdapter,
    SQLAlchemyOAuthStateAdapter,
    SQLAlchemyRefreshTokenAdapter,
)
from fastauth.core.refresh_tokens import create_refresh_token
from fastauth.security.jwt import create_access_token

app = FastAPI()

# Required for storing PKCE code_verifier
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key",
)

# Initialize Google provider
google_provider = GoogleOAuthProvider(
    client_id="your-client-id",
    client_secret="your-client-secret",
)

@app.get("/oauth/google/authorize")
async def google_authorize(
    request: Request,
    session: Session = Depends(get_session),
):
    """Initiate Google OAuth flow."""
    oauth_state_adapter = SQLAlchemyOAuthStateAdapter(session)

    authorization_url, state_token, code_verifier = initiate_oauth_flow(
        states=oauth_state_adapter,
        provider=google_provider,
        redirect_uri="http://localhost:8000/oauth/google/callback",
    )

    # Store code_verifier in session for PKCE
    request.session["oauth_code_verifier"] = code_verifier
    request.session["oauth_state"] = state_token

    return RedirectResponse(url=authorization_url)


@app.get("/oauth/google/callback")
async def google_callback(
    request: Request,
    code: str,
    state: str,
    session: Session = Depends(get_session),
):
    """Handle Google OAuth callback."""
    user_adapter = SQLAlchemyUserAdapter(session)
    oauth_account_adapter = SQLAlchemyOAuthAccountAdapter(session)
    oauth_state_adapter = SQLAlchemyOAuthStateAdapter(session)
    refresh_token_adapter = SQLAlchemyRefreshTokenAdapter(session)

    code_verifier = request.session.get("oauth_code_verifier")

    user, is_new_user = await complete_oauth_flow(
        states=oauth_state_adapter,
        oauth_accounts=oauth_account_adapter,
        users=user_adapter,
        provider=google_provider,
        code=code,
        state=state,
        code_verifier=code_verifier,
    )

    # Clean up session
    request.session.pop("oauth_code_verifier", None)
    request.session.pop("oauth_state", None)

    # Generate tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(
        refresh_tokens=refresh_token_adapter,
        user_id=user.id,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "is_new_user": is_new_user,
    }
```

### Step 4: Test

1. Start your app: `uvicorn main:app --reload`
2. Visit `http://localhost:8000/oauth/google/authorize`
3. Complete Google sign-in
4. You'll be redirected with tokens

## OAuth Flow

```
1. User → GET /oauth/google/authorize
   ↓
2. Backend generates state & PKCE verifier
   Backend stores state in DB, verifier in session
   Backend returns Google authorization URL
   ↓
3. User redirected to Google consent screen
   ↓
4. User approves access
   ↓
5. Google → GET /oauth/google/callback?code=...&state=...
   ↓
6. Backend validates state
   Backend exchanges code + verifier for access token
   Backend fetches user info from Google
   Backend creates/links user account
   ↓
7. Backend returns JWT tokens
```

## Managing OAuth Accounts

### List Linked Accounts

```python
from fastauth.core.oauth import get_linked_accounts

@app.get("/oauth-accounts")
def list_oauth_accounts(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    oauth_account_adapter = SQLAlchemyOAuthAccountAdapter(session)
    accounts = get_linked_accounts(
        oauth_accounts=oauth_account_adapter,
        user_id=current_user.id,
    )
    return {"accounts": accounts}
```

### Unlink Account

```python
from fastauth.core.oauth import unlink_oauth_account

@app.delete("/oauth-accounts/{account_id}")
def unlink_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    oauth_account_adapter = SQLAlchemyOAuthAccountAdapter(session)

    unlink_oauth_account(
        oauth_accounts=oauth_account_adapter,
        user_id=current_user.id,
        account_id=account_id,
    )

    return {"message": "Account unlinked"}
```

## Security: PKCE

FastAuth uses **PKCE** (Proof Key for Code Exchange) for enhanced security:

1. **Code Verifier**: Random string stored in session
2. **Code Challenge**: SHA-256 hash of verifier, sent to OAuth provider
3. **Validation**: Provider validates challenge when exchanging code for token

This prevents authorization code interception attacks.

## Frontend Integration

### React Example

```javascript
// Trigger OAuth flow
const handleGoogleLogin = () => {
  window.location.href = 'http://localhost:8000/oauth/google/authorize';
};

// Handle callback (on redirect page)
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const accessToken = params.get('access_token');
  const refreshToken = params.get('refresh_token');

  if (accessToken) {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    // Redirect to dashboard
  }
}, []);
```

## Production Considerations

### Redirect URI

Update your `.env` for production:

```bash
OAUTH_GOOGLE_REDIRECT_URI=https://yourdomain.com/oauth/google/callback
```

Add to Google Cloud Console authorized redirect URIs:
```
https://yourdomain.com/oauth/google/callback
```

### Session Security

Use a strong secret key:

```python
import secrets

app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32),  # Generate and store securely
    https_only=True,  # Production only
    same_site="lax",
)
```

### Error Handling

```python
from fastapi import HTTPException

@app.get("/oauth/google/callback")
async def google_callback(code: str, state: str, session: Session):
    try:
        user, is_new = await complete_oauth_flow(...)
        return {"access_token": ..., "refresh_token": ...}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="OAuth flow failed")
```

## Common Issues

### "Invalid redirect_uri"

**Cause**: Redirect URI mismatch between code and Google Console.

**Solution**: Ensure `.env` redirect URI matches Google Console exactly.

### "Missing code_verifier"

**Cause**: Session lost between authorize and callback.

**Solution**: Ensure `SessionMiddleware` is configured and cookies are enabled.

### "State token not found"

**Cause**: State token expired or database issue.

**Solution**: Check `OAUTH_STATE_EXPIRE_MINUTES` setting (default: 10 minutes).

## Complete Example

See the [OAuth Google Example](https://github.com/sreekarnv/fastauth/tree/main/examples/oauth-google) for a full working implementation with:
- Google OAuth integration
- PKCE flow
- Account linking/unlinking
- HTML templates
- Complete setup instructions

## Next Steps

- **[Authentication](authentication.md)** - Traditional email/password auth
- **[Sessions](sessions.md)** - Track user sessions
- **[OAuth Example](https://github.com/sreekarnv/fastauth/tree/main/examples/oauth-google)** - Complete working example
