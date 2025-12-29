# API Reference

Complete reference for FastAuth's public API.

## Core Module

### `fastauth.core.users`

User management functions.

#### `create_user(users, email, password)`

Create a new user with a hashed password.

**Parameters:**
- `users` (UserAdapter): User adapter for database operations
- `email` (str): User's email address
- `password` (str): Plain text password (will be hashed)

**Returns:**
- User object

**Raises:**
- `UserAlreadyExistsError`: If a user with the email already exists

**Example:**
```python
from fastauth.core.users import create_user
from fastauth.adapters.sqlalchemy import SQLAlchemyUserAdapter

user = create_user(
    users=user_adapter,
    email="user@example.com",
    password="securepassword123"
)
```

#### `authenticate_user(users, email, password)`

Authenticate a user by email and password.

**Parameters:**
- `users` (UserAdapter): User adapter for database operations
- `email` (str): User's email address
- `password` (str): Plain text password to verify

**Returns:**
- User object

**Raises:**
- `InvalidCredentialsError`: If email doesn't exist, password is wrong, or user is inactive
- `EmailNotVerifiedError`: If email verification is required but not completed

**Example:**
```python
from fastauth.core.users import authenticate_user

user = authenticate_user(
    users=user_adapter,
    email="user@example.com",
    password="securepassword123"
)
```

### `fastauth.core.refresh_tokens`

Refresh token management.

#### `create_refresh_token(refresh_tokens, user_id, expires_delta)`

Create a new refresh token for a user.

**Parameters:**
- `refresh_tokens` (RefreshTokenAdapter): Refresh token adapter
- `user_id` (UUID): User's unique identifier
- `expires_delta` (timedelta, optional): Token expiration time

**Returns:**
- Tuple of (token string, token hash)

#### `refresh_access_token(refresh_tokens, users, refresh_token_str)`

Generate new access token using a refresh token.

**Parameters:**
- `refresh_tokens` (RefreshTokenAdapter): Refresh token adapter
- `users` (UserAdapter): User adapter
- `refresh_token_str` (str): Refresh token string

**Returns:**
- Dict with new access_token and refresh_token

**Raises:**
- `RefreshTokenError`: If token is invalid or expired

### `fastauth.core.password_reset`

Password reset functionality.

#### `request_password_reset(users, password_resets, email)`

Request a password reset token.

**Parameters:**
- `users` (UserAdapter): User adapter
- `password_resets` (PasswordResetAdapter): Password reset adapter
- `email` (str): User's email address

**Returns:**
- Password reset token string

#### `confirm_password_reset(users, password_resets, token, new_password)`

Reset password using a valid token.

**Parameters:**
- `users` (UserAdapter): User adapter
- `password_resets` (PasswordResetAdapter): Password reset adapter
- `token` (str): Password reset token
- `new_password` (str): New password (plain text)

**Raises:**
- `PasswordResetError`: If token is invalid or expired

### `fastauth.core.email_verification`

Email verification functionality.

#### `send_verification_email(users, email_verifications, email_provider, user_id)`

Send email verification token to user.

**Parameters:**
- `users` (UserAdapter): User adapter
- `email_verifications` (EmailVerificationAdapter): Email verification adapter
- `email_provider`: Email provider instance
- `user_id` (UUID): User's unique identifier

**Returns:**
- Verification token string

#### `verify_email(users, email_verifications, token)`

Verify user's email with token.

**Parameters:**
- `users` (UserAdapter): User adapter
- `email_verifications` (EmailVerificationAdapter): Email verification adapter
- `token` (str): Verification token

**Raises:**
- `EmailVerificationError`: If token is invalid or expired

### `fastauth.core.roles`

Role-Based Access Control (RBAC) functions.

#### `create_role(roles, name, description)`

Create a new role.

**Parameters:**
- `roles` (RoleAdapter): Role adapter for database operations
- `name` (str): Unique role name
- `description` (str, optional): Role description

**Returns:**
- Role object

**Raises:**
- `RoleAlreadyExistsError`: If a role with the name already exists

**Example:**
```python
from fastauth.core.roles import create_role

admin_role = create_role(
    roles=role_adapter,
    name="admin",
    description="Administrator role"
)
```

#### `create_permission(roles, name, description)`

Create a new permission.

**Parameters:**
- `roles` (RoleAdapter): Role adapter for database operations
- `name` (str): Unique permission name
- `description` (str, optional): Permission description

**Returns:**
- Permission object

**Raises:**
- `PermissionAlreadyExistsError`: If a permission with the name already exists

#### `assign_role(roles, user_id, role_name)`

Assign a role to a user.

**Parameters:**
- `roles` (RoleAdapter): Role adapter for database operations
- `user_id` (UUID): User's unique identifier
- `role_name` (str): Name of the role to assign

**Raises:**
- `RoleNotFoundError`: If the role does not exist

**Example:**
```python
from fastauth.core.roles import assign_role

assign_role(
    roles=role_adapter,
    user_id=user.id,
    role_name="admin"
)
```

#### `remove_role(roles, user_id, role_name)`

