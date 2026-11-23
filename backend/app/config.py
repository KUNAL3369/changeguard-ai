import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_env_file() -> str:
    """Find .env file starting from current dir and going up."""
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):  # Go up max 5 levels
        env_path = os.path.join(current, ".env")
        if os.path.exists(env_path):
            return env_path
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return ".env"  # fallback


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=get_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database (required, no defaults)
    postgres_user: str = Field(..., validation_alias="POSTGRES_USER")
    postgres_password: str = Field(..., validation_alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(..., validation_alias="POSTGRES_DB")
    postgres_host: str = Field("localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(5433, validation_alias="POSTGRES_PORT")

    # Application
    secret_key: str = Field(..., validation_alias="SECRET_KEY")
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")
    max_upload_mb: int = Field(10, validation_alias="MAX_UPLOAD_MB")

    @property
    def database_url_sync(self) -> str:
        """Synchronous database URL for SQLAlchemy (psycopg)."""
        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
