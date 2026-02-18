# FastAuth — JWT Microservice Example

Two services that communicate using RS256 JWTs — no shared secret needed between them.

- **`auth_service.py`** — FastAuth with RS256 signing and a public JWKS endpoint
- **`resource_service.py`** — A separate FastAPI service that verifies tokens by fetching the auth service's JWKS

## What it demonstrates

- RS256 asymmetric JWT signing
- JWKS endpoint (`GET /.well-known/jwks.json`)
- Token verification in a downstream service using `joserfc` + JWKS

## Setup

```bash
pip install sreekarnv-fastauth[standard,jwt]

python generate_keys.py
```

**Terminal 1 — auth service**
```bash
uvicorn auth_service:app --port 8000 --reload
```

**Terminal 2 — resource service**
```bash
pip install fastapi uvicorn httpx joserfc
uvicorn resource_service:app --port 8001 --reload
```

## Flow

1. Register: `POST http://localhost:8000/auth/register`
2. Login: `POST http://localhost:8000/auth/login` → copy the `access_token`
3. Call the resource service:
   ```bash
   curl http://localhost:8001/me -H "Authorization: Bearer <access_token>"
   ```

## Endpoints

**Auth service** (`localhost:8000`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register |
| `POST` | `/auth/login` | Login, receive RS256 JWT |
| `GET` | `/.well-known/jwks.json` | Public key set |

**Resource service** (`localhost:8001`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/me` | Protected — returns decoded JWT claims |
| `GET` | `/health` | Health check |
