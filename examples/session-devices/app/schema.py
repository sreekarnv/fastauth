from datetime import datetime

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SessionResponse(BaseModel):
    id: str
    device: str | None
    ip_address: str | None
    user_agent: str | None
    last_active: datetime
    created_at: datetime
    is_current: bool = False
