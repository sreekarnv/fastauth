# Manual Testing Checklist

This guide provides a complete checklist for manually testing all FastAuth endpoints before publishing to PyPI.

## Prerequisites

1. **Start the application**:
```bash
uvicorn main:app --reload
```

2. **Access Swagger UI**: http://localhost:8000/docs

3. **Have these ready**:
   - Email for testing (e.g., test@example.com)
   - Strong password
   - Notepad for saving tokens

## Testing Order

Follow this order to test all features systematically.

---

## 1. Authentication Endpoints

### ✅ Register User

**Endpoint**: `POST /auth/register`

**Request**:
```json
{
  "email": "test@example.com",
  "password": "SecurePass123!"
}
```

**Expected Response** (201):
```json
{
  "id": "uuid",
  "email": "test@example.com",
  "is_verified": false,
  "is_active": true,
  "created_at": "2025-12-29T..."
}
```

**Verify**:
- [ ] User created successfully
- [ ] Email is correct
- [ ] is_verified is false (if email verification enabled)
- [ ] is_active is true

**Edge Cases**:
- [ ] Try registering same email again → 400 "User already exists"
- [ ] Try invalid email format → 422 validation error
- [ ] Try weak password → Should succeed (no password strength validation by default)

---

### ✅ Login

**Endpoint**: `POST /auth/login`

**Request**:
```json
{
  "email": "test@example.com",
  "password": "SecurePass123!"
}
```

**Expected Response** (200):
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Verify**:
- [ ] Tokens received
- [ ] Token type is "bearer"

**Save**:
- Access token → Use for authenticated requests
- Refresh token → Use for token refresh

**Edge Cases**:
- [ ] Wrong password → 401 "Invalid credentials"
- [ ] Non-existent email → 401 "Invalid credentials"
- [ ] If email verification enabled and not verified → 403 "Email not verified"

---

### ✅ Email Verification (if enabled)

**Endpoint**: `POST /auth/email-verification/resend`

**Request**:
```json
{
  "email": "test@example.com"
}
```

**Expected Response** (200):
```json
{
  "message": "Verification email sent",
  "token": "verification-token-string"
}
```

**Note**: In console email provider, token is returned. In production, it's sent via email.

**Save**: Verification token

**Verify**:
- [ ] Token received (console mode)
- [ ] Or check email (SMTP mode)

---

**Endpoint**: `POST /auth/email-verification/confirm`

**Request**:
```json
{
  "token": "your-verification-token"
}
```

**Expected Response** (200):
```json
{
  "message": "Email verified successfully"
}
```

**Verify**:
- [ ] Email verified
- [ ] Can now login if was blocked before

**Edge Cases**:
- [ ] Invalid token → 400 "Invalid token"
- [ ] Already verified → Should still succeed
- [ ] Expired token → 400 "Token expired"

---

### ✅ Refresh Token

**Endpoint**: `POST /auth/refresh`

**Request**:
```json
{
  "refresh_token": "your-refresh-token"
}
```

**Expected Response** (200):
```json
{
  "access_token": "new-access-token",
  "refresh_token": "new-refresh-token",
  "token_type": "bearer"
}
```

**Verify**:
- [ ] New tokens received
- [ ] Old refresh token is invalidated (try using it again → 401)

**Update**: Save new tokens

---

### ✅ Password Reset Request

**Endpoint**: `POST /auth/password-reset/request`

**Request**:
```json
{
  "email": "test@example.com"
}
```

**Expected Response** (200):
```json
{
  "message": "Password reset email sent"
}
```

**Verify**:
- [ ] Success message received
- [ ] Check console/email for reset token

