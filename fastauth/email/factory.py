from fastauth.settings import settings
from fastauth.email.console import ConsoleEmailClient
from fastauth.email.base import EmailClient


def get_email_client() -> EmailClient:
    if settings.email_backend == "console":
        return ConsoleEmailClient()

    raise RuntimeError("Unsupported email backend")
