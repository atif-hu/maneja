from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve .env path relative to this file's location
_project_root = Path(__file__).parent.parent.parent.parent
_env_file = _project_root / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_env_file) if _env_file.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    database_url: str = ""
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_service_role_key: str = ""
    redis_url: str = "redis://127.0.0.1:6379"

    image_provider: str = "replicate"
    image_model: str = "google/nano-banana-2"

    embedding_provider: str = "stub"

    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-5"

    openai_api_key: str = ""
    replicate_api_key: str = ""
    pollinations_api_key: str = ""

    api_base_url: str = "http://localhost:8000"
    internal_job_secret: str = "change-me-internal-cron-secret"
    scheduler_interval_seconds: int = 60
    max_provider_retries: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()
