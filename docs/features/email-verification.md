# Email Verification

FastAuth can require users to verify their email address before they can sign in. The flow uses a one-time token stored via `token_adapter` and delivered by `email_transport`.

## Prerequisites

```python
from fastauth.email_transports.console import ConsoleTransport  # dev
# from fastauth.email_transports.smtp import SMTPTransport      # production

config = FastAuthConfig(
    ...,
    token_adapter=adapter.token,          # persists verification tokens
    email_transport=ConsoleTransport(),   # prints link to console in dev
    base_url="https://your-app.com",      # used in the verification link
)
```

## Flow

```mermaid
sequenceDiagram
    participant U as User
    participant C as Client
    participant FA as FastAuth
    participant E as Email Transport
    participant DB as Token Store

    U->>C: POST /auth/register {email, password}
    C->>FA: POST /auth/register
    FA->>DB: create user (email_verified=False)
    FA->>DB: create_token(type="verification", token=<cuid>)
    FA->>E: send verification email with link
    FA-->>C: 201 Created (user created, not yet verified)

    U->>U: Opens email, clicks verification link
    U->>C: GET /auth/verify-email?token=<cuid>
    C->>FA: GET /auth/verify-email?token=<cuid>
    FA->>DB: get_token(token, type="verification")
    alt token expired or not found
        FA-->>C: 400 Bad Request
    else valid
        FA->>DB: update_user(email_verified=True)
        FA->>DB: delete_token(token)
        FA->>FA: hooks.on_email_verify(user)
        FA-->>C: 200 OK {"message": "Email verified successfully"}
    end
```

## Endpoints

| Method | Path | Auth required | Description |
|--------|------|:---:|-------------|
| `POST` | `/auth/request-verify-email` | Yes | Re-send the verification email |
| `GET`  | `/auth/verify-email?token=<token>` | No | Verify the email and activate the account |
| `POST` | `/auth/verify-email` | No | Verify via body: `{"token": "..."}` |

### Resend verification email

The resend endpoint requires a valid access token (the user must be logged in):

```bash
curl -X POST http://localhost:8000/auth/request-verify-email \
  -H "Authorization: Bearer <access_token>"
```

### Verify email

The verification link in the email points to a `GET` endpoint. You can also submit the token via `POST`:

```bash
# Via GET (browser link)
curl http://localhost:8000/auth/verify-email?token=<token-from-email>

# Via POST (API client)
curl -X POST http://localhost:8000/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "<token-from-email>"}'
```

## Email transports

| Transport | Install | Use case |
|-----------|---------|---------|
| `ConsoleTransport` | built-in | Development — prints link to stdout |
| `SMTPTransport` | `email` extra | Production SMTP server |
| `WebhookTransport` | built-in | Custom HTTP endpoint / third-party service |

### SMTP

```python
from fastauth.email_transports.smtp import SMTPTransport

transport = SMTPTransport(
    hostname="smtp.sendgrid.net",
    port=587,
    username="apikey",
    password=os.environ["SENDGRID_API_KEY"],
    use_tls=True,
    sender="noreply@example.com",
)
```

## Hook

Override `on_email_verify` to run custom logic after verification:

```python
class MyHooks(EventHooks):
    async def on_email_verify(self, user: UserData) -> None:
        await grant_welcome_credits(user["id"])
```
