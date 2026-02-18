import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastauth import FastAuth, FastAuthConfig, JWTConfig
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.email_transports.smtp import SMTPTransport
from fastauth.providers.credentials import CredentialsProvider
from fastauth.providers.github import GitHubProvider
from fastauth.providers.google import GoogleProvider
from fastauth.session_backends.redis import RedisSessionBackend

_PRIVATE_KEY = Path("private_key.pem").read_text()
_PUBLIC_KEY = Path("public_key.pem").read_text()

adapter = SQLAlchemyAdapter(
    engine_url=os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./auth.db")
)

redis_backend = RedisSessionBackend(
    url=os.environ.get("REDIS_URL", "redis://localhost:6379")
)

email_transport = SMTPTransport(
    host=os.environ["SMTP_HOST"],
    port=int(os.environ.get("SMTP_PORT", "587")),
    username=os.environ["SMTP_USER"],
    password=os.environ["SMTP_PASS"],
    from_email=os.environ["SMTP_FROM"],
)

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
    session_strategy="database",
    session_backend=redis_backend,
    oauth_adapter=adapter.oauth,
    oauth_state_store=RedisSessionBackend(
        url=os.environ.get("REDIS_URL", "redis://localhost:6379"),
        prefix="fastauth:oauth-state:",
    ),
    oauth_redirect_url=os.environ.get(
        "OAUTH_REDIRECT_URL", "http://localhost:8000/auth/oauth/callback"
    ),
    email_transport=email_transport,
    jwt=JWTConfig(
        algorithm="RS256",
        private_key=_PRIVATE_KEY,
        public_key=_PUBLIC_KEY,
        jwks_enabled=True,
        access_token_ttl=900,
        refresh_token_ttl=2_592_000,
    ),
    roles=[
        {"name": "admin", "permissions": ["users:read", "users:write", "users:delete"]},
        {"name": "user", "permissions": ["profile:read", "profile:write"]},
    ],
    default_role="user",
    base_url=os.environ.get("BASE_URL", "http://localhost:8000"),
    cors_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
    debug=os.environ.get("DEBUG", "false").lower() == "true",
)

auth = FastAuth(config)
auth.role_adapter = adapter.role


@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    await auth.initialize_jwks()
    yield


app = FastAPI(title="FastAuth Full Example", lifespan=lifespan)
auth.mount(app)
