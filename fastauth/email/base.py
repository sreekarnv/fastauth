from abc import ABC, abstractmethod


class EmailClient(ABC):
    @abstractmethod
    def send_verification_email(self, *, to: str, token: str) -> None:
        ...

    @abstractmethod
    def send_password_reset_email(self, *, to: str, token: str) -> None:
        ...
