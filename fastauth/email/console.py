from fastauth.email.base import EmailClient


class ConsoleEmailClient(EmailClient):
    def send_verification_email(self, *, to: str, token: str) -> None:
        print(f"[EMAIL] Verify {to}: token={token}")

    def send_password_reset_email(self, *, to: str, token: str) -> None:
        print(f"[EMAIL] Reset password for {to}: token={token}")
