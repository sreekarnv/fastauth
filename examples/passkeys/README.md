# FastAuth — Passkeys Example

Credentials + passkey (WebAuthn) authentication with SQLite. Includes a minimal browser UI that lets you register, sign in, add passkeys, and remove them — no build step required.

## What it demonstrates

- `PasskeyProvider` — WebAuthn registration and authentication
- `CredentialsProvider` — email/password as a fallback
- `SQLAlchemyAdapter` — SQLite via aiosqlite (swap for PostgreSQL in production)
- `MemorySessionBackend` — challenge state (swap for `RedisSessionBackend` in production)
- `@simplewebauthn/browser` — browser-side WebAuthn API via CDN
- Jinja2 template + vanilla JS frontend

## Setup

```bash
pip install "sreekarnv-fastauth[standard,webauthn]"
uvicorn main:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

> **Important:** WebAuthn requires a hostname — you must open the app at `http://localhost:8000`, not `http://127.0.0.1:8000`. IP addresses are not valid WebAuthn Relying Party IDs.

## Flow

1. **Create an account** with email + password (or sign in if you already have one)
2. **Add a passkey** — your browser will prompt you for Touch ID / Face ID / Windows Hello / security key
3. **Sign out**, then **sign in with passkey** — no password needed

## Endpoints

FastAuth mounts all auth routes under `/auth`. The passkey-specific ones are:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/passkeys/register/begin` | yes | Generate registration options |
| `POST` | `/auth/passkeys/register/complete` | yes | Verify and store the new credential |
| `GET` | `/auth/passkeys` | yes | List your registered passkeys |
| `DELETE` | `/auth/passkeys/{id}` | yes | Remove a passkey |
| `POST` | `/auth/passkeys/authenticate/begin` | no | Generate authentication options |
| `POST` | `/auth/passkeys/authenticate/complete` | no | Verify credential, return tokens |

## Production notes

- Replace `secret` with the output of `fastauth generate-secret`
- Replace `MemorySessionBackend` with `RedisSessionBackend`
- Set `rp_id` to your actual domain (e.g. `"example.com"`) and `origin` to the full origin (e.g. `"https://example.com"`)
- Use a PostgreSQL URL instead of SQLite
