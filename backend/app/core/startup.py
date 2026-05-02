"""Startup validation — logs warnings for unsafe configuration."""
import logging

logger = logging.getLogger(__name__)


def validate_config(settings) -> None:
    """Check configuration and log warnings for production issues."""
    env = settings.environment
    logger.info("EsportsForge starting — environment=%s", env)

    if env == "production":
        if not settings.secret_key or "change" in settings.secret_key.lower() or "your_" in settings.secret_key.lower():
            logger.error("SECRET_KEY is not set for production! Authentication is insecure.")
        if "sqlite" in settings.database_url.lower():
            logger.warning("SQLite detected in production — use PostgreSQL for reliability.")
        if not settings.anthropic_api_key:
            logger.warning("ANTHROPIC_API_KEY not set — AI features will return mock data.")

    db_type = "SQLite" if "sqlite" in settings.database_url.lower() else "PostgreSQL"
    ai_status = "configured" if settings.anthropic_api_key and "your_" not in settings.anthropic_api_key.lower() else "mock mode"
    logger.info("Database: %s | AI: %s | Debug: %s", db_type, ai_status, settings.debug)
