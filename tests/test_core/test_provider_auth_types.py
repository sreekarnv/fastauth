from fastauth.providers.credentials import CredentialsProvider
from fastauth.providers.github import GitHubProvider
from fastauth.providers.google import GoogleProvider
from fastauth.providers.magic_links import MagicLinksProvider
from fastauth.providers.passkey import PasskeyProvider


def test_credentials_provider_exposes_auth_type():
    assert CredentialsProvider.auth_type == "credentials"


def test_google_provider_exposes_auth_type():
    assert GoogleProvider.auth_type == "oauth"


def test_github_provider_exposes_auth_type():
    assert GitHubProvider.auth_type == "oauth"


def test_magic_links_provider_exposes_auth_type():
    assert MagicLinksProvider.auth_type == "magic_links"


def test_passkey_provider_exposes_auth_type():
    assert PasskeyProvider.auth_type == "passkey"
