def test_public_symbols_importable():
    from fastauth import (  # noqa: F401
        AccountLockedError,
        AuthenticationError,
        AuthProvider,
        ConfigError,
        EmailTransport,
        EventHooks,
        FastAuth,
        FastAuthConfig,
        FastAuthError,
        InvalidTokenError,
        JWTConfig,
        LoginAttemptData,
        MissingDependencyError,
        OAuthAccountAdapter,
        OAuthAccountData,
        PasskeyAdapter,
        PasskeyData,
        PasswordConfig,
        ProviderError,
        RoleAdapter,
        RoleData,
        SecurityConfig,
        SessionAdapter,
        SessionBackend,
        SessionData,
        TokenAdapter,
        TokenData,
        TokenPair,
        UserAdapter,
        UserAlreadyExistsError,
        UserData,
        UserNotFoundError,
    )


def test_fastauth_module_all_contains_core_symbols():
    import fastauth

    expected = {
        "AuthProvider",
        "EmailTransport",
        "FastAuth",
        "FastAuthConfig",
        "JWTConfig",
        "PasswordConfig",
        "OAuthAccountAdapter",
        "OAuthAccountData",
        "PasskeyAdapter",
        "PasskeyData",
        "RoleAdapter",
        "RoleData",
        "SecurityConfig",
        "SessionAdapter",
        "SessionBackend",
        "SessionData",
        "TokenAdapter",
        "TokenData",
        "TokenPair",
        "UserAdapter",
        "UserData",
        "EventHooks",
    }
    assert expected.issubset(set(fastauth.__all__))


def test_providers_remain_importable_from_submodule():
    """Providers and adapters stay in their submodules so they can pull in
    their own optional dependencies. Importing the provider directly must
    succeed when its extra is installed.
    """
    from fastauth.providers.credentials import CredentialsProvider
    from fastauth.providers.github import GitHubProvider
    from fastauth.providers.google import GoogleProvider
    from fastauth.providers.magic_links import MagicLinksProvider

    assert CredentialsProvider.id == "credentials"
    assert GoogleProvider.id == "google"
    assert GitHubProvider.id == "github"
    assert MagicLinksProvider.id == "magic_links"
