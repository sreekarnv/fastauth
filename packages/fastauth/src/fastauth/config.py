from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from fastauth.exceptions import ConfigError

if TYPE_CHECKING:
    from fastauth.core.protocols import (
        EmailTransport,
        EventHooks,
        OAuthAccountAdapter,
        PasskeyAdapter,
        SessionBackend,
        TokenAdapter,
        UserAdapter,
    )


@dataclass
class PasswordConfig:
    """Password strength and security settings.

    Attributes:
        min_length: Minimum password length (default: 8).
        require_uppercase: Require at least one uppercase letter.
        require_lowercase: Require at least one lowercase letter.
        require_digit: Require at least one digit.
        require_special: Require at least one special character.
        max_length: Maximum password length (default: 128).
    """

    min_length: int = 8
    require_uppercase: bool = False
    require_lowercase: bool = False
    require_digit: bool = False
    require_special: bool = False
    max_length: int = 128


@dataclass
class SecurityConfig:
    """Security settings including account lockout.

    Attributes:
        max_login_attempts: Maximum failed login attempts before lockout (default: 5).
        lockout_duration: Duration of lockout in seconds (default: 300 = 5 minutes).
    """

    max_login_attempts: int = 5
    lockout_duration: int = 300  # 5 minutes


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
    remember_me_ttl: int = 7_776_000  # 90 days
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
        session_strategy: Currently informational only. FastAuth always issues
            JWT token pairs on register/login/refresh. The ``"database"`` value
            is reserved for a future server-side session model and is not
            currently wired through to auth routes; do not rely on it yet.
        route_prefix: URL prefix for all FastAuth endpoints (default: ``"/auth"``).
        session_backend: Reserved for the future ``"database"`` session strategy.
            Auth routes do not use it today; assign a ``session_adapter`` on the
            :class:`~fastauth.app.FastAuth` instance to manage user sessions
            through ``/auth/sessions`` endpoints.
        email_transport: Transport used to deliver verification and password-reset
            emails. Omit to disable email flows entirely.
        email_template_dir: Directory containing custom Jinja2 email templates.
            Any file placed here overrides the corresponding built-in template;
            templates not present in this directory fall back to the built-in ones.
            See the :ref:`custom email templates <custom-email-templates>` guide for
            the expected filenames and available template variables.
        hooks: An :class:`~fastauth.core.protocols.EventHooks` subclass for
            lifecycle callbacks (``on_signup``, ``modify_jwt``, etc.).
        oauth_adapter: Adapter for persisting linked OAuth accounts.
        oauth_state_store: Session backend used to store OAuth CSRF state.
        oauth_redirect_url: Frontend URL FastAuth 302s to after a successful
            OAuth callback (e.g. ``"https://app.example.com/auth/callback"``).
            Tokens are set as ``HttpOnly`` cookies on the response — never
            appended to the URL. This is **not** the OAuth provider callback URL;
            the provider callback is the ``/auth/oauth/{provider}/callback``
            route and is identified by the ``redirect_uri`` query parameter on
            the authorize endpoint.
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
        password: Password strength and validation settings.
        security: Security settings including account lockout.
    """

    secret: str
    providers: list[Any]
    adapter: UserAdapter
    jwt: JWTConfig = field(default_factory=JWTConfig)
    password: PasswordConfig = field(default_factory=PasswordConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    session_strategy: Literal["jwt", "database"] = "jwt"
    route_prefix: str = "/auth"
    session_backend: SessionBackend | None = None
    email_transport: EmailTransport | None = None
    email_template_dir: str | Path | None = None
    hooks: EventHooks | None = None
    oauth_adapter: OAuthAccountAdapter | None = None
    oauth_state_store: SessionBackend | None = None
    oauth_redirect_url: str | None = None
    store_oauth_provider_tokens: bool = False
    token_adapter: TokenAdapter | None = None
    passkey_adapter: PasskeyAdapter | None = None
    passkey_state_store: SessionBackend | None = None
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

        if self.jwt.algorithm.startswith("HS"):
            secret_bytes = len(self.secret.encode("utf-8"))
            if secret_bytes < 32:
                raise ConfigError(
                    "JWT HS-family algorithms require a secret of at least "
                    f"32 bytes. Got {secret_bytes} bytes. Use a strong "
                    "random secret."
                )

        if not self.providers:
            raise ConfigError("At least one provider must be configured")

        if self.session_strategy == "database" and self.session_backend is None:
            raise ConfigError(
                "session_backend is required when session_strategy is 'database'"
            )

        if self.jwt.algorithm.startswith("RS"):
            if not self.jwt.jwks_enabled:
                raise ConfigError(
                    f"{self.jwt.algorithm} requires jwks_enabled=True and "
                    "auth.initialize_jwks() before signing tokens"
                )
