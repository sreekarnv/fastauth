# Authentication Guide

Complete guide to user authentication with FastAuth.

## Setup

Include the auth router in your app:

```python
from fastauth.api.auth import router as auth_router

app.include_router(auth_router)
```

This adds all authentication endpoints:
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user
- `POST /auth/password-reset/request` - Request password reset
- `POST /auth/password-reset/confirm` - Confirm password reset
- `POST /auth/email-verification/resend` - Resend verification email
- `POST /auth/email-verification/confirm` - Confirm email

## Registration

### Basic Registration

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

Response:

```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### In Python

```python
from fastauth.core.users import create_user
from fastauth.adapters.sqlalchemy import SQLAlchemyUserAdapter

user = create_user(
    users=SQLAlchemyUserAdapter(session),
    email="user@example.com",
    password="securepassword123",
)
```

## Login

### Basic Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

Response:

```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### In Python

```python
from fastauth.core.users import authenticate_user
from fastauth.adapters.sqlalchemy import SQLAlchemyUserAdapter
from fastauth.security.jwt import create_access_token

user = authenticate_user(
    users=SQLAlchemyUserAdapter(session),
    email="user@example.com",
    password="securepassword123",
)

access_token = create_access_token(subject=str(user.id))
```

## Token Refresh

Access tokens expire after 30 minutes (configurable). Use the refresh token to get a new access token:

```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

Response:

```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

## Logout

Revoke the refresh token:

```bash
curl -X POST "http://localhost:8000/auth/logout" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

## Password Reset

### Step 1: Request Reset

```bash
curl -X POST "http://localhost:8000/auth/password-reset/request" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

This sends a password reset email with a token.

### Step 2: Confirm Reset

```bash
curl -X POST "http://localhost:8000/auth/password-reset/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "RESET_TOKEN_FROM_EMAIL",
    "new_password": "newpassword456"
  }'
```

## Email Verification

Enable email verification in `.env`:

```bash
REQUIRE_EMAIL_VERIFICATION=true
EMAIL_PROVIDER=console  # or smtp
```

### Resend Verification Email

```bash
curl -X POST "http://localhost:8000/auth/email-verification/resend" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

### Confirm Email

```bash
curl -X POST "http://localhost:8000/auth/email-verification/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "VERIFICATION_TOKEN_FROM_EMAIL"
  }'
```

## Error Handling

```python
from fastauth.core.users import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    EmailNotVerifiedError,
)

try:
    user = create_user(users=user_adapter, email=email, password=password)
except UserAlreadyExistsError:
    # Handle duplicate email
    pass
```

Common errors:
- `UserAlreadyExistsError` - Email already registered
- `InvalidCredentialsError` - Wrong email or password
- `EmailNotVerifiedError` - Email not verified (when verification required)
- `TokenExpiredError` - Verification/reset token expired

## Next Steps

- **[Protecting Routes](protecting-routes.md)** - Secure your endpoints
- **[Sessions](sessions.md)** - Track user sessions
- **[Email Configuration](email.md)** - Configure email provider
