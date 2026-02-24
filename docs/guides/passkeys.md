# Guide: Passkeys (WebAuthn)

This guide walks through the `examples/passkeys` application — a FastAPI app with both email/password and passkey authentication, plus a minimal browser UI.

## What we're building

- Email + password register and sign-in
- Passkey registration (Touch ID, Face ID, Windows Hello, security key)
- Passwordless sign-in with a registered passkey
- List and delete passkeys via a browser UI
- SQLite database via SQLAlchemy

## Full server source

```python title="examples/passkeys/main.py"
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.api.deps import require_auth
from fastauth.providers.credentials import CredentialsProvider
from fastauth.providers.passkey import PasskeyProvider
from fastauth.session_backends.memory import MemorySessionBackend
from fastauth.types import UserData

adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

auth = FastAuth(
    FastAuthConfig(
        secret="dev-secret-change-me",
        providers=[
            CredentialsProvider(),
            PasskeyProvider(
                rp_id="localhost",
                rp_name="FastAuth Passkeys Demo",
                origin="http://localhost:8000",
            ),
        ],
        adapter=adapter.user,
        token_adapter=adapter.token,
        passkey_adapter=adapter.passkey,
        passkey_state_store=MemorySessionBackend(),
        debug=True,
    )
)

templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    yield


app = FastAPI(title="FastAuth Passkeys Example", lifespan=lifespan)
auth.mount(app)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.jinja2", {"request": request})


@app.get("/profile")
async def profile(user: UserData = Depends(require_auth)):
    return {"id": user["id"], "email": user["email"]}
```

## Step-by-step walkthrough

### 1. Install the webauthn extra

```bash
pip install "sreekarnv-fastauth[standard,webauthn]"
```

`webauthn` pulls in the [py-webauthn](https://github.com/duo-labs/py_webauthn) library which handles the FIDO2 ceremony on the server.

### 2. Configure `PasskeyProvider`

```python
PasskeyProvider(
    rp_id="localhost",              # domain only, no scheme or port
    rp_name="FastAuth Passkeys Demo",
    origin="http://localhost:8000", # full origin — must match the browser page
)
```

`rp_id` is the Relying Party ID. The browser checks that it matches the domain of the page performing the ceremony. For production, use your actual domain: `"example.com"`.

!!! warning "Use `localhost`, not `127.0.0.1`"
    WebAuthn requires a registrable domain as `rp_id`. IP addresses (including `127.0.0.1`) are not valid. Always open the app at `http://localhost:8000` during local development.

Multiple origins (e.g. dev + prod):

```python
PasskeyProvider(
    rp_id="example.com",
    rp_name="My App",
    origin=["https://example.com", "http://localhost:5173"],
)
```

### 3. Add the passkey adapter and state store

```python
passkey_adapter=adapter.passkey,
passkey_state_store=MemorySessionBackend(),
```

`passkey_adapter` persists credentials in the `fastauth_passkeys` table. `passkey_state_store` stores challenges while the WebAuthn ceremony is in progress (TTL: 5 minutes). Use `RedisSessionBackend` in production.

### 4. Mount routes and serve the UI

```python
auth.mount(app)
app.mount("/static", StaticFiles(directory="static"), name="static")
```

`auth.mount(app)` registers all `/auth/*` routes including the six passkey endpoints. The static mount serves `passkeys.js`.

### 5. Browser-side with `@simplewebauthn/browser`

The client talks to the passkey endpoints using [`@simplewebauthn/browser`](https://simplewebauthn.dev) loaded directly from CDN — no build step needed.

**Registration:**

```js
import { startRegistration } from "https://esm.sh/@simplewebauthn/browser@13";

const options = await fetch("/auth/passkeys/register/begin", {
  headers: { Authorization: `Bearer ${token}` },
}).then(r => r.json());

const credential = await startRegistration({ optionsJSON: options });

await fetch("/auth/passkeys/register/complete", {
  method: "POST",
  headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  body: JSON.stringify({ credential, name: "Touch ID" }),
});
```

**Authentication:**

```js
import { startAuthentication } from "https://esm.sh/@simplewebauthn/browser@13";

const options = await fetch("/auth/passkeys/authenticate/begin", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email }),
}).then(r => r.json());

const credential = await startAuthentication({ optionsJSON: options });

const tokens = await fetch("/auth/passkeys/authenticate/complete", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ credential }),
}).then(r => r.json());
```

`startRegistration` and `startAuthentication` wrap `navigator.credentials.create` and `navigator.credentials.get` respectively and handle all base64url encoding for you.

### Why Windows Hello / Touch ID appears in the sign-in dialog

For the platform authenticator picker (Windows Hello, Touch ID, Face ID) to appear, the credential must be stored as a **resident/discoverable key**. FastAuth requests `residentKey: preferred` during registration, so most authenticators store it automatically.

When calling `authenticate/begin` without an email, `allowCredentials` is empty and the browser shows all available passkeys for the `rp_id`. When an email is provided, the server sends a targeted `allowCredentials` list — more reliable on older devices that do not support discoverable credentials.

## Run it

```bash
pip install "sreekarnv-fastauth[standard,webauthn]"
uvicorn main:app --reload
```

Open [http://localhost:8000](http://localhost:8000), create an account, then add a passkey from the dashboard.

## Production checklist

- Replace `secret` with `fastauth generate-secret` output
- Replace `MemorySessionBackend` with `RedisSessionBackend`
- Set `rp_id` to your domain (`"example.com"`) and `origin` to the full origin (`"https://example.com"`)
- Use a PostgreSQL connection URL in `SQLAlchemyAdapter`
- Set `debug=False` (or omit it) so `cookie_secure=True` is enforced