**Note**: Even for non-existent emails, returns 200 (security: don't reveal if email exists)

**Save**: Reset token

---

### ✅ Password Reset Confirm

**Endpoint**: `POST /auth/password-reset/confirm`

**Request**:
```json
{
  "token": "reset-token",
  "new_password": "NewSecurePass456!"
}
```

**Expected Response** (200):
```json
{
  "message": "Password reset successful"
}
```

**Verify**:
- [ ] Password changed
- [ ] Can login with new password
- [ ] Cannot login with old password
- [ ] Old tokens are invalidated

**Edge Cases**:
- [ ] Invalid token → 400 "Invalid token"
- [ ] Expired token → 400 "Token expired"
- [ ] Using same token twice → 400 "Token already used"

---

### ✅ Logout

**Endpoint**: `POST /auth/logout`

**Headers**: None (doesn't require authentication)

**Request**:
```json
{
  "refresh_token": "your-refresh-token"
}
```

**Expected Response** (200):
```json
{
  "message": "Logged out successfully"
}
```

**Verify**:
- [ ] Success message
- [ ] Refresh token is revoked (try using it → 401)
- [ ] Access token still works until expiry

---

## 2. Session Management Endpoints

**Setup**: Login to get access token

### ✅ List Sessions

**Endpoint**: `GET /sessions`

**Headers**:
```
Authorization: Bearer your-access-token
```

**Expected Response** (200):
```json
{
  "sessions": [
    {
      "id": "uuid",
      "device": null,
      "ip_address": "127.0.0.1",
      "user_agent": "python-requests/...",
      "last_active": "2025-12-29T...",
      "created_at": "2025-12-29T..."
    }
  ]
}
```

**Verify**:
- [ ] At least one session returned
- [ ] Session has created_at and last_active timestamps
- [ ] Session ID is valid UUID

---

### ✅ Delete Specific Session

**Endpoint**: `DELETE /sessions/{session_id}`

**Setup**: Create second session (login from different client/browser)

**Headers**:
```
Authorization: Bearer your-access-token
```

**Expected Response** (200):
```json
{
  "message": "Session deleted successfully"
}
```

**Verify**:
- [ ] Session deleted
- [ ] Session no longer appears in list
- [ ] Other sessions still active

**Edge Cases**:
- [ ] Invalid session ID → 404 "Session not found"
- [ ] Deleting another user's session → 404 "Session not found"

---

### ✅ Delete All Sessions

**Endpoint**: `DELETE /sessions/all`

**Headers**:
```
Authorization: Bearer your-access-token
```

**Expected Response** (200):
```json
{
  "message": "All sessions deleted successfully"
}
```

**Verify**:
- [ ] All sessions deleted
- [ ] Session list is empty
- [ ] Current access token still works (stateless JWT)

---

## 3. Account Management Endpoints

**Setup**: Login to get access token

### ✅ Change Password

**Endpoint**: `POST /account/change-password`

**Headers**:
```
Authorization: Bearer your-access-token
```

**Request**:
```json
{
  "current_password": "SecurePass123!",
  "new_password": "NewPassword789!"
}
```

**Expected Response** (200):
```json
{
  "message": "Password changed successfully"
}
```

**Verify**:
- [ ] Password changed
- [ ] Can login with new password
- [ ] Cannot login with old password
- [ ] All sessions except current are invalidated

**Edge Cases**:
- [ ] Wrong current password → 400 "Invalid password"
- [ ] No authentication → 401 "Unauthorized"

---

### ✅ Request Email Change

**Endpoint**: `POST /account/request-email-change`

**Headers**:
```
Authorization: Bearer your-access-token
```

**Request**:
```json
{
  "new_email": "newemail@example.com"
}
```

**Expected Response** (200):
```json
{
  "message": "Email change requested. Please verify the token to complete the change.",
  "token": "email-change-token"
}
```

**Save**: Email change token

**Verify**:
- [ ] Token received
- [ ] Email not changed yet (still old email)

**Edge Cases**:
- [ ] Email already exists → 400 "Email already exists"

---

### ✅ Confirm Email Change

**Endpoint**: `POST /account/confirm-email-change`

**Request** (no auth required):
```json
{
  "token": "email-change-token"
}
```

**Expected Response** (200):
```json
{
  "message": "Email changed successfully"
}
```

**Verify**:
- [ ] Email changed
- [ ] Login with new email works
- [ ] Login with old email fails
- [ ] is_verified reset to false (need to verify new email)

**Edge Cases**:
- [ ] Invalid token → 400 "Invalid token"
- [ ] Email taken by another user after request → 400 "Email no longer available"

---

### ✅ Delete Account (Soft Delete)

**Endpoint**: `DELETE /account/delete`

**Headers**:
```
Authorization: Bearer your-access-token
```

**Request**:
```json
{
  "password": "your-password",
  "hard_delete": false
}
```

**Expected Response** (200):
```json
{
  "message": "Account deactivated successfully"
}
```

**Verify**:
- [ ] Account deactivated (is_active = false)
- [ ] Cannot login anymore
- [ ] User still exists in database (soft delete)
- [ ] All sessions invalidated

---

### ✅ Delete Account (Hard Delete)

**Setup**: Register a new test user

**Endpoint**: `DELETE /account/delete`

**Headers**:
```
Authorization: Bearer your-access-token
```

**Request**:
```json
{
  "password": "your-password",
  "hard_delete": true
}
```

**Expected Response** (200):
```json
{
  "message": "Account permanently deleted successfully"
}
```

**Verify**:
- [ ] Account permanently deleted
- [ ] Cannot login
- [ ] User removed from database
- [ ] All sessions invalidated

**Edge Cases**:
- [ ] Wrong password → 400 "Invalid password"

---

## 4. Role-Based Access Control (RBAC)

**Setup**: Create admin role and assign to user (via code/script)

### ✅ Create Test Roles

Run this setup script:

```python
from sqlmodel import Session, create_engine
from fastauth.adapters.sqlalchemy import SQLAlchemyRoleAdapter, SQLAlchemyUserAdapter
from fastauth.core.roles import create_role, create_permission, assign_role, assign_permission_to_role

engine = create_engine("sqlite:///./app.db")
with Session(engine) as session:
    roles = SQLAlchemyRoleAdapter(session)
    users = SQLAlchemyUserAdapter(session)

    # Create roles
    admin_role = create_role(roles, "admin", "Administrator")
    user_role = create_role(roles, "user", "Regular User")

    # Create permissions
    delete_users = create_permission(roles, "delete:users", "Delete users")
    view_users = create_permission(roles, "view:users", "View users")

    # Assign permissions to roles
    assign_permission_to_role(roles, "admin", "delete:users")
    assign_permission_to_role(roles, "admin", "view:users")
    assign_permission_to_role(roles, "user", "view:users")

    # Assign admin role to test user
    user = users.get_by_email("test@example.com")
    assign_role(roles, user.id, "admin")

    session.commit()
    print("Roles and permissions created!")
```

### ✅ Test Protected Route (Role)

**Setup**: Create a test endpoint

```python
from fastauth.api.dependencies import require_role

@app.get("/admin/dashboard", dependencies=[Depends(require_role("admin"))])
def admin_dashboard():
    return {"message": "Admin access granted"}
```

**Test**:
- [ ] With admin user → 200 OK
- [ ] Without admin role → 403 "Insufficient permissions"
- [ ] Without authentication → 401 "Unauthorized"

---

### ✅ Test Protected Route (Permission)

**Setup**: Create a test endpoint

```python
from fastauth.api.dependencies import require_permission

@app.delete("/admin/users/{id}", dependencies=[Depends(require_permission("delete:users"))])
def delete_user(id: str):
    return {"message": f"User {id} deleted"}
```

**Test**:
- [ ] With delete:users permission → 200 OK
- [ ] Without permission → 403 "Insufficient permissions"
- [ ] Without authentication → 401 "Unauthorized"

---

## 5. OAuth 2.0 Endpoints

**Setup**: Configure Google OAuth credentials in .env

### ✅ Initiate OAuth Flow

**Endpoint**: `POST /oauth/google/authorize`

**Request**:
```json
{
  "redirect_uri": "http://localhost:8000/callback",
  "use_pkce": true
}
```

**Expected Response** (200):
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "random-state-token"
}
```

**Save**: State token

**Verify**:
- [ ] Authorization URL received
- [ ] URL contains client_id, redirect_uri, state
- [ ] URL contains code_challenge if PKCE enabled

**Test**: Open authorization_url in browser

---

### ✅ Complete OAuth Flow

**Manual Steps**:
1. Open authorization URL in browser
2. Login with Google
3. Grant permissions
4. Copy `code` and `state` from redirect URL

**Endpoint**: `POST /oauth/google/callback`

**Request**:
```json
{
  "code": "authorization-code-from-google",
  "state": "state-token-from-authorize"
}
```

**Expected Response** (200):
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "googleuser@gmail.com",
    "is_verified": true,
    "is_active": true
  }
}
```

**Verify**:
- [ ] User created or logged in
- [ ] JWT tokens received
- [ ] Email is verified (OAuth emails pre-verified)
- [ ] OAuth account linked

**Edge Cases**:
- [ ] Invalid state → 400 "Invalid state"
- [ ] Expired state → 400 "State expired"
- [ ] Invalid code → 400 "Code exchange failed"

---

### ✅ List Linked OAuth Accounts

**Endpoint**: `GET /oauth/accounts`

**Headers**:
```
Authorization: Bearer your-access-token
```

**Expected Response** (200):
```json
{
  "accounts": [
    {
      "id": "uuid",
      "provider": "google",
      "provider_user_id": "google_user_id",
      "created_at": "2025-12-29T..."
    }
  ]
}
```

**Verify**:
- [ ] OAuth account listed
- [ ] Correct provider name
- [ ] Has provider_user_id

---

### ✅ Unlink OAuth Account

**Endpoint**: `DELETE /oauth/accounts/{account_id}`

**Headers**:
```
Authorization: Bearer your-access-token
```

**Expected Response** (200):
```json
{
  "message": "OAuth account unlinked successfully"
}
```

**Verify**:
- [ ] Account unlinked
- [ ] No longer appears in list
- [ ] User still exists (if has password or other OAuth)

**Edge Cases**:
- [ ] Invalid account ID → 404 "Account not found"
- [ ] Unlinking another user's account → 404 "Account not found"

---

## 6. Error Handling

### ✅ Test Common Errors

**Invalid JSON**:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d 'invalid-json'
```
- [ ] Returns 422 validation error

**Missing Required Fields**:
```json
{
  "email": "test@example.com"
  // missing password
}
```
- [ ] Returns 422 validation error

**Invalid Token Format**:
```
Authorization: Bearer invalid-token-format
```
- [ ] Returns 401 "Invalid token"

**Expired Access Token**:
Wait for token to expire or manually create expired token
- [ ] Returns 401 "Token expired"

**No Authentication**:
Access protected route without token
- [ ] Returns 401 "Not authenticated"

---

## 7. Rate Limiting

**Test**: Make multiple failed login attempts

```bash
for i in {1..10}; do
  curl -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"wrong"}'
