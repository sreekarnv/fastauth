from fastauth.email.base import EmailClient
from fastauth.email.console import ConsoleEmailClient
from fastauth.email.smtp import SMTPEmailClient
from fastauth.settings import settings


def get_email_client() -> EmailClient:
    if settings.email_backend == "console":
        return ConsoleEmailClient()

    if settings.email_backend == "smtp":
        return SMTPEmailClient()

    raise RuntimeError(f"Unsupported email_backend: {settings.email_backend}")
