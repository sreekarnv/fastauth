# OAuth with Google Example

This example demonstrates how to integrate **Google OAuth (Sign in with Google)** using FastAuth.

## 🎯 What This Example Demonstrates

- ✅ **Google OAuth Login Flow** - Complete OAuth 2.0 authorization code flow with PKCE
- ✅ **Automatic User Creation** - Create users automatically from OAuth profile
- ✅ **Account Linking** - Link OAuth accounts to existing users
- ✅ **Account Unlinking** - Remove OAuth connections
- ✅ **Profile Management** - View user profile with linked OAuth accounts
- ✅ **Secure State Management** - CSRF protection with state tokens

## 📋 Prerequisites

- Python 3.11+
- Google Cloud account (free tier is sufficient)
- Basic understanding of OAuth 2.0

## 🚀 Quick Start

### Step 1: Set Up Google OAuth Console

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/

2. **Create a New Project** (or select existing):
   - Click "Select a Project" → "New Project"
   - Name: `FastAuth OAuth Example`
   - Click "Create"

3. **Enable Google+ API:**
   - Navigate to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click "Enable"

4. **Configure OAuth Consent Screen:**
   - Go to "APIs & Services" → "OAuth consent screen"
   - User Type: **External**
   - Click "Create"
   - Fill in:
     - **App name:** FastAuth OAuth Example
     - **User support email:** Your email
     - **Developer contact:** Your email
   - Click "Save and Continue"
   - Scopes: Click "Save and Continue" (use defaults)
   - Test users: Add your Gmail address
   - Click "Save and Continue"

