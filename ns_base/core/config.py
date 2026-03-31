"""
Application configuration using pydantic-settings.
All settings are loaded from environment variables with sensible defaults.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global application settings."""

    # Application
    APP_NAME: str = "Multi-Tenant SaaS Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./multitenant_saas.db"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Authentication
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # AI / LLM
    ANTHROPIC_API_KEY: str = ""
    DEFAULT_MODEL: str = "claude-sonnet-4-20250514"
    MAX_TOKENS_PER_REQUEST: int = 4096
    AGENT_MAX_ITERATIONS: int = 10

    # Tenant defaults
    DEFAULT_TENANT_PLAN: str = "free"
    MAX_AGENT_CALLS_FREE: int = 100
    MAX_AGENT_CALLS_PRO: int = 5000
    MAX_AGENT_CALLS_ENTERPRISE: int = -1  # unlimited

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": True}


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
