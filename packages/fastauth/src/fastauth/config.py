from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from fastauth.exceptions import ConfigError

if TYPE_CHECKING:
    from fastauth.core.protocols import (
        EmailTransport,
        EventHooks,
        OAuthAccountAdapter,
        SessionBackend,
        UserAdapter,
    )


@dataclass
class JWTConfig:
    algorithm: str = "HS256"
    access_token_ttl: int = 900
    refresh_token_ttl: int = 2_592_000  # 30 days
    issuer: str | None = None
    audience: list[str] | None = None
    jwks_enabled: bool = False
    key_rotation_interval: int | None = None
    private_key: str | None = None
    public_key: str | None = None


@dataclass
class FastAuthConfig:
    secret: str
    providers: list[Any]
    adapter: UserAdapter
    jwt: JWTConfig = field(default_factory=JWTConfig)
    session_strategy: Literal["jwt", "database"] = "jwt"
    route_prefix: str = "/auth"
    session_backend: SessionBackend | None = None
    email_transport: EmailTransport | None = None
    hooks: EventHooks | None = None
    oauth_adapter: OAuthAccountAdapter | None = None
    oauth_state_store: SessionBackend | None = None
    oauth_redirect_url: str | None = None
    cors_origins: list[str] | None = None
    roles: list[dict[str, Any]] | None = None
    default_role: str | None = None
    debug: bool = False

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.secret:
            raise ConfigError("'secret' must be set and non-empty")

        if not self.providers:
            raise ConfigError("At least one provider must be configured")

        if self.session_strategy == "database" and self.session_backend is None:
            raise ConfigError(
                "session_backend is required when session_strategy is 'database'"
            )

        if self.jwt.algorithm.startswith("RS"):
            has_keys = self.jwt.private_key and self.jwt.public_key
            if not has_keys and not self.jwt.jwks_enabled:
                raise ConfigError(
                    f"For {self.jwt.algorithm}, provide private_key/public_key "
                    "or enable jwks_enabled"
                )
