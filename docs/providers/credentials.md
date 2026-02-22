# Credentials Provider

The built-in email/password provider. No extra dependencies required (password hashing uses `argon2-cffi` from the `argon2` extra).

## Setup

```python
from fastauth.providers.credentials import CredentialsProvider

config = FastAuthConfig(
    providers=[CredentialsProvider()],
    ...
)
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Sign in with email + password |
| `POST` | `/auth/logout` | Sign out (clears cookies or invalidates session) |
| `POST` | `/auth/refresh` | Refresh token pair |
| `GET`  | `/auth/me` | Return current user |

### Register

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "s3cur3P@ss!"}'
```

The optional `name` field is also accepted:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "s3cur3P@ss!", "name": "Alice"}'
```

Response (`201 Created`):

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Sign in

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "s3cur3P@ss!"}'
```

## Email verification

When an `email_transport` and `token_adapter` are configured, FastAuth automatically sends a verification email on registration.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/request-verify-email` | Re-send the verification email (requires auth) |
| `GET`  | `/auth/verify-email?token=<token>` | Mark email as verified |
| `POST` | `/auth/verify-email` | Mark email as verified (body: `{"token": "..."}`) |

See [Email Verification](../features/email-verification.md) for the full flow.

## Password reset

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/forgot-password` | Send a reset email |
| `POST` | `/auth/reset-password` | Set a new password using the reset token |

See [Password Reset](../features/password-reset.md).

## Account management

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/account/change-password` | Change password (requires auth) |
| `POST` | `/auth/account/change-email` | Request email change (requires auth) |
| `GET`  | `/auth/account/confirm-email-change?token=<token>` | Confirm the new email |
| `DELETE` | `/auth/account` | Delete account (requires auth) |

See [Account Management](../features/account.md) for details.

## Password hashing

FastAuth uses **Argon2id** by default (`argon2-cffi`). If Argon2 is not installed it falls back to **bcrypt**.

!!! tip "Install Argon2"
    ```bash
    pip install "sreekarnv-fastauth[argon2]"
    ```
