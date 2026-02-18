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
| `POST` | `/auth/signup` | Register a new user |
| `POST` | `/auth/signin` | Sign in with email + password |
| `POST` | `/auth/signout` | Sign out (invalidate session/token) |
| `POST` | `/auth/refresh` | Refresh token pair |
| `GET`  | `/auth/me` | Return current user |

### Sign up

```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "s3cur3P@ss!"}'
```

Response:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Sign in

```bash
curl -X POST http://localhost:8000/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "s3cur3P@ss!"}'
```

## Email verification

When an `email_transport` and `token_adapter` are configured, FastAuth automatically sends a verification email on sign-up. The user must click the link before they can sign in.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/email/request-verify` | Re-send the verification email |
| `GET`  | `/auth/email/verify?token=<token>` | Mark email as verified |

See [Email Verification](../features/email-verification.md) for the full flow.

## Password reset

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/password/forgot` | Send a reset email |
| `POST` | `/auth/password/reset` | Set a new password using the reset token |

See [Password Reset](../features/password-reset.md).

## Password hashing

FastAuth uses **Argon2id** by default (`argon2-cffi`). If Argon2 is not installed it falls back to **bcrypt**.

!!! tip "Install Argon2"
    ```bash
    pip install "sreekarnv-fastauth[argon2]"
    ```
