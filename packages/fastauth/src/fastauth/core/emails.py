from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jinja2 import Environment

    from fastauth.core.protocols import EmailTransport
    from fastauth.types import UserData


def _create_env(template_dir: str | Path | None = None) -> Environment:
    from jinja2 import Environment, FileSystemLoader, PackageLoader

    if template_dir is not None:
        loader = FileSystemLoader(str(template_dir))
    else:
        loader = PackageLoader("fastauth", "templates")
    return Environment(loader=loader, autoescape=True)


class EmailDispatcher:
    def __init__(
        self,
        transport: EmailTransport | None,
        base_url: str,
        template_dir: str | Path | None = None,
    ) -> None:
        self.transport = transport
        self.base_url = base_url.rstrip("/")
        self._env: Environment | None = None
        if self.transport:
            from fastauth._compat import require

            require("jinja2", "email")
            self._env = _create_env(template_dir)

    async def send_verification_email(
        self,
        user: UserData,
        token: str,
        expires_in_minutes: int = 1440,
    ) -> None:
        if not self.transport or self._env is None:
            return
        url = f"{self.base_url}/auth/verify-email?token={token}"
        template = self._env.get_template("verification.jinja2")
        html = template.render(
            name=user.get("name") or user["email"],
            url=url,
            expires_in_minutes=expires_in_minutes,
        )
        await self.transport.send(
            to=user["email"],
            subject="Verify your email address",
            body_html=html,
        )

    async def send_password_reset_email(
        self,
        user: UserData,
        token: str,
        expires_in_minutes: int = 30,
    ) -> None:
        if not self.transport or self._env is None:
            return
        url = f"{self.base_url}/auth/reset-password?token={token}"
        template = self._env.get_template("password_reset.jinja2")
        html = template.render(
            name=user.get("name") or user["email"],
            url=url,
            expires_in_minutes=expires_in_minutes,
        )
        await self.transport.send(
            to=user["email"],
            subject="Reset your password",
            body_html=html,
        )

    async def send_welcome_email(self, user: UserData) -> None:
        if not self.transport or self._env is None:
            return
        template = self._env.get_template("welcome.jinja2")
        html = template.render(
            name=user.get("name") or user["email"],
        )
        await self.transport.send(
            to=user["email"],
            subject="Welcome!",
            body_html=html,
        )

    async def send_email_change_email(
        self,
        user: UserData,
        new_email: str,
        token: str,
        expires_in_minutes: int = 30,
    ) -> None:
        if not self.transport or self._env is None:
            return
        url = f"{self.base_url}/auth/account/confirm-email-change?token={token}"
        template = self._env.get_template("email_change.jinja2")
        html = template.render(
            name=user.get("name") or user["email"],
            new_email=new_email,
            url=url,
            expires_in_minutes=expires_in_minutes,
        )
        await self.transport.send(
            to=new_email,
            subject="Confirm your new email address",
            body_html=html,
        )
