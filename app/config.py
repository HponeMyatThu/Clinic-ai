"""GCMS Clinical AI Backend — Application Settings."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class AIProvider(str, Enum):
    OLLAMA = "ollama"


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "gcms-ai-backend"
    app_env: Environment = Environment.DEVELOPMENT
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: str = "INFO"

    # --- Database ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "gcms_ai"
    postgres_user: str = "gcms"
    postgres_password: str = "change_me_in_production"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        """Synchronous URL for Alembic migrations."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # --- Ollama ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"
    ollama_timeout: int = 120
    ollama_max_retries: int = 3

    # --- AI Behaviour ---
    ai_provider: AIProvider = AIProvider.OLLAMA
    ai_temperature: float = 0.0
    ai_max_tokens: int = 4096

    # --- SNOMED CT ---
    snomed_release_version: str = "dev-seed-2024"
    snomed_edition: str = "International"

    # --- SDD ---
    sdd_catalogue_version: str = "dev-seed-2024"

    # --- Security / JWT ---
    jwt_secret_key: str = "change_me_in_production"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "https://your-idp.example.com"
    jwt_audience: str = "gcms-ai-backend"
    access_token_expire_minutes: int = 30

    # --- CMS ---
    cms_base_url: str = "http://localhost:9000/api"
    cms_timeout: int = 30
    cms_max_retries: int = 2

    # --- Rate Limiting ---
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    # --- Privacy ---
    enable_pii_filter: bool = True


@lru_cache
def get_settings() -> Settings:
    """Cached singleton for application settings."""
    return Settings()