Remove a role from a user.

**Parameters:**
- `roles` (RoleAdapter): Role adapter for database operations
- `user_id` (UUID): User's unique identifier
- `role_name` (str): Name of the role to remove

**Raises:**
- `RoleNotFoundError`: If the role does not exist

#### `assign_permission_to_role(roles, role_name, permission_name)`

Assign a permission to a role.

**Parameters:**
- `roles` (RoleAdapter): Role adapter for database operations
- `role_name` (str): Name of the role
- `permission_name` (str): Name of the permission to assign

**Raises:**
- `RoleNotFoundError`: If the role does not exist
- `PermissionNotFoundError`: If the permission does not exist

#### `check_permission(roles, user_id, permission_name)`

Check if a user has a specific permission through any of their roles.

**Parameters:**
- `roles` (RoleAdapter): Role adapter for database operations
- `user_id` (UUID): User's unique identifier
- `permission_name` (str): Name of the permission to check

**Returns:**
- bool: True if user has the permission, False otherwise

**Example:**
```python
from fastauth.core.roles import check_permission

has_access = check_permission(
    roles=role_adapter,
    user_id=user.id,
    permission_name="delete:users"
)
```

#### `get_user_roles(roles, user_id)`

Get all roles assigned to a user.

**Parameters:**
- `roles` (RoleAdapter): Role adapter for database operations
- `user_id` (UUID): User's unique identifier

**Returns:**
- List of role objects

#### `get_user_permissions(roles, user_id)`

Get all permissions for a user across all their roles.

**Parameters:**
- `roles` (RoleAdapter): Role adapter for database operations
- `user_id` (UUID): User's unique identifier

**Returns:**
- List of permission objects

#### `get_role_permissions(roles, role_name)`

Get all permissions assigned to a role.

**Parameters:**
- `roles` (RoleAdapter): Role adapter for database operations
- `role_name` (str): Name of the role

**Returns:**
- List of permission objects

**Raises:**
- `RoleNotFoundError`: If the role does not exist

### `fastauth.core.sessions`

Session management functions.

#### `create_session(sessions, users, user_id, device, ip_address, user_agent)`

Create a new session for a user and update their last login timestamp.

**Parameters:**
- `sessions` (SessionAdapter): Session adapter for database operations
- `users` (UserAdapter): User adapter for database operations
- `user_id` (UUID): User's unique identifier
- `device` (str, optional): Device information
- `ip_address` (str, optional): IP address of the client
- `user_agent` (str, optional): User agent string

**Returns:**
- Session object

**Example:**
```python
from fastauth.core.sessions import create_session

session = create_session(
    sessions=session_adapter,
    users=user_adapter,
    user_id=user.id,
    device="iPhone 13",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0"
)
```

#### `get_user_sessions(sessions, user_id)`

Get all active sessions for a user.

**Parameters:**
- `sessions` (SessionAdapter): Session adapter for database operations
- `user_id` (UUID): User's unique identifier

**Returns:**
- List of session objects

**Example:**
```python
from fastauth.core.sessions import get_user_sessions

sessions_list = get_user_sessions(
    sessions=session_adapter,
    user_id=user.id
)
```

#### `delete_session(sessions, session_id, user_id)`

Delete a specific session with ownership verification.

**Parameters:**
- `sessions` (SessionAdapter): Session adapter for database operations
- `session_id` (UUID): Session's unique identifier
- `user_id` (UUID): User's unique identifier (for authorization)

**Raises:**
- `SessionNotFoundError`: If session doesn't exist or doesn't belong to user

**Example:**
```python
from fastauth.core.sessions import delete_session

delete_session(
    sessions=session_adapter,
    session_id=session_id,
    user_id=user.id
)
```

#### `delete_all_user_sessions(sessions, user_id, except_session_id)`

Delete all sessions for a user, optionally excluding the current session.

**Parameters:**
- `sessions` (SessionAdapter): Session adapter for database operations
- `user_id` (UUID): User's unique identifier
- `except_session_id` (UUID, optional): Session ID to keep (current session)

**Example:**
```python
from fastauth.core.sessions import delete_all_user_sessions

# Delete all sessions except current
delete_all_user_sessions(
    sessions=session_adapter,
    user_id=user.id,
    except_session_id=current_session_id
)

# Delete all sessions
delete_all_user_sessions(
    sessions=session_adapter,
    user_id=user.id
)
```

#### `update_session_activity(sessions, session_id)`

Update the last active timestamp for a session.

**Parameters:**
- `sessions` (SessionAdapter): Session adapter for database operations
- `session_id` (UUID): Session's unique identifier

#### `cleanup_inactive_sessions(sessions, inactive_days)`

Remove sessions that haven't been active for a specified number of days.

**Parameters:**
- `sessions` (SessionAdapter): Session adapter for database operations
- `inactive_days` (int): Number of days of inactivity before cleanup (default: 30)

**Example:**
```python
from fastauth.core.sessions import cleanup_inactive_sessions

# Remove sessions inactive for 30+ days
cleanup_inactive_sessions(
    sessions=session_adapter,
    inactive_days=30
)
```

