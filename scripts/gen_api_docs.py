import mkdocs_gen_files

REFERENCE_PAGES = [
    (
        "reference/fastauth.md",
        "FastAuth",
        ["fastauth.app.FastAuth"],
    ),
    (
        "reference/config.md",
        "Configuration",
        ["fastauth.config.FastAuthConfig", "fastauth.config.JWTConfig"],
    ),
    (
        "reference/exceptions.md",
        "Exceptions",
        [
            "fastauth.exceptions.FastAuthError",
            "fastauth.exceptions.ConfigError",
            "fastauth.exceptions.MissingDependencyError",
            "fastauth.exceptions.AuthenticationError",
            "fastauth.exceptions.UserAlreadyExistsError",
            "fastauth.exceptions.UserNotFoundError",
            "fastauth.exceptions.InvalidTokenError",
            "fastauth.exceptions.ProviderError",
        ],
    ),
    (
        "reference/types.md",
        "Types",
        [
            "fastauth.types.UserData",
            "fastauth.types.SessionData",
            "fastauth.types.TokenData",
            "fastauth.types.OAuthAccountData",
            "fastauth.types.RoleData",
            "fastauth.types.TokenPair",
        ],
    ),
    (
        "reference/protocols.md",
        "Protocols",
        [
            "fastauth.core.protocols.UserAdapter",
            "fastauth.core.protocols.SessionAdapter",
            "fastauth.core.protocols.TokenAdapter",
            "fastauth.core.protocols.OAuthAccountAdapter",
            "fastauth.core.protocols.RoleAdapter",
            "fastauth.core.protocols.SessionBackend",
            "fastauth.core.protocols.EmailTransport",
            "fastauth.core.protocols.EventHooks",
        ],
    ),
    (
        "reference/deps.md",
        "Dependencies",
        [
            "fastauth.api.deps.require_auth",
            "fastauth.api.deps.require_role",
            "fastauth.api.deps.require_permission",
        ],
    ),
    (
        "reference/adapters.md",
        "Adapters",
        [
            "fastauth.adapters.sqlalchemy.SQLAlchemyAdapter",
            "fastauth.adapters.memory.MemoryUserAdapter",
            "fastauth.adapters.memory.MemoryTokenAdapter",
            "fastauth.adapters.memory.MemorySessionAdapter",
            "fastauth.adapters.memory.MemoryRoleAdapter",
            "fastauth.adapters.memory.MemoryOAuthAccountAdapter",
        ],
    ),
    (
        "reference/providers.md",
        "Providers",
        [
            "fastauth.providers.credentials.CredentialsProvider",
            "fastauth.providers.google.GoogleProvider",
            "fastauth.providers.github.GitHubProvider",
        ],
    ),
    (
        "reference/session-backends.md",
        "Session Backends",
        [
            "fastauth.session_backends.memory.MemorySessionBackend",
            "fastauth.session_backends.redis.RedisSessionBackend",
            "fastauth.session_backends.database.DatabaseSessionBackend",
        ],
    ),
    (
        "reference/email-transports.md",
        "Email Transports",
        [
            "fastauth.email_transports.console.ConsoleTransport",
            "fastauth.email_transports.smtp.SMTPTransport",
            "fastauth.email_transports.webhook.WebhookTransport",
        ],
    ),
]

DIVIDER = "\n---\n\n"

for page_path, title, identifiers in REFERENCE_PAGES:
    with mkdocs_gen_files.open(page_path, "w") as f:
        f.write(f"# {title}\n\n")
        for ident in identifiers:
            f.write(f"::: {ident}\n")
            f.write(DIVIDER)
