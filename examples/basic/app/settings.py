from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./fastauth.db"
    secret_key: str = "dev-secret-key"

    require_email_verification: bool = True

    email_backend: str = "console"

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str = "no-reply@example.com"
    smtp_use_tls: bool = True

    auto_create_tables: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
