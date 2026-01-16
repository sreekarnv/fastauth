"""
OAuth security utilities.

Provides cryptographic functions for OAuth flows including state tokens,
PKCE implementation, and authorization URL building.
"""

import base64
import hashlib
import secrets
from urllib.parse import urlencode


def generate_state_token() -> str:
    """
    Generate a cryptographically secure state token for CSRF protection.

    Uses same pattern as refresh tokens.

    Returns:
        URL-safe random token string
    """
    return secrets.token_urlsafe(48)


def hash_state_token(token: str) -> str:
    """
    Hash state token before storing.

    Uses SHA-256 hashing like other tokens.

    Args:
        token: Raw state token

    Returns:
        Hexadecimal hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def hash_oauth_token(token: str) -> str:
    """
    Hash OAuth provider tokens before storing.

    We store provider access/refresh tokens hashed for security.

    Args:
        token: Raw OAuth token from provider

    Returns:
        Hexadecimal hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


# PKCE (Proof Key for Code Exchange) Implementation
def generate_code_verifier() -> str:
    """
    Generate a cryptographically random code verifier for PKCE.

    Per RFC 7636, the code verifier should be 43-128 characters.
    We use 64 bytes for good entropy (~86 characters base64url encoded).

    Returns:
        URL-safe random string for PKCE code verifier
    """
    return secrets.token_urlsafe(64)


def generate_code_challenge(verifier: str) -> str:
    """
    Generate S256 code challenge from verifier.

    Challenge = BASE64URL(SHA256(verifier))

    Args:
        verifier: Code verifier string

    Returns:
        Base64url-encoded SHA-256 hash of the verifier (without padding)
    """
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return challenge


def build_authorization_url(
    *,
    auth_endpoint: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    scope: str,
    code_challenge: str | None = None,
) -> str:
    """
    Build OAuth authorization URL with PKCE support.

    Args:
        auth_endpoint: Provider's authorization endpoint URL
        client_id: OAuth client ID
        redirect_uri: Callback URL after authorization
        state: State token for CSRF protection
        scope: Space-separated list of OAuth scopes
        code_challenge: Optional PKCE code challenge

    Returns:
        Complete authorization URL with query parameters
    """
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "state": state,
        "access_type": "offline",  # Request refresh token
    }

    if code_challenge:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"

    return f"{auth_endpoint}?{urlencode(params)}"