### `fastauth.core.oauth`

OAuth 2.0 authentication functions.

#### `initiate_oauth_flow(oauth_states, provider, redirect_uri, state_data, use_pkce)`

Initiate an OAuth 2.0 authorization flow.

**Parameters:**
- `oauth_states` (OAuthStateAdapter): OAuth state adapter for database operations
- `provider` (OAuthProvider): OAuth provider instance (e.g., GoogleOAuthProvider)
- `redirect_uri` (str): Callback URL after OAuth authorization
- `state_data` (dict, optional): Additional data to store in state
- `use_pkce` (bool): Whether to use PKCE (Proof Key for Code Exchange) (default: False)

**Returns:**
- Dict with `authorization_url` (str) and `state` (str)

**Example:**
```python
from fastauth.core.oauth import initiate_oauth_flow
from fastauth.providers import GoogleOAuthProvider

provider = GoogleOAuthProvider(
    client_id="your-client-id",
    client_secret="your-client-secret"
)

result = initiate_oauth_flow(
    oauth_states=oauth_state_adapter,
    provider=provider,
    redirect_uri="http://localhost:8000/auth/oauth/google/callback",
    use_pkce=True
)
# result = {"authorization_url": "https://...", "state": "..."}
```

#### `complete_oauth_flow(oauth_states, oauth_accounts, users, provider, code, state, link_user_id)`

Complete an OAuth 2.0 authorization flow and create or link account.

**Parameters:**
- `oauth_states` (OAuthStateAdapter): OAuth state adapter
- `oauth_accounts` (OAuthAccountAdapter): OAuth account adapter
- `users` (UserAdapter): User adapter
- `provider` (OAuthProvider): OAuth provider instance
- `code` (str): Authorization code from OAuth provider
- `state` (str): State token to validate
- `link_user_id` (UUID, optional): User ID to link account to (if authenticated)

**Returns:**
- Tuple of (User object, bool indicating if new user was created)

**Raises:**
- `OAuthError`: If state is invalid, expired, or code exchange fails

**Example:**
```python
from fastauth.core.oauth import complete_oauth_flow

user, is_new = await complete_oauth_flow(
    oauth_states=oauth_state_adapter,
    oauth_accounts=oauth_account_adapter,
    users=user_adapter,
    provider=provider,
    code="authorization_code",
    state="state_token"
)
```

#### `get_linked_accounts(oauth_accounts, user_id)`

Get all OAuth accounts linked to a user.

**Parameters:**
- `oauth_accounts` (OAuthAccountAdapter): OAuth account adapter
- `user_id` (UUID): User's unique identifier

**Returns:**
- List of OAuthAccount objects

**Example:**
```python
from fastauth.core.oauth import get_linked_accounts

accounts = get_linked_accounts(
    oauth_accounts=oauth_account_adapter,
    user_id=user.id
)
```

#### `unlink_oauth_account(oauth_accounts, account_id, user_id)`

Unlink an OAuth account from a user.

**Parameters:**
- `oauth_accounts` (OAuthAccountAdapter): OAuth account adapter
- `account_id` (UUID): OAuth account's unique identifier
- `user_id` (UUID): User's unique identifier (for authorization)

**Raises:**
- `OAuthAccountNotFoundError`: If account doesn't exist or doesn't belong to user

**Example:**
```python
from fastauth.core.oauth import unlink_oauth_account

unlink_oauth_account(
    oauth_accounts=oauth_account_adapter,
    account_id=account_id,
    user_id=user.id
)
```

### `fastauth.core.account`

Account management functions for authenticated users.

#### `change_password(users, sessions, user_id, current_password, new_password, current_session_id)`

Change a user's password with verification.

**Parameters:**
- `users` (UserAdapter): User adapter for database operations
- `sessions` (SessionAdapter): Session adapter for database operations
- `user_id` (UUID): User's unique identifier
- `current_password` (str): Current password for verification
- `new_password` (str): New password to set
- `current_session_id` (UUID, optional): Session ID to preserve during logout

**Raises:**
- `UserNotFoundError`: If the user doesn't exist
- `InvalidPasswordError`: If the current password is incorrect

**Example:**
```python
from fastauth.core.account import change_password

change_password(
    users=user_adapter,
    sessions=session_adapter,
    user_id=user.id,
    current_password="old_password",
    new_password="new_password",
    current_session_id=current_session.id  # Optional: preserve current session
)
```

**Note:** Automatically invalidates all other sessions for security.

#### `delete_account(users, sessions, user_id, password, hard_delete)`

Delete a user account with soft or hard delete.

**Parameters:**
- `users` (UserAdapter): User adapter for database operations
- `sessions` (SessionAdapter): Session adapter for database operations
- `user_id` (UUID): User's unique identifier
- `password` (str): Password for verification
- `hard_delete` (bool): If True, permanently delete; if False, soft delete (default: False)

**Raises:**
- `UserNotFoundError`: If the user doesn't exist
- `InvalidPasswordError`: If the password is incorrect

