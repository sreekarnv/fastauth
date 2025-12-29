from fastauth.security.oauth import (
    build_authorization_url,
    generate_code_challenge,
    generate_code_verifier,
    generate_state_token,
    hash_oauth_token,
    hash_state_token,
)


def test_generate_state_token():
    """State token should be a URL-safe random string."""
    token = generate_state_token()
    assert isinstance(token, str)
    assert len(token) > 0
    assert "/" not in token or "+" not in token or "=" not in token


def test_hash_state_token():
    """State token should be hashed with SHA-256."""
    token = "test_state_token"
    hash1 = hash_state_token(token)
    hash2 = hash_state_token(token)

    assert hash1 == hash2
    assert all(c in "0123456789abcdef" for c in hash1)
    assert len(hash1) == 64


def test_hash_oauth_token():
    """OAuth tokens should be hashed with SHA-256."""
    token = "test_access_token"
    hash1 = hash_oauth_token(token)
    hash2 = hash_oauth_token(token)

    assert hash1 == hash2
    assert all(c in "0123456789abcdef" for c in hash1)
    assert len(hash1) == 64


def test_generate_code_verifier():
    """PKCE code verifier should be a URL-safe random string."""
    verifier = generate_code_verifier()
    assert isinstance(verifier, str)
    assert len(verifier) > 43
    assert len(verifier) <= 128


def test_generate_code_challenge():
    """PKCE code challenge should be S256 hash of verifier."""
    verifier = "test_code_verifier"
    challenge = generate_code_challenge(verifier)

    assert isinstance(challenge, str)
    assert "=" not in challenge
    assert len(challenge) > 0

    challenge2 = generate_code_challenge(verifier)
    assert challenge == challenge2


def test_build_authorization_url_without_pkce():
    """Build authorization URL without PKCE."""
    url = build_authorization_url(
        auth_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
        client_id="test_client_id",
        redirect_uri="https://example.com/callback",
        state="test_state",
        scope="openid email profile",
    )

    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=test_client_id" in url
    assert "redirect_uri=https%3A%2F%2Fexample.com%2Fcallback" in url
    assert "response_type=code" in url
    assert "scope=openid+email+profile" in url
    assert "state=test_state" in url
    assert "access_type=offline" in url

    assert "code_challenge" not in url
    assert "code_challenge_method" not in url


def test_build_authorization_url_with_pkce():
    """Build authorization URL with PKCE challenge."""
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier)

    url = build_authorization_url(
        auth_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
        client_id="test_client_id",
        redirect_uri="https://example.com/callback",
        state="test_state",
        scope="openid email profile",
        code_challenge=challenge,
    )

    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=test_client_id" in url
    assert f"code_challenge={challenge}" in url
    assert "code_challenge_method=S256" in url
    assert "access_type=offline" in url
