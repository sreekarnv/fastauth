from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from fastauth._compat import require
from fastauth.exceptions import ProviderError
from fastauth.types import UserData


class GitHubProvider:
    """GitHub OAuth 2.0 provider."""

    id = "github"
    name = "GitHub"
    auth_type = "oauth"

    AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scopes: list[str] | None = None,
    ) -> None:
        require("httpx", "oauth")
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes or ["user:email"]

    async def get_authorization_url(
        self, state: str, redirect_uri: str, **kwargs: Any
    ) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
        }
        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def exchange_code(
        self, code: str, redirect_uri: str, **kwargs: Any
    ) -> dict[str, Any]:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            if resp.status_code != 200:
                raise ProviderError(f"GitHub token exchange failed: {resp.text}")
            data = resp.json()
            if "error" in data:
                raise ProviderError(f"GitHub token exchange failed: {data['error']}")
            return data

    async def get_user_info(self, access_token: str) -> UserData:
        import httpx

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(self.USER_URL, headers=headers)
            if resp.status_code != 200:
                raise ProviderError(f"GitHub user info failed: {resp.text}")
            data = resp.json()

            email = data.get("email")
            if not email:
                email = await self._fetch_primary_email(client, access_token)

            return {
                "id": str(data["id"]),
                "email": email,
                "name": data.get("name") or data.get("login"),
                "image": data.get("avatar_url"),
                "email_verified": True,
                "is_active": True,
            }

    async def _fetch_primary_email(self, client: Any, access_token: str) -> str:
        resp = await client.get(
            self.EMAILS_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        if resp.status_code != 200:
            raise ProviderError("Failed to fetch GitHub emails")
        emails = resp.json()
        for entry in emails:
            if entry.get("primary") and entry.get("verified"):
                return entry["email"]
        for entry in emails:
            if entry.get("primary"):
                return entry["email"]
        if emails:
            return emails[0]["email"]
        raise ProviderError("No email found on GitHub account")

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any] | None:
        return None