**Example:**
```python
from fastauth.core.account import delete_account

# Soft delete (deactivate account, preserve data)
delete_account(
    users=user_adapter,
    sessions=session_adapter,
    user_id=user.id,
    password="user_password",
    hard_delete=False
)

# Hard delete (permanent removal)
delete_account(
    users=user_adapter,
    sessions=session_adapter,
    user_id=user.id,
    password="user_password",
    hard_delete=True
)
```

**Note:** Soft delete sets `deleted_at` timestamp and deactivates account. Hard delete permanently removes user from database. Both invalidate all sessions.

#### `request_email_change(users, email_changes, user_id, new_email, expires_in_minutes)`

Request an email change with verification token.

**Parameters:**
- `users` (UserAdapter): User adapter for database operations
- `email_changes` (EmailChangeAdapter): Email change adapter for database operations
- `user_id` (UUID): User's unique identifier
- `new_email` (str): New email address
- `expires_in_minutes` (int): Token expiration time in minutes (default: 60)

**Returns:**
- Verification token string if successful, None if user not found

**Raises:**
- `EmailAlreadyExistsError`: If the new email already exists

**Example:**
```python
from fastauth.core.account import request_email_change

token = request_email_change(
    users=user_adapter,
    email_changes=email_change_adapter,
    user_id=user.id,
    new_email="newemail@example.com",
    expires_in_minutes=60
)
```

#### `confirm_email_change(users, email_changes, token)`

Confirm an email change with verification token.

**Parameters:**
- `users` (UserAdapter): User adapter for database operations
- `email_changes` (EmailChangeAdapter): Email change adapter for database operations
- `token` (str): Verification token

**Raises:**
- `EmailChangeError`: If token is invalid or expired
- `EmailAlreadyExistsError`: If the new email is no longer available

**Example:**
```python
from fastauth.core.account import confirm_email_change

confirm_email_change(
    users=user_adapter,
    email_changes=email_change_adapter,
    token=verification_token
)
```

**Note:** Email change resets `is_verified` to False, requiring re-verification.

## Adapters

### Base Adapters

#### `UserAdapter`

Abstract base class for user database operations.

**Methods:**
- `get_by_email(email)` - Retrieve user by email
- `get_by_id(user_id)` - Retrieve user by ID
- `create_user(email, hashed_password)` - Create new user
- `mark_verified(user_id)` - Mark email as verified
- `set_password(user_id, new_password)` - Update password
- `update_last_login(user_id)` - Update last login timestamp
- `update_email(user_id, new_email)` - Update user's email address
- `soft_delete_user(user_id)` - Soft delete user (set deleted_at timestamp)
- `hard_delete_user(user_id)` - Permanently delete user from database

#### `RefreshTokenAdapter`

Abstract base class for refresh token operations.

**Methods:**
- `create(user_id, token_hash, expires_at)` - Create refresh token
- `get_active(token_hash)` - Get active token by hash
- `revoke(token_hash)` - Revoke a token

#### `PasswordResetAdapter`

Abstract base class for password reset operations.

**Methods:**
- `create(user_id, token_hash, expires_at)` - Create reset token
- `get_valid(token_hash)` - Get valid token by hash
- `mark_used(token_hash)` - Mark token as used

#### `EmailVerificationAdapter`

Abstract base class for email verification operations.

**Methods:**
- `create(user_id, token_hash, expires_at)` - Create verification token
- `get_valid(token_hash)` - Get valid token by hash
- `mark_used(token_hash)` - Mark token as used

#### `RoleAdapter`

Abstract base class for role and permission operations.

**Methods:**
- `create_role(name, description)` - Create a new role
- `get_role_by_name(name)` - Retrieve role by name
- `create_permission(name, description)` - Create a new permission
- `get_permission_by_name(name)` - Retrieve permission by name
- `assign_role_to_user(user_id, role_id)` - Assign role to user
- `remove_role_from_user(user_id, role_id)` - Remove role from user
- `get_user_roles(user_id)` - Get all roles for a user
- `assign_permission_to_role(role_id, permission_id)` - Assign permission to role
- `get_role_permissions(role_id)` - Get all permissions for a role
- `get_user_permissions(user_id)` - Get all permissions for a user (from all roles)

#### `SessionAdapter`

Abstract base class for session management operations.

**Methods:**
- `create_session(user_id, device, ip_address, user_agent)` - Create a new session
- `get_session_by_id(session_id)` - Retrieve session by ID
- `get_user_sessions(user_id)` - Get all sessions for a user
- `delete_session(session_id)` - Delete a specific session
- `delete_user_sessions(user_id, except_session_id)` - Delete all user sessions (optionally except one)
- `update_last_active(session_id)` - Update session's last active timestamp
- `cleanup_inactive_sessions(inactive_days)` - Remove inactive sessions

#### `EmailChangeAdapter`

Abstract base class for email change token operations.

**Methods:**
- `create(user_id, new_email, token_hash, expires_at)` - Create email change request with token
- `get_valid(token_hash)` - Get valid (not used) email change record by token hash
- `mark_used(token_hash)` - Mark email change token as used

#### `OAuthAccountAdapter`

