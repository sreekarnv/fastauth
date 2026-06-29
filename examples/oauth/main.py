import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.email_transports.console import ConsoleTransport
from fastauth.providers.credentials import CredentialsProvider
from fastauth.providers.github import GitHubProvider
from fastauth.providers.google import GoogleProvider
from fastauth.session_backends.memory import MemorySessionBackend

load_dotenv()

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
    # The redirect URL passed to `/auth/oauth/{provider}/authorize?redirect_uri=...`
    # is the FastAPI route registered with the OAuth provider. After a successful
    # callback, FastAuth 302s to `oauth_redirect_url` (your frontend) with tokens
    # set as HttpOnly cookies — they are never placed in the URL.
    oauth_redirect_url=os.environ.get(
        "OAUTH_REDIRECT_URL", "http://localhost:3000/auth/callback"
    ),
    email_transport=ConsoleTransport(),
    base_url="http://localhost:8000",
    # Enable cookie delivery so the local frontend can read the HttpOnly cookies
    # on http://localhost (or set `debug=True` to relax `cookie_secure` for dev).
    token_delivery="cookie",
    debug=True,
)

auth = FastAuth(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    yield


app = FastAPI(title="FastAuth OAuth Example", lifespan=lifespan)
auth.mount(app)
