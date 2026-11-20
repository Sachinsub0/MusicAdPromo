"""Application configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Optional settings loaded from the environment."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    posthog_project_token: str | None = None
    posthog_host: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
