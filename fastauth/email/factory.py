from typing import Dict, Type

from fastauth.email.base import EmailClient
from fastauth.email.console import ConsoleEmailClient
from fastauth.email.smtp import SMTPEmailClient
from fastauth.settings import settings

_email_client_registry: Dict[str, Type[EmailClient]] = {
    "console": ConsoleEmailClient,
    "smtp": SMTPEmailClient,
}


def register_email_client(backend_name: str, client_class: Type[EmailClient]) -> None:
    """Register a custom email client backend.

    This allows users to add their own email client implementations
    without modifying the FastAuth library code.

    Args:
        backend_name: Name to identify this backend (used in settings.email_backend)
        client_class: EmailClient subclass to use for this backend

    Example:
        >>> from fastauth.email.factory import register_email_client
        >>> from fastauth.email.base import EmailClient
        >>>
        >>> class MyCustomEmailClient(EmailClient):
        ...     def send_verification_email(self, *, to: str, token: str) -> None:
        ...         # Custom implementation
        ...         pass
        >>>
        >>> register_email_client("custom", MyCustomEmailClient)
    """
    _email_client_registry[backend_name] = client_class


def get_email_client() -> EmailClient:
    """Get email client based on settings.email_backend.

    Returns:
        An instance of the configured email client.

    Raises:
        RuntimeError: If the configured backend is not registered.
    """
    client_class = _email_client_registry.get(settings.email_backend)

    if not client_class:
        available = ", ".join(_email_client_registry.keys())
        raise RuntimeError(
            f"Unsupported email_backend: '{settings.email_backend}'. "
            f"Available backends: {available}"
        )

    return client_class()