done
```

**Verify**:
- [ ] After 5 attempts → 429 "Rate limit exceeded"
- [ ] After waiting → Can retry

---

## Testing Checklist Summary

### Authentication (8 endpoints)
- [ ] Register user
- [ ] Login
- [ ] Email verification (resend)
- [ ] Email verification (confirm)
- [ ] Refresh token
- [ ] Password reset (request)
- [ ] Password reset (confirm)
- [ ] Logout

### Sessions (3 endpoints)
- [ ] List sessions
- [ ] Delete specific session
- [ ] Delete all sessions

### Account Management (4 endpoints)
- [ ] Change password
- [ ] Request email change
- [ ] Confirm email change
- [ ] Delete account (soft + hard)

### RBAC (2 custom endpoints)
- [ ] Protected route with role
- [ ] Protected route with permission

### OAuth (3 endpoints)
- [ ] Initiate OAuth flow
- [ ] Complete OAuth callback
- [ ] List linked accounts
- [ ] Unlink OAuth account

### Error Handling
- [ ] Invalid JSON
- [ ] Missing fields
- [ ] Invalid tokens
- [ ] Expired tokens
- [ ] No authentication
- [ ] Rate limiting

---

## Post-Testing Checklist

Before publishing to PyPI:

- [ ] All endpoints tested and working
- [ ] All edge cases handled correctly
- [ ] Error messages are clear and helpful
- [ ] Rate limiting works
- [ ] OAuth flow works end-to-end
- [ ] Database operations successful
- [ ] No console errors or warnings
- [ ] Automated tests still passing (195 tests)
- [ ] Coverage still at 85%+
- [ ] Documentation is accurate
- [ ] CHANGELOG updated
- [ ] Version number bumped in pyproject.toml

**Once everything passes, you're ready to publish to PyPI!** 🚀
