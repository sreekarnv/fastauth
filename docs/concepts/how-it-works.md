# How it Works

FastAuth is a thin orchestration layer that connects **providers**, **adapters**, and **transports** together under a single FastAPI router.

## Architecture overview

```mermaid
graph TD
    APP["FastAPI Application"]

    subgraph ROUTER["FastAuth Router  /auth/*"]
        ENDPOINTS["/register · /login · /logout · /refresh · /me
/oauth/{provider}/authorize · /oauth/{provider}/callback
/request-verify-email · /verify-email
/forgot-password · /reset-password
/account/* · /roles/* · /sessions/*"]
    end

    subgraph CORE["Core Logic"]
        CORELOGIC["tokens · sessions · rbac · oauth · emails · jwks"]
    end

    subgraph PROVIDERS["Providers"]
        direction LR
        P1["Credentials"]
        P2["Google"]
        P3["GitHub"]
    end

    subgraph ADAPTERS["Adapters"]
        direction LR
        A1["SQLAlchemy"]
        A2["Memory"]
        A3["Custom"]
    end

    subgraph TRANSPORTS["Transports"]
        direction LR
        T1["SMTP"]
        T2["Console"]
        T3["Webhook"]
    end

    APP --> ROUTER
    ROUTER --> CORE
    CORE --> PROVIDERS & ADAPTERS & TRANSPORTS
```

### Layers

| Layer | Responsibility |
|-------|---------------|
| **API (router)** | HTTP endpoints — validates request bodies, calls core logic, returns responses |
| **Core** | Business logic — token creation, session management, RBAC checks |
| **Providers** | Authenticate users — verify a password or exchange an OAuth code |
| **Adapters** | Persist data — read/write users, tokens, sessions, roles in a database |
| **Transports** | Deliver emails — SMTP, webhook, or console (for dev) |

---

## Sign-in flow (credentials)

The sequence below shows what happens when a user posts `{ email, password }` to `/auth/login`:

```mermaid
sequenceDiagram
    participant C as Client
    participant FA as FastAuth Router
    participant P as CredentialsProvider
    participant A as UserAdapter
    participant T as Core/Tokens

    C->>FA: POST /auth/login {email, password}
    FA->>P: authenticate({email, password})
    P->>A: get_user_by_email(email)
    A-->>P: user record (or None)
    P->>P: verify_password(plain, hashed)
    P-->>FA: user (or None)

    alt authentication failed
        FA-->>C: 401 Unauthorized
    else success
        FA->>FA: hooks.on_signin(user, "credentials")
        FA->>T: create_access_token(user)
        FA->>T: create_refresh_token(user)
        T-->>FA: {access_token, refresh_token}
        FA-->>C: 200 OK {access_token, refresh_token, token_type, expires_in}
    end
```

---

## Request authentication flow

When a protected route uses `Depends(require_auth)`:

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Protected Route
    participant D as require_auth dep
    participant T as Core/Tokens
    participant A as UserAdapter

    C->>R: GET /dashboard (Authorization: Bearer <token>)
    R->>D: Depends(require_auth)
    D->>D: extract token from header or cookie
    D->>T: decode_token(token_str)
    T-->>D: claims {sub, type, exp}

    alt token invalid or expired
        D-->>C: 401 Unauthorized
    else
        D->>A: get_user_by_id(claims["sub"])
        A-->>D: user record
        D-->>R: user
        R-->>C: 200 OK {response data}
    end
```

---

## Key design decisions

**Protocol-based (duck typing)** — Every adapter and transport is defined as a Python `Protocol`. You never inherit from a FastAuth base class; you just implement the right methods and pass your object in.

**Async-first** — All adapters, providers, and hooks are `async`. FastAuth works natively with SQLAlchemy's async engine, aioredis, aiosmtplib, and httpx.

**Opt-in features** — Email flows, RBAC, OAuth, JWKS — nothing is enabled unless you configure it. A minimal install has zero runtime dependencies beyond `cuid2` and `pydantic`.
