from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastauth import FastAuth, FastAuthConfig, JWTConfig
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.providers.credentials import CredentialsProvider

_PRIVATE_KEY = Path("private_key.pem").read_text()
_PUBLIC_KEY = Path("public_key.pem").read_text()

adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

config = FastAuthConfig(
    secret="unused-for-rs256-but-required",
    providers=[CredentialsProvider()],
    adapter=adapter.user,
    token_adapter=adapter.token,
    jwt=JWTConfig(
        algorithm="RS256",
        private_key=_PRIVATE_KEY,
        public_key=_PUBLIC_KEY,
        jwks_enabled=True,
        access_token_ttl=900,
    ),
    base_url="http://localhost:8000",
)

auth = FastAuth(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    await auth.initialize_jwks()
    yield


app = FastAPI(title="FastAuth — Auth Service", lifespan=lifespan)
auth.mount(app)
