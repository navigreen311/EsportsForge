"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """EsportsForge configuration."""

    # Application
    app_name: str = "EsportsForge"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/esportsforge"
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    secret_key: str = "YOUR_SECRET_KEY_HERE"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"

    # AI
    anthropic_api_key: str = "YOUR_ANTHROPIC_API_KEY_HERE"
    claude_model: str = "claude-sonnet-4-20250514"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
