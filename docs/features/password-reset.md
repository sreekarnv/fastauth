# Password Reset

FastAuth provides a two-step password reset flow: request a reset link via email, then submit a new password with the token from the link.

## Prerequisites

Same as [Email Verification](email-verification.md) — you need a `token_adapter` and `email_transport` configured.

## Flow

```mermaid
sequenceDiagram
    participant U as User
    participant C as Client
    participant FA as FastAuth
    participant E as Email Transport
    participant DB as Token Store

    U->>C: POST /auth/password/forgot {email}
    C->>FA: POST /auth/password/forgot
    FA->>DB: get_user_by_email(email)
    alt user not found
        FA-->>C: 200 OK (no information leak)
    else user exists
        FA->>DB: create_token(type="password_reset", token=<uuid>)
        FA->>E: send reset email with link
        FA-->>C: 200 OK
    end

    U->>U: Opens email, clicks reset link
    U->>C: POST /auth/password/reset {token, new_password}
    C->>FA: POST /auth/password/reset
    FA->>DB: get_token(token, type="password_reset")
    alt token expired or not found
        FA-->>C: 400 Bad Request
    else valid
        FA->>FA: hash new_password
        FA->>DB: set_hashed_password(user_id, hashed)
        FA->>DB: delete_token(token)
        FA->>FA: hooks.on_password_reset(user)
        FA-->>C: 200 OK
    end
```

## Endpoints

| Method | Path | Body | Description |
|--------|------|------|-------------|
| `POST` | `/auth/password/forgot` | `{"email": "..."}` | Send a reset email |
| `POST` | `/auth/password/reset` | `{"token": "...", "password": "..."}` | Set a new password |

### Request a reset

```bash
curl -X POST http://localhost:8000/auth/password/forgot \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com"}'
```

FastAuth always returns `200 OK` for this endpoint regardless of whether the email exists, to prevent user enumeration.

### Submit a new password

```bash
curl -X POST http://localhost:8000/auth/password/reset \
  -H "Content-Type: application/json" \
  -d '{"token": "<token-from-email>", "password": "newS3cur3P@ss!"}'
```

## Hook

```python
class MyHooks(EventHooks):
    async def on_password_reset(self, user: UserData) -> None:
        await notify_user_of_password_change(user["email"])
```
