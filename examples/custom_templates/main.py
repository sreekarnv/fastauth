import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastauth import FastAuth, FastAuthConfig
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter
from fastauth.email_transports.smtp import SMTPTransport
from fastauth.providers.credentials import CredentialsProvider
from fastauth.providers.magic_links import MagicLinksProvider

TEMPLATES_DIR = Path(__file__).parent / "templates"

adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./custom_templates.db")


email_transport = SMTPTransport(
    host=os.environ["SMTP_HOST"],
    port=int(os.environ.get("SMTP_PORT", "587")),
    username=os.environ["SMTP_USER"],
    password=os.environ["SMTP_PASS"],
    from_email=os.environ["SMTP_FROM"],
    use_tls=False,
)

config = FastAuthConfig(
    secret="dev-secret-change-me",
    providers=[
        CredentialsProvider(),
        MagicLinksProvider(),
    ],
    adapter=adapter.user,
    token_adapter=adapter.token,
    email_transport=email_transport,
    email_template_dir=TEMPLATES_DIR,
    base_url="http://localhost:8000",
)


auth = FastAuth(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    yield


app = FastAPI(title="FastAuth Custom Templates Example", lifespan=lifespan)
auth.mount(app)
