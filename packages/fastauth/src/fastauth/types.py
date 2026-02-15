from __future__ import annotations

from datetime import datetime
from typing import List, Optional, TypedDict


class UserData(TypedDict):
    id: str
    email: str
    name: Optional[str]
    email_verified: bool
    is_active: bool
    image: Optional[str]


class SessionData(TypedDict):
    id: str
    user_id: str
    expires_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]


class TokenData(TypedDict):
    token: str
    user_id: str
    token_type: str
    expires_at: datetime


class OAuthAccountData(TypedDict):
    provider: str
    provider_account_id: str
    user_id: str
    access_token: Optional[str]
    refresh_token: Optional[str]
    expires_at: Optional[datetime]


class RoleData(TypedDict):
    name: str
    permissions: List[str]


class TokenPair(TypedDict):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
