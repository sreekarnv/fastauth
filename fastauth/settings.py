from datetime import timedelta
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./fastauth.db"

    jwt_secret_key: str = "CHANGE_ME_SUPER_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    require_email_verification: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
