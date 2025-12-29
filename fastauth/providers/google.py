import httpx

from fastauth.providers.base import OAuthProvider, OAuthTokens, OAuthUserInfo


class GoogleOAuthProvider(OAuthProvider):
    """
    Google OAuth 2.0 provider implementation.

    Uses Google's OAuth 2.0 endpoints for authorization code flow.
    Supports PKCE and refresh tokens.
    """

    def __init__(self, *, client_id: str, client_secret: str):
        """
        Initialize Google OAuth provider.

        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret

    @property
    def name(self) -> str:
        """Provider name."""
        return "google"

    @property
    def authorization_endpoint(self) -> str:
        """Google OAuth authorization URL."""
        return "https://accounts.google.com/o/oauth2/v2/auth"

    @property
    def token_endpoint(self) -> str:
        """Google OAuth token exchange URL."""
        return "https://oauth2.googleapis.com/token"

    @property
    def user_info_endpoint(self) -> str:
        """Google user info API endpoint."""
        return "https://www.googleapis.com/oauth2/v2/userinfo"

    @property
    def default_scopes(self) -> str:
        """Default OAuth scopes for Google (space-separated)."""
        return "openid email profile"

    async def exchange_code_for_tokens(
        self,
        *,
        code: str,
        redirect_uri: str,
        code_verifier: str | None = None,
    ) -> OAuthTokens:
        """
        Exchange authorization code for access/refresh tokens.

        Args:
            code: Authorization code from callback
            redirect_uri: Redirect URI used in authorization
            code_verifier: Optional PKCE code verifier

        Returns:
            OAuthTokens with access token and optional refresh token

        Raises:
            httpx.HTTPError: If token exchange fails
        """
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_endpoint, data=data)
            response.raise_for_status()
            token_data = response.json()

        return OAuthTokens(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in"),
            token_type=token_data.get("token_type", "Bearer"),
        )

    async def get_user_info(self, *, access_token: str) -> OAuthUserInfo:
        """
        Fetch user information using access token.

        Args:
            access_token: OAuth access token

        Returns:
            OAuthUserInfo with user profile data

        Raises:
            httpx.HTTPError: If user info fetch fails
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(self.user_info_endpoint, headers=headers)
            response.raise_for_status()
            user_data = response.json()

        return OAuthUserInfo(
            provider_user_id=user_data["id"],
            email=user_data["email"],
            email_verified=user_data.get("verified_email", False),
            name=user_data.get("name"),
            avatar_url=user_data.get("picture"),
        )

    async def refresh_access_token(self, *, refresh_token: str) -> OAuthTokens:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: OAuth refresh token

        Returns:
            OAuthTokens with new access token

        Raises:
            httpx.HTTPError: If token refresh fails
        """
        data = {
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_endpoint, data=data)
            response.raise_for_status()
            token_data = response.json()

        return OAuthTokens(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in"),
            token_type=token_data.get("token_type", "Bearer"),
        )
