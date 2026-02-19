import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.email_transports.console import ConsoleTransport
from fastauth.providers.credentials import CredentialsProvider
from fastauth.providers.github import GitHubProvider
from fastauth.providers.google import GoogleProvider
from fastauth.session_backends.memory import MemorySessionBackend

adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

config = FastAuthConfig(
    secret=os.environ["SECRET"],
    providers=[
        CredentialsProvider(),
        GoogleProvider(
            client_id=os.environ["GOOGLE_CLIENT_ID"],
            client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        ),
        GitHubProvider(
            client_id=os.environ["GITHUB_CLIENT_ID"],
            client_secret=os.environ["GITHUB_CLIENT_SECRET"],
        ),
    ],
    adapter=adapter.user,
    token_adapter=adapter.token,
    oauth_adapter=adapter.oauth,
    oauth_state_store=MemorySessionBackend(),
    oauth_redirect_url="http://localhost:8000/auth/oauth/callback",
    email_transport=ConsoleTransport(),
    base_url="http://localhost:8000",
)

auth = FastAuth(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    yield


app = FastAPI(title="FastAuth OAuth Example", lifespan=lifespan)
auth.mount(app)
