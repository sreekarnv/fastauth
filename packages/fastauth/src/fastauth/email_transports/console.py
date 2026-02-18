from __future__ import annotations


class ConsoleTransport:
    async def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> None:
        print(f"\n{'=' * 60}")
        print(f"To: {to}")
        print(f"Subject: {subject}")
        print(f"{'=' * 60}")
        if body_text:
            print(body_text)
        else:
            print(body_html)
        print(f"{'=' * 60}\n")
