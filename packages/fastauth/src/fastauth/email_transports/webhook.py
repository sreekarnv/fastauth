from __future__ import annotations

from typing import Any

from fastauth._compat import require


class WebhookTransport:
    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        require("httpx", "oauth")
        self.url = url
        self.headers = headers or {}

    async def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> None:
        import httpx

        payload: dict[str, Any] = {
            "to": to,
            "subject": subject,
            "body_html": body_html,
        }
        if body_text:
            payload["body_text"] = body_text

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.url,
                json=payload,
                headers=self.headers,
            )
            resp.raise_for_status()
