def test_public_symbols_importable():
    from fastauth import (  # noqa: F401
        AccountLockedError,
        AuthenticationError,
        ConfigError,
        EventHooks,
        FastAuth,
        FastAuthConfig,
        FastAuthError,
        InvalidTokenError,
        JWTConfig,
        MissingDependencyError,
        PasswordConfig,
        ProviderError,
        SecurityConfig,
        UserAlreadyExistsError,
        UserNotFoundError,
    )


def test_fastauth_module_all_contains_core_symbols():
    import fastauth

    expected = {
        "FastAuth",
        "FastAuthConfig",
        "JWTConfig",
        "PasswordConfig",
        "SecurityConfig",
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