Abstract base class for OAuth account operations.

**Methods:**
- `create(user_id, provider, provider_user_id, access_token, refresh_token, expires_at)` - Create OAuth account link
- `get_by_provider_user_id(provider, provider_user_id)` - Get OAuth account by provider and provider user ID
- `get_by_user_id(user_id)` - Get all OAuth accounts for a user
- `get_by_id(account_id)` - Get OAuth account by ID
- `delete(account_id)` - Delete OAuth account link

#### `OAuthStateAdapter`

Abstract base class for OAuth state token operations.

**Methods:**
- `create(state_hash, provider, redirect_uri, code_verifier, expires_at, state_data)` - Create OAuth state token
- `get_valid(state_hash)` - Get valid (not expired) state record by hash
- `delete(state_hash)` - Delete used state token

### SQLAlchemy Adapters

#### `SQLAlchemyUserAdapter`

SQLAlchemy implementation of UserAdapter.

**Example:**
```python
from sqlmodel import Session
from fastauth.adapters.sqlalchemy import SQLAlchemyUserAdapter

adapter = SQLAlchemyUserAdapter(session)
user = adapter.create_user(
    email="user@example.com",
    hashed_password="hashed..."
)
```

#### `SQLAlchemyRefreshTokenAdapter`

SQLAlchemy implementation of RefreshTokenAdapter.

#### `SQLAlchemyPasswordResetAdapter`

SQLAlchemy implementation of PasswordResetAdapter.

#### `SQLAlchemyEmailVerificationAdapter`

SQLAlchemy implementation of EmailVerificationAdapter.

#### `SQLAlchemyRoleAdapter`

SQLAlchemy implementation of RoleAdapter.

**Example:**
```python
from sqlmodel import Session
from fastauth.adapters.sqlalchemy import SQLAlchemyRoleAdapter

role_adapter = SQLAlchemyRoleAdapter(session)
role = role_adapter.create_role(name="admin", description="Administrator role")
```

#### `SQLAlchemySessionAdapter`

SQLAlchemy implementation of SessionAdapter.

**Example:**
```python
from sqlmodel import Session
from fastauth.adapters.sqlalchemy import SQLAlchemySessionAdapter

session_adapter = SQLAlchemySessionAdapter(session)
session = session_adapter.create_session(
    user_id=user.id,
    device="iPhone 13",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0"
)
```

#### `SQLAlchemyEmailChangeAdapter`

SQLAlchemy implementation of EmailChangeAdapter.

**Example:**
```python
from sqlmodel import Session
from fastauth.adapters.sqlalchemy import SQLAlchemyEmailChangeAdapter

email_change_adapter = SQLAlchemyEmailChangeAdapter(session)
email_change_adapter.create(
    user_id=user.id,
    new_email="newemail@example.com",
    token_hash="hashed_token",
    expires_at=datetime.now(UTC) + timedelta(hours=1)
)
```

#### `SQLAlchemyOAuthAccountAdapter`

SQLAlchemy implementation of OAuthAccountAdapter.

**Example:**
```python
from sqlmodel import Session
from fastauth.adapters.sqlalchemy import SQLAlchemyOAuthAccountAdapter

oauth_account_adapter = SQLAlchemyOAuthAccountAdapter(session)
oauth_account = oauth_account_adapter.create(
    user_id=user.id,
    provider="google",
    provider_user_id="google_user_123",
    access_token="encrypted_access_token",
    refresh_token="encrypted_refresh_token",
    expires_at=datetime.now(UTC) + timedelta(hours=1)
)
```

#### `SQLAlchemyOAuthStateAdapter`

SQLAlchemy implementation of OAuthStateAdapter.

**Example:**
```python
from sqlmodel import Session
from fastauth.adapters.sqlalchemy import SQLAlchemyOAuthStateAdapter

oauth_state_adapter = SQLAlchemyOAuthStateAdapter(session)
oauth_state_adapter.create(
    state_hash="hashed_state_token",
    provider="google",
    redirect_uri="http://localhost:8000/callback",
    code_verifier="pkce_code_verifier",
    expires_at=datetime.now(UTC) + timedelta(minutes=10),
    state_data={"link_user_id": str(user.id)}
)
```

## API Routes

### Authentication Endpoints

All routes are prefixed with `/auth`.

#### `POST /auth/register`

Register a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "is_verified": false,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00"
}
```

#### `POST /auth/login`

Login with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### `POST /auth/logout`

Logout and revoke refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

#### `POST /auth/refresh`

Get new access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Password Reset Endpoints

#### `POST /auth/password-reset/request`

Request password reset email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset email sent"
}
```

#### `POST /auth/password-reset/confirm`

Confirm password reset with token.

**Request Body:**
```json
{
  "token": "reset-token",
  "new_password": "newsecurepassword123"
}
```

**Response:** `200 OK`

### Email Verification Endpoints

#### `POST /auth/email-verification/request`

Request email verification.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`

#### `POST /auth/email-verification/confirm`

Confirm email with verification token.

**Request Body:**
```json
{
  "token": "verification-token"
}
```

**Response:** `200 OK`

#### `POST /auth/email-verification/resend`

Resend verification email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`

