from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.api.deps import require_auth, require_permission, require_role
from fastauth.email_transports.console import ConsoleTransport
from fastauth.providers.credentials import CredentialsProvider
from fastauth.types import UserData

adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

config = FastAuthConfig(
    secret="super-secret-change-me-in-production",
    providers=[CredentialsProvider()],
    adapter=adapter.user,
    token_adapter=adapter.token,
    email_transport=ConsoleTransport(),
    base_url="http://localhost:8000",
    # Switch to cookie delivery — tokens set as HttpOnly cookies on login/register.
    # cookie_secure defaults to False when debug=True, True otherwise.
    # token_delivery="cookie",
    # debug=True,
)

auth = FastAuth(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    yield


app = FastAPI(title="FastAuth Basic Example", lifespan=lifespan)
auth.mount(app)


# ---------------------------------------------------------------------------
# Your own protected routes — use require_auth / require_role / require_permission
# ---------------------------------------------------------------------------


@app.get("/dashboard")
async def dashboard(user: UserData = Depends(require_auth)):
    return {"message": f"Hello, {user['email']}", "user": user}


@app.get("/admin")
async def admin_area(user: UserData = Depends(require_role("admin"))):
    return {"message": "Welcome, admin", "user_id": user["id"]}


@app.get("/reports")
async def reports(user: UserData = Depends(require_permission("reports:read"))):
    return {"message": "Here are your reports", "user_id": user["id"]}
