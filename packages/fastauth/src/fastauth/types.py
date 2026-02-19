"""TypedDict shapes for FastAuth domain objects passed between adapters and core."""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict


class UserData(TypedDict):
    id: str
    email: str
    name: str | None
    email_verified: bool
    is_active: bool
    image: str | None


class SessionData(TypedDict):
    id: str
    user_id: str
    expires_at: datetime
    ip_address: str | None
    user_agent: str | None


class TokenData(TypedDict):
    token: str
    user_id: str
    token_type: str
    expires_at: datetime


class OAuthAccountData(TypedDict):
    provider: str
    provider_account_id: str
    user_id: str
    access_token: str | None
    refresh_token: str | None
    expires_at: datetime | None


class RoleData(TypedDict):
    name: str
    permissions: list[str]


class TokenPair(TypedDict):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