### Session Management Endpoints

All routes are prefixed with `/sessions` and require authentication.

#### `GET /sessions`

List all active sessions for the authenticated user.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "sessions": [
    {
      "id": "uuid",
      "device": "iPhone 13",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "last_active": "2024-01-01T12:00:00",
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

#### `DELETE /sessions/{session_id}`

Delete a specific session (logout from specific device).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Parameters:**
- `session_id` (UUID): ID of the session to delete

**Response:** `200 OK`
```json
{
  "message": "Session deleted successfully"
}
```

**Error Responses:**
- `404 Not Found` - Session not found or doesn't belong to user
- `401 Unauthorized` - Invalid or missing access token

#### `DELETE /sessions/all`

Delete all sessions for the authenticated user (logout from all devices).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "message": "All sessions deleted successfully"
}
```

**Note:** This endpoint deletes all sessions, which can be useful when a user suspects unauthorized access and wants to force logout from all devices.

### Account Management Endpoints

All routes are prefixed with `/account` and require authentication (except confirm-email-change).

#### `POST /account/change-password`

Change the authenticated user's password.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "current_password": "old_password123",
  "new_password": "new_password456"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Current password is incorrect
- `401 Unauthorized` - Invalid or missing access token
- `404 Not Found` - User not found

**Note:** Automatically invalidates all other sessions for security.

#### `DELETE /account/delete`

Delete the authenticated user's account.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "password": "user_password",
  "hard_delete": false
}
```

**Parameters:**
- `password` (string, required): User's password for verification
- `hard_delete` (boolean, optional): If true, permanently delete; if false, soft delete (default: false)

**Response:** `200 OK`
```json
{
  "message": "Account deactivated successfully"
}
```

OR (for hard delete):
```json
{
  "message": "Account permanently deleted successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Password is incorrect
- `401 Unauthorized` - Invalid or missing access token
- `404 Not Found` - User not found

**Note:** Soft delete sets `deleted_at` timestamp and deactivates account. Hard delete permanently removes user. Both invalidate all sessions.

#### `POST /account/request-email-change`

Request an email change with verification token.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "new_email": "newemail@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "Email change requested. Please verify the token to complete the change.",
  "token": "email-change-verification-token"
}
```

**Error Responses:**
- `400 Bad Request` - Email already exists
- `401 Unauthorized` - Invalid or missing access token
- `404 Not Found` - User not found

**Note:** Token expires in 60 minutes. In production, send this token via email instead of returning it in the response.

#### `POST /account/confirm-email-change`

Confirm an email change with verification token.

**Request Body:**
```json
{
  "token": "email-change-verification-token"
}
```

**Response:** `200 OK`
```json
{
  "message": "Email changed successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid, expired, or already used token, or email no longer available

**Note:** Email change resets `is_verified` to False, requiring re-verification of the new email.

### OAuth Authentication Endpoints

All routes are prefixed with `/oauth`.

#### `POST /oauth/{provider}/authorize`

Initiate OAuth 2.0 authorization flow.

**Path Parameters:**
- `provider` (str): OAuth provider name (e.g., "google")

**Request Body:**
```json
{
  "redirect_uri": "http://localhost:8000/auth/oauth/google/callback",
  "use_pkce": true
}
```

**Parameters:**
- `redirect_uri` (string, required): Callback URL after OAuth authorization
- `use_pkce` (boolean, optional): Use PKCE for enhanced security (default: false)

**Response:** `200 OK`
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "state_token_string"
}
```

**Note:** Redirect user to `authorization_url`. The `state` token is stored server-side for validation.

#### `POST /oauth/{provider}/callback`

Complete OAuth 2.0 authorization and create/link account.

**Path Parameters:**
- `provider` (str): OAuth provider name (e.g., "google")

**Request Body:**
```json
{
  "code": "authorization_code_from_provider",
  "state": "state_token_from_authorize"
}
```

**Parameters:**
- `code` (string, required): Authorization code from OAuth provider
- `state` (string, required): State token from authorize endpoint

**Response:** `200 OK`
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

**Error Responses:**
- `400 Bad Request` - Invalid state, expired state, or code exchange failed
- `401 Unauthorized` - OAuth provider authentication failed

**Note:** Creates new user if first-time OAuth login, or logs in existing user.

#### `GET /oauth/accounts`

List all OAuth accounts linked to the authenticated user.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
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

**Error Responses:**
- `401 Unauthorized` - Invalid or missing access token

#### `DELETE /oauth/accounts/{account_id}`

Unlink an OAuth account from the authenticated user.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Path Parameters:**
- `account_id` (UUID): ID of the OAuth account to unlink

**Response:** `200 OK`
```json
{
  "message": "OAuth account unlinked successfully"
}
```

**Error Responses:**
- `404 Not Found` - OAuth account not found or doesn't belong to user
- `401 Unauthorized` - Invalid or missing access token

**Note:** User must have a password set or at least one other OAuth account linked before unlinking.

## Security

### JWT Functions

#### `create_access_token(data, expires_delta)`

Create a JWT access token.

**Parameters:**
- `data` (dict): Payload data
- `expires_delta` (timedelta, optional): Expiration time

**Returns:**
- JWT token string

#### `decode_access_token(token)`

Decode and validate a JWT token.

**Parameters:**
- `token` (str): JWT token string

**Returns:**
- Decoded payload dict

**Raises:**
- `TokenError`: If token is invalid or expired

### Password Hashing

#### `hash_password(password)`

Hash a password using Argon2.

**Parameters:**
- `password` (str): Plain text password

**Returns:**
- Hashed password string

#### `verify_password(hashed_password, plain_password)`

Verify a password against its hash.

**Parameters:**
- `hashed_password` (str): Hashed password
- `plain_password` (str): Plain text password to verify

**Returns:**
- True if valid, False otherwise

### Rate Limiting

#### `RateLimiter`

Rate limiter for protecting endpoints.

**Methods:**
- `hit(key)` - Register an attempt
- `reset(key)` - Clear attempts

**Example:**
```python
from fastauth.security.rate_limit import RateLimiter

limiter = RateLimiter(max_attempts=5, window_seconds=300)
limiter.hit("user@example.com")  # Raises RateLimitExceeded if exceeded
```

## Models

### User

SQLAlchemy user model.

**Fields:**
- `id` (UUID): Unique identifier
- `email` (str): Email address (unique)
- `hashed_password` (str): Hashed password
- `is_active` (bool): Whether user is active
- `is_verified` (bool): Whether email is verified
- `is_superuser` (bool): Whether user has superuser privileges
- `last_login` (datetime, optional): Last login timestamp
- `deleted_at` (datetime, optional): Soft delete timestamp
- `created_at` (datetime): Creation timestamp

### RefreshToken

SQLAlchemy refresh token model.

**Fields:**
- `id` (UUID): Unique identifier
- `user_id` (UUID): User reference
- `token_hash` (str): Token hash (unique)
- `expires_at` (datetime): Expiration time
- `revoked` (bool): Whether token is revoked
- `created_at` (datetime): Creation timestamp

### PasswordResetToken

SQLAlchemy password reset token model.

**Fields:**
- `id` (UUID): Unique identifier
- `user_id` (UUID): User reference
- `token_hash` (str): Token hash (unique)
- `expires_at` (datetime): Expiration time
- `used` (bool): Whether token is used
- `created_at` (datetime): Creation timestamp

### EmailVerificationToken

SQLAlchemy email verification token model.

**Fields:**
- `id` (UUID): Unique identifier
- `user_id` (UUID): User reference
- `token_hash` (str): Token hash (unique)
- `expires_at` (datetime): Expiration time
- `used` (bool): Whether token is used
- `created_at` (datetime): Creation timestamp

### EmailChangeToken

SQLAlchemy email change token model.

**Fields:**
- `id` (UUID): Unique identifier
- `user_id` (UUID): User reference
- `new_email` (str): New email address to change to
- `token_hash` (str): Token hash (unique)
- `expires_at` (datetime): Expiration time
- `used` (bool): Whether token is used
- `created_at` (datetime): Creation timestamp

### Role

SQLAlchemy role model.

**Fields:**
- `id` (UUID): Unique identifier
- `name` (str): Role name (unique)
- `description` (str, optional): Role description
- `created_at` (datetime): Creation timestamp

### Permission

SQLAlchemy permission model.

**Fields:**
- `id` (UUID): Unique identifier
- `name` (str): Permission name (unique)
- `description` (str, optional): Permission description
- `created_at` (datetime): Creation timestamp

### UserRole

SQLAlchemy user-role junction model (many-to-many).

**Fields:**
- `user_id` (UUID): User reference (primary key)
- `role_id` (UUID): Role reference (primary key)
- `created_at` (datetime): Creation timestamp

### RolePermission

SQLAlchemy role-permission junction model (many-to-many).

**Fields:**
- `role_id` (UUID): Role reference (primary key)
- `permission_id` (UUID): Permission reference (primary key)
- `created_at` (datetime): Creation timestamp

### Session

SQLAlchemy session model.

**Fields:**
- `id` (UUID): Unique identifier
- `user_id` (UUID): User reference
- `device` (str, optional): Device information
- `ip_address` (str, optional): Client IP address
- `user_agent` (str, optional): User agent string
- `last_active` (datetime): Last activity timestamp
- `created_at` (datetime): Creation timestamp

**Example:**
```python
from fastauth.adapters.sqlalchemy.models import Session

# Sessions are automatically created on login/register
# and tracked across the user's devices
```

### OAuthAccount

SQLAlchemy OAuth account model for linking OAuth providers to users.

**Fields:**
- `id` (UUID): Unique identifier
- `user_id` (UUID): User reference
- `provider` (str): OAuth provider name (e.g., "google", "github")
- `provider_user_id` (str): User ID from OAuth provider
- `access_token` (str): Encrypted OAuth access token
- `refresh_token` (str, optional): Encrypted OAuth refresh token
- `expires_at` (datetime, optional): Access token expiration time
- `created_at` (datetime): Creation timestamp

**Example:**
```python
from fastauth.adapters.sqlalchemy.models import OAuthAccount

# OAuth accounts are automatically created/linked
# when users authenticate via OAuth providers
```

### OAuthState

SQLAlchemy OAuth state token model for CSRF protection.

**Fields:**
- `id` (UUID): Unique identifier
- `state_hash` (str): Hashed state token (unique)
- `provider` (str): OAuth provider name
- `redirect_uri` (str): Callback URL
- `code_verifier` (str, optional): PKCE code verifier
- `state_data` (JSON, optional): Additional state data
- `expires_at` (datetime): Expiration time
- `created_at` (datetime): Creation timestamp

**Example:**
```python
from fastauth.adapters.sqlalchemy.models import OAuthState

# OAuth states are automatically created during authorization
# and validated during callback to prevent CSRF attacks
```

## Settings

### `Settings`

Configuration class using Pydantic settings.

**Fields:**
- `jwt_secret_key` (str): Secret key for JWT tokens
- `jwt_algorithm` (str): JWT algorithm (default: HS256)
- `access_token_expire_minutes` (int): Access token expiration
- `refresh_token_expire_days` (int): Refresh token expiration
- `require_email_verification` (bool): Require email verification
- `email_provider` (str): Email provider type
- `oauth_google_client_id` (str, optional): Google OAuth client ID
- `oauth_google_client_secret` (str, optional): Google OAuth client secret
- `oauth_google_redirect_uri` (str, optional): Google OAuth redirect URI
- `oauth_state_expire_minutes` (int): OAuth state token expiration (default: 10)

**Example:**
```python
from fastauth import Settings

settings = Settings(
    jwt_secret_key="your-secret-key",
    access_token_expire_minutes=60,
    require_email_verification=True,
    oauth_google_client_id="your-google-client-id",
    oauth_google_client_secret="your-google-client-secret",
    oauth_google_redirect_uri="http://localhost:8000/auth/oauth/google/callback"
)
```

## Dependencies

### `get_current_user(credentials, session)`

FastAPI dependency to get the current authenticated user.

**Example:**
```python
from fastapi import Depends
from fastauth.api.dependencies import get_current_user

@app.get("/profile")
def get_profile(current_user = Depends(get_current_user)):
    return {"email": current_user.email}
```

### `get_role_adapter(session)`

FastAPI dependency to get the role adapter instance.

**Returns:**
- `SQLAlchemyRoleAdapter` instance

**Example:**
```python
from fastapi import Depends
from fastauth.api.dependencies import get_role_adapter

@app.get("/roles")
def list_roles(roles = Depends(get_role_adapter)):
    return roles.get_all_roles()
```

### `require_role(role_name)`

FastAPI dependency factory to require a specific role.

**Parameters:**
- `role_name` (str): Name of the required role

**Returns:**
- Dependency function that can be used with `Depends`

**Raises:**
- `HTTPException(403)`: If user doesn't have the required role

**Example:**
```python
from fastapi import Depends
from fastauth.api.dependencies import require_role

@app.get("/admin/dashboard", dependencies=[Depends(require_role("admin"))])
def admin_dashboard():
    return {"message": "Admin access granted"}
```

### `require_permission(permission_name)`

FastAPI dependency factory to require a specific permission.

**Parameters:**
- `permission_name` (str): Name of the required permission

**Returns:**
- Dependency function that can be used with `Depends`

**Raises:**
- `HTTPException(403)`: If user doesn't have the required permission

**Example:**
```python
from fastapi import Depends
from fastauth.api.dependencies import require_permission

@app.delete(
    "/users/{id}",
    dependencies=[Depends(require_permission("delete:users"))]
)
def delete_user(id: str):
    return {"message": "User deleted"}
```

## Exceptions

- `UserAlreadyExistsError` - User with email already exists
- `InvalidCredentialsError` - Invalid login credentials
- `EmailNotVerifiedError` - Email not verified
- `RefreshTokenError` - Invalid or expired refresh token
- `PasswordResetError` - Invalid or expired reset token
- `EmailVerificationError` - Invalid or expired verification token
- `RoleNotFoundError` - Role does not exist
- `PermissionNotFoundError` - Permission does not exist
- `RoleAlreadyExistsError` - Role with the name already exists
- `PermissionAlreadyExistsError` - Permission with the name already exists
- `SessionNotFoundError` - Session not found or doesn't belong to user
- `InvalidPasswordError` - Current password is incorrect (account management)
- `UserNotFoundError` - User not found (account management)
- `EmailChangeError` - Invalid or expired email change token
- `EmailAlreadyExistsError` - Email address already exists
- `OAuthError` - OAuth authentication error (invalid state, code exchange failed, etc.)
- `OAuthAccountNotFoundError` - OAuth account not found or doesn't belong to user
- `OAuthProviderNotFoundError` - OAuth provider not configured or not found
- `RateLimitExceeded` - Too many attempts
- `TokenError` - Invalid or expired JWT token
