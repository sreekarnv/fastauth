from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from fastauth._compat import require
from fastauth.exceptions import ProviderError
from fastauth.types import UserData


class GoogleProvider:
    """Google OAuth 2.0 / OIDC provider."""

    id = "google"
    name = "Google"
    auth_type = "oauth"

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scopes: list[str] | None = None,
    ) -> None:
        require("httpx", "oauth")
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes or ["openid", "email", "profile"]

    async def get_authorization_url(
        self, state: str, redirect_uri: str, **kwargs: Any
    ) -> str:
        params: dict[str, str] = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        if "code_challenge" in kwargs:
            params["code_challenge"] = kwargs["code_challenge"]
            params["code_challenge_method"] = kwargs.get(
                "code_challenge_method", "S256"
            )
        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    async def exchange_code(
        self, code: str, redirect_uri: str, **kwargs: Any
    ) -> dict[str, Any]:
        import httpx

        data: dict[str, Any] = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        if kwargs.get("code_verifier"):
            data["code_verifier"] = kwargs["code_verifier"]

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.TOKEN_URL, data=data)
            if resp.status_code != 200:
                raise ProviderError(f"Google token exchange failed: {resp.text}")
            return resp.json()

    async def get_user_info(self, access_token: str) -> UserData:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code != 200:
                raise ProviderError(f"Google user info failed: {resp.text}")
            data = resp.json()
            return {
                "id": data["sub"],
                "email": data["email"],
                "name": data.get("name"),
                "image": data.get("picture"),
                "email_verified": data.get("email_verified", False),
                "is_active": True,
            }

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any] | None:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            if resp.status_code != 200:
                return None
            return resp.json()
