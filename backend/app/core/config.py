"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """EsportsForge configuration."""

    # Application
    app_name: str = "EsportsForge"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./esportsforge.db"
    redis_url: str = ""

    # Auth
    secret_key: str = "esportsforge-dev-secret-change-in-production"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"

    # AI
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-5"

    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_competitive: str = ""
    stripe_price_elite: str = ""
    stripe_price_team: str = ""

    # Redis pool
    redis_max_connections: int = 50
    redis_socket_timeout: float = 5.0

    # Cache TTLs (seconds)
    cache_ttl_agent_output: int = 300
    cache_ttl_player_state: int = 300
    cache_ttl_meta_snapshot: int = 86400
    cache_ttl_opponent_dossier: int = 1800
    cache_ttl_session: int = 14400

    # Network / Logging
    allowed_hosts: list[str] = ["*"]
    log_level: str = "INFO"

    # CORS — dev defaults cover the ports the frontend may have fallen back to
    # when SiteForge / medlink-pro held :3000 / :8000. NextAuth runs auth
    # callbacks server-side so it doesn't trip CORS, but client-side fetches
    # (animaforge availability, daily-forge state, share-win lookups, ...) are
    # cross-origin from the browser to FastAPI and need the matching entry
    # here. Override via the CORS_ORIGINS env var in production.
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://localhost:8000",
        "http://localhost:8001",
    ]

    # AnimaForge integration
    animaforge_api_url: str = "http://localhost:3001"
    animaforge_api_key: str = ""
    animaforge_webhook_secret: str = ""           # HMAC for webhook verification
    animaforge_webhook_base_url: str = "http://localhost:8001"  # the URL AnimaForge calls back
    animaforge_default_quality: str = "standard"  # standard|high|low

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