5. **Create OAuth 2.0 Credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: **Web application**
   - Name: `FastAuth Example`
   - **Authorized redirect URIs:**
     ```
     http://localhost:8000/oauth/google/callback
     ```
   - Click "Create"
   - **Copy** the `Client ID` and `Client Secret` (you'll need these!)

### Step 2: Install Dependencies

```bash
# Navigate to this example directory
cd examples/oauth-google

# Install FastAuth with OAuth support (required for Google OAuth)
pip install sreekarnv-fastauth[oauth]

# Install FastAPI (peer dependency) and uvicorn
pip install fastapi uvicorn[standard] itsdangerous

# OR install from parent directory (for development)
pip install -e ../..
pip install fastapi uvicorn[standard] itsdangerous

# OR install all dependencies from requirements.txt
pip install -r requirements.txt
```

> **Note:** The `[oauth]` extra is required for OAuth providers. FastAPI is a peer dependency.

### Step 3: Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Google OAuth credentials
# Use the Client ID and Client Secret from Step 1
```

Your `.env` should look like:
```bash
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/google/callback
JWT_SECRET_KEY=your-strong-secret-key-here
```

**🔐 Security Note:** Never commit your `.env` file to version control!

### Step 4: Run the Application

```bash
# Run the FastAPI app
uvicorn app.main:app --reload
```

The application will start at: **http://localhost:8000**

### Step 5: Test OAuth Flow

1. **Open your browser:** http://localhost:8000

2. **Click "Sign in with Google"**

3. **Authorize the app:**
   - You'll be redirected to Google's consent screen
   - Select your Google account
   - Click "Allow"

4. **Success!**
   - You'll be redirected back to the app
   - Your profile will be created automatically
   - You'll receive JWT tokens

5. **View your profile:**
   - Click "View Profile" to see your user information
   - Click "View Linked Accounts" to see your Google OAuth connection

## 📖 How It Works

### OAuth Flow Diagram

```
┌─────────┐         ┌──────────┐         ┌────────────┐
│ Browser │         │ FastAuth │         │   Google   │
└────┬────┘         └─────┬────┘         └──────┬─────┘
     │                    │                     │
     │ 1. Click Login    │                     │
     ├──────────────────►│                     │
     │                    │ 2. Generate State  │
     │                    │    + Redirect      │
     │                    ├────────────────────►│
     │                    │                     │
     │ 3. User consents   │                     │
     │◄───────────────────┼─────────────────────┤
     │                    │                     │
     │ 4. Callback        │                     │
     ├──────────────────►│                     │
     │                    │ 5. Exchange code   │
     │                    ├────────────────────►│
     │                    │                     │
     │                    │ 6. Access token    │
     │                    │◄────────────────────┤
     │                    │ 7. Fetch profile   │
     │                    ├────────────────────►│
     │                    │                     │
     │                    │ 8. User info       │
     │                    │◄────────────────────┤
     │                    │ 9. Create/link user│
     │ 10. JWT tokens     │                     │
     │◄───────────────────┤                     │
     │                    │                     │
```

### Code Walkthrough

**1. Initiate OAuth Flow** (`GET /oauth/google/authorize`):
```python
# Generate state token for CSRF protection
authorization_url = initiate_oauth_flow(
    provider=google_provider,
    oauth_state_adapter=oauth_state_adapter,
)
# Redirects to Google's consent screen
```

**2. Handle Callback** (`GET /oauth/google/callback`):
```python
# Validate state, exchange code for tokens, create/link user
result = await complete_oauth_flow(
    provider=google_provider,
    code=code,
    state=state,
    user_adapter=user_adapter,
    oauth_account_adapter=oauth_account_adapter,
    oauth_state_adapter=oauth_state_adapter,
    settings=fastauth_settings,
)
# Returns: access_token, refresh_token, user
```

**3. List Linked Accounts** (`GET /oauth-accounts`):
```python
accounts = get_linked_accounts(
    user_id=user_id,
    oauth_account_adapter=oauth_account_adapter,
)
```

**4. Unlink Account** (`DELETE /oauth-accounts/{id}`):
```python
unlink_oauth_account(
    user_id=user_id,
    account_id=account_id,
    oauth_account_adapter=oauth_account_adapter,
)
```

## 🔧 Available Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Home page with login button | No |
| GET | `/oauth/google/authorize` | Initiate Google OAuth flow | No |
| GET | `/oauth/google/callback` | Handle OAuth callback | No |
| GET | `/oauth-accounts` | List linked OAuth accounts | Yes |
| GET | `/oauth-accounts/{id}/unlink` | Unlink OAuth account | Yes |
| GET | `/profile` | View user profile | Yes |
| GET | `/docs` | Interactive API documentation | No |

## 🧪 Testing the Example

### Test 1: New User Registration
1. Click "Sign in with Google"
2. Authorize with a Google account that hasn't been used before
3. A new user should be created
4. You should receive JWT tokens

### Test 2: Existing User Login
1. Sign in with the same Google account again
2. You should be logged in (no new user created)
3. You should receive new JWT tokens

### Test 3: View Linked Accounts
1. After logging in, copy the access token from the success page
2. Visit: `/oauth-accounts?access_token=YOUR_TOKEN`
3. You should see your Google account listed

### Test 4: Unlink Account
1. From the linked accounts page, click "Unlink"
2. The OAuth connection should be removed
3. You can still log in with the same Google account (it will re-link)

## 📝 Database Schema

The example uses SQLite and creates these tables:

- `users` - User accounts
- `oauth_accounts` - OAuth account linkages
- `oauth_states` - Temporary state tokens for CSRF protection
- `refresh_tokens` - JWT refresh tokens
- `email_verification_tokens` - Email verification (not used in this example)
- `password_reset_tokens` - Password reset (not used in this example)

View the database:
```bash
sqlite3 oauth_example.db
.tables
.schema oauth_accounts
```

## 🔐 Security Features

This example demonstrates FastAuth's built-in security:

✅ **CSRF Protection** - State tokens prevent cross-site request forgery
✅ **PKCE Support** - Proof Key for Code Exchange for added security
✅ **Token Hashing** - OAuth tokens are hashed before storage
✅ **State Expiration** - State tokens expire after 10 minutes
✅ **Secure Redirects** - Validates redirect URIs

## 🚀 Production Deployment

### Before deploying to production:

1. **Use HTTPS:**
   ```bash
   GOOGLE_REDIRECT_URI=https://yourdomain.com/oauth/google/callback
   ```

2. **Update Google OAuth Console:**
   - Add your production URL to authorized redirect URIs
   - Remove localhost from authorized URIs (or keep for testing)

3. **Use Strong Secret:**
   ```bash
   # Generate a strong JWT secret
   openssl rand -hex 32
   ```

4. **Use Production Database:**
   ```bash
   # PostgreSQL example
   DATABASE_URL=postgresql://user:pass@localhost/dbname
   ```

5. **Enable Email Verification:**
   ```bash
   REQUIRE_EMAIL_VERIFICATION=true
   EMAIL_BACKEND=smtp
   SMTP_HOST=smtp.gmail.com
   # ... SMTP settings
   ```

6. **Store Tokens Securely:**
   - Use httpOnly cookies instead of query parameters
   - Implement refresh token rotation
   - Add token expiration handling

## 🎨 Customization

### Add More OAuth Providers

FastAuth supports multiple OAuth providers. To add GitHub:

```python
from fastauth.providers.github import GitHubOAuthProvider

github_provider = GitHubOAuthProvider(
    client_id=settings.github_client_id,
    client_secret=settings.github_client_secret,
    redirect_uri="http://localhost:8000/oauth/github/callback",
)
```

### Customize User Creation

You can customize what happens when a user logs in via OAuth:

```python
# In your callback handler, you can access the OAuth user info:
result = await complete_oauth_flow(...)

# The result contains:
# - user: The created/existing user
# - access_token: JWT access token
# - refresh_token: JWT refresh token
# - oauth_account: The linked OAuth account
```

## 📚 Next Steps

- **Add More Providers:** Try adding GitHub, Microsoft, or other providers
- **Build a Frontend:** Create a React/Vue frontend that consumes these APIs
- **Add RBAC:** Combine OAuth with role-based access control (see `examples/rbac-blog`)
- **Session Management:** Add session tracking (see `examples/session-devices`)

## 🐛 Troubleshooting

### "redirect_uri_mismatch" Error

**Problem:** Google OAuth returns an error about redirect URI mismatch.

**Solution:**
1. Check your `.env` file - `GOOGLE_REDIRECT_URI` must exactly match what you configured in Google Console
2. In Google Console, make sure you added: `http://localhost:8000/oauth/google/callback`
3. No trailing slashes!

### "invalid_client" Error

**Problem:** Google OAuth returns invalid client error.

**Solution:**
1. Double-check your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
2. Make sure you copied them correctly from Google Console
3. No extra spaces or quotes in the `.env` file

### "Access blocked" by Google

**Problem:** Google shows "This app is blocked" message.

**Solution:**
1. In Google Console, make sure your OAuth consent screen is configured
2. Add your email as a test user in OAuth consent screen
3. For production, you'll need to verify your app (requires domain ownership)

### Database Errors

**Problem:** SQLAlchemy errors about tables not existing.

**Solution:**
1. Delete the database file: `rm oauth_example.db`
2. Restart the application (tables will be recreated automatically)

## 📖 Additional Resources

- [FastAuth Documentation](https://sreekarnv.github.io/fastauth/)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [OAuth 2.0 RFC](https://datatracker.ietf.org/doc/html/rfc6749)
- [FastAPI OAuth Documentation](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)

## 💡 Tips

- **Development:** The example shows tokens in URLs for simplicity. In production, use httpOnly cookies.
- **Testing:** You can use multiple Google accounts to test the flow.
- **Debugging:** Set `echo=True` in `database.py` to see SQL queries.
- **API Testing:** Use the `/docs` endpoint for interactive API documentation.

## 📄 License

This example is part of the FastAuth project and is licensed under the MIT License.

---

**Built with [FastAuth](https://github.com/sreekarnv/fastauth)** - Production-ready authentication for FastAPI
