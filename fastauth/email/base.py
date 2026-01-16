"""
Email client base interface.

Defines the abstract interface for email clients. All email implementations
(SMTP, console, third-party services) must inherit from EmailClient.
"""

from abc import ABC, abstractmethod


class EmailClient(ABC):
    """
    Abstract base class for email clients.

    Implementations must provide methods for sending verification
    and password reset emails.
    """

    @abstractmethod
    def send_verification_email(self, *, to: str, token: str) -> None: ...

    @abstractmethod
    def send_password_reset_email(self, *, to: str, token: str) -> None: ...
