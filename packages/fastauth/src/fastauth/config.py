from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

if TYPE_CHECKING:
    from fastauth.core.protocols import (
        EmailTransport,
        EventHooks,
        SessionBackend,
        UserAdapter,
    )


@dataclass
class JWTConfig:
    algorithm: str = "HS256"
    access_token_ttl: int = 900
    refresh_token_ttl: int = 2_592_000  # 30 days
    issuer: Optional[None] = None
    audience: Optional[List[str]] = None
    jwks_enabled: bool = False
    key_rotation_interval: Optional[int] = None
    private_key: Optional[str] = None
    public_key: Optional[str] = None


@dataclass
class FastAuthConfig:
    secret: str
    providers: List[str]
    adapter: UserAdapter
    jwt: JWTConfig = field(default_factory=JWTConfig)
    session_stragety: Literal["jwt", "database"] = "jwt"
    route_prefix: str = "/auth"
    session_backend: Optional[SessionBackend] = None
    email_transport: Optional[EmailTransport] = None
    hooks: Optional[EventHooks] = None
    cors_origin: Optional[List[str]] = None
    roles: Optional[List[Dict[str, Any]]] = None
    default_role: Optional[str] = None
    debug: bool = False


# TODO: Need to add a validate method
# @staticmethod
# def validate():
