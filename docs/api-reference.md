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

**Example:**
```python
from fastauth import Settings

settings = Settings(
    jwt_secret_key="your-secret-key",
    access_token_expire_minutes=60,
    require_email_verification=True
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
- `RateLimitExceeded` - Too many attempts
- `TokenError` - Invalid or expired JWT token
