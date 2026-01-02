"""Application settings for OAuth Google example."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # JWT Settings
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Email Settings (using console for development)
    email_backend: str = "console"
    require_email_verification: bool = False  # Simplified for OAuth demo

    # Google OAuth Settings
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:8000/oauth/google/callback"

    # Database
    database_url: str = "sqlite:///./oauth_example.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
