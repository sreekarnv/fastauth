"""Application settings and configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    # JWT Settings
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = "sqlite:///./rbac_blog.db"

    # FastAuth Settings
    require_email_verification: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
