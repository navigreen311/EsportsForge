"""Health endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.adapters.registry import registered_titles
from app.core.session import registry

router = APIRouter()


@router.get("/api/health")
async def health() -> dict:
    return {
        "status": "healthy",
        "service": "visionaudioforge_core",
        "active_sessions": registry.active_count(),
        "registered_adapters": [t.value for t in registered_titles()],
    }
