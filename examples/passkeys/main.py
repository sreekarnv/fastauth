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
