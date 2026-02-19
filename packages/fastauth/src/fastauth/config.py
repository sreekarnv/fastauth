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
        TokenAdapter,
        UserAdapter,
    )


@dataclass
class JWTConfig:
    """JWT signing and validation settings.

    All TTL values are in **seconds**.

    Attributes:
        algorithm: Signing algorithm — ``"HS256"`` for HMAC shared-secret,
            ``"RS256"`` / ``"RS512"`` for RSA key-pair signing.
        access_token_ttl: Lifetime of access tokens (default: 900 = 15 minutes).
        refresh_token_ttl: Lifetime of refresh tokens (default: 2 592 000 = 30 days).
        issuer: Optional ``iss`` claim embedded in every token.
        audience: Optional ``aud`` claim; validated on every decode.
        jwks_enabled: When ``True``, expose a ``/.well-known/jwks.json`` endpoint
            and rotate RSA keys automatically.
        key_rotation_interval: Seconds between automatic RSA key rotations when
            ``jwks_enabled=True``. ``None`` disables auto-rotation.
        private_key: PEM-encoded RSA private key (required for RS256/RS512).
        public_key: PEM-encoded RSA public key (required for RS256/RS512).
    """

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
    """Top-level configuration for a :class:`~fastauth.app.FastAuth` instance.

    The three **required** fields are *secret*, *providers*, and *adapter*.
    All other fields have sensible defaults.

    Attributes:
        secret: HMAC shared secret used to sign tokens when ``jwt.algorithm``
            is ``"HS256"``. Generate a secure value with ``fastauth generate-secret``.
        providers: One or more provider instances — e.g. ``CredentialsProvider()``,
            ``GoogleProvider(...)``, ``GitHubProvider(...)``.
        adapter: A :class:`~fastauth.core.protocols.UserAdapter` implementation
            that reads and writes user records in your database.
        jwt: JWT signing and TTL configuration; defaults to HS256 with 15-minute
            access tokens.
        session_strategy: ``"jwt"`` for stateless JWT sessions (default) or
            ``"database"`` for server-side sessions stored in *session_backend*.
        route_prefix: URL prefix for all FastAuth endpoints (default: ``"/auth"``).
        session_backend: Required when *session_strategy* is ``"database"``.
            Provide a :class:`~fastauth.core.protocols.SessionBackend` such as
            :class:`~fastauth.session_backends.redis.RedisSessionBackend`.
        email_transport: Transport used to deliver verification and password-reset
            emails. Omit to disable email flows entirely.
        hooks: An :class:`~fastauth.core.protocols.EventHooks` subclass for
            lifecycle callbacks (``on_signup``, ``modify_jwt``, etc.).
        oauth_adapter: Adapter for persisting linked OAuth accounts.
        oauth_state_store: Session backend used to store OAuth CSRF state.
        oauth_redirect_url: Full callback URL registered with OAuth providers
            (e.g. ``"https://example.com/auth/oauth/callback"``).
        token_adapter: Adapter for persisting one-time verification/reset tokens.
        base_url: Public base URL of your application; used when building
            email verification / password-reset links.
        cors_origins: Allowed CORS origins. ``None`` disables CORS middleware.
        roles: Seed role definitions applied on startup.
        default_role: Role automatically assigned to every new user.
        debug: Relaxes cookie security (``Secure=False``) and enables verbose
            error output. **Never enable in production.**
        token_delivery: ``"json"`` returns tokens in the response body;
            ``"cookie"`` sets them as HttpOnly cookies.
        cookie_name_access: Name of the access-token cookie (default:
            ``"access_token"``).
        cookie_name_refresh: Name of the refresh-token cookie (default:
            ``"refresh_token"``).
        cookie_secure: Explicit ``Secure`` flag override; defaults to
            ``not debug``.
        cookie_httponly: ``HttpOnly`` cookie flag (default: ``True``).
        cookie_samesite: ``SameSite`` policy — ``"lax"``, ``"strict"``, or
            ``"none"`` (default: ``"lax"``).
        cookie_domain: Optional domain scope for cookies.
    """

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
    token_adapter: TokenAdapter | None = None
    base_url: str = "http://localhost:8000"
    cors_origins: list[str] | None = None
    roles: list[dict[str, Any]] | None = None
    default_role: str | None = None
    debug: bool = False
    token_delivery: Literal["json", "cookie"] = "json"
    cookie_name_access: str = "access_token"
    cookie_name_refresh: str = "refresh_token"
    cookie_secure: bool | None = None
    cookie_httponly: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: str | None = None

    @property
    def effective_cookie_secure(self) -> bool:
        if self.cookie_secure is not None:
            return self.cookie_secure
        return not self.debug

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
