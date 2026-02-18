from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastauth._compat import require


class SMTPTransport:
    """SMTP email transport using aiosmtplib."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True,
    ) -> None:
        require("aiosmtplib", "email")
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls

    async def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> None:
        import aiosmtplib

        msg = MIMEMultipart("alternative")
        msg["From"] = self.from_email
        msg["To"] = to
        msg["Subject"] = subject

        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        await aiosmtplib.send(
            msg,
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            use_tls=self.use_tls,
        )
