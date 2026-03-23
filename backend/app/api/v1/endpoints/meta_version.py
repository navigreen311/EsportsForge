"""Meta version endpoints — game meta tracking across patches."""

from __future__ import annotations

from fastapi import APIRouter, Query

router = APIRouter(prefix="/meta-version", tags=["Meta Versioning"])


@router.get("/current")
async def get_current_meta(
    title: str = Query(..., description="Game title"),
):
    """Get the current meta state for a title."""
    return {"title": title, "meta_version": None, "status": "stub — implementation pending"}


@router.get("/history")
async def get_meta_history(
    title: str = Query(..., description="Game title"),
    limit: int = Query(10, ge=1, le=50),
):
    """Get meta version history for a title."""
    return {"title": title, "versions": [], "status": "stub — implementation pending"}


@router.get("/diff")
async def get_meta_diff(
    title: str = Query(..., description="Game title"),
    from_version: str = Query(..., description="Previous meta version"),
    to_version: str = Query(..., description="Target meta version"),
):
    """Compare two meta versions to see what changed."""
    return {
        "title": title,
        "from_version": from_version,
        "to_version": to_version,
        "changes": [],
        "status": "stub — implementation pending",
    }
