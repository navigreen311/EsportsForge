"""System status endpoints (admin-level observability)."""

import platform
import time

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_db
from app.db.base import engine

router = APIRouter()


@router.get("/info")
async def system_info():
    """Return application metadata: version, environment, uptime, Python version."""
    from app.main import _start_time

    uptime_seconds = round(time.time() - _start_time, 2) if _start_time else 0.0

    return {
        "app_name": settings.app_name,
        "version": "0.1.0",
        "environment": settings.environment,
        "python_version": platform.python_version(),
        "uptime_seconds": uptime_seconds,
    }


@router.get("/db-stats")
async def db_stats(db: AsyncSession = Depends(get_db)):
    """Return row counts for core database tables."""
    tables = [
        "users",
        "gameplans",
        "recommendations",
        "game_sessions",
        "player_profiles",
        "opponents",
        "drills",
        "impact_rankings",
        "agent_performances",
    ]
    counts: dict[str, int] = {}
    for table in tables:
        try:
            result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))  # noqa: S608
            counts[table] = result.scalar_one()
        except Exception:
            counts[table] = -1  # table may not exist yet
    return {"table_row_counts": counts}
