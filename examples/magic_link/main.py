import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.email_transports.smtp import SMTPTransport
from fastauth.providers.magic_links import MagicLinksProvider

adapter = SQLAlchemyAdapter(
    engine_url=os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./magic_links.db")
)

email_transport = SMTPTransport(
    host=os.environ["SMTP_HOST"],
    port=int(os.environ.get("SMTP_PORT", "587")),
    username=os.environ["SMTP_USER"],
    password=os.environ["SMTP_PASS"],
    from_email=os.environ["SMTP_FROM"],
    use_tls=False,
)

config = FastAuthConfig(
    secret=os.environ["SECRET"],
    providers=[MagicLinksProvider()],
    adapter=adapter.user,
    token_adapter=adapter.token,
    email_transport=email_transport,
)

auth = FastAuth(config=config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    yield


app = FastAPI(lifespan=lifespan)
auth.mount(app)
