"""Gameplan endpoints — strategic play-calling sheet management."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["Gameplans"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class GameplanGenerateRequest(BaseModel):
    """Request payload for AI-generated gameplan."""

    user_id: uuid.UUID
    title: str = Field(max_length=100, description="Game title slug.")
    opponent_id: uuid.UUID | None = None
    mode: str = Field(default="ranked", description="Game mode context.")
    preferences: dict[str, Any] = Field(
        default_factory=dict,
        description="Player style preferences the AI should consider.",
    )


class GameplanOut(BaseModel):
    """Response schema for a gameplan."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    opponent_id: uuid.UUID | None = None
    plays: list[dict[str, Any]] | None = None
    kill_sheet: dict[str, Any] | None = None
    meta_snapshot: str | None = None
    expires_at: datetime | None = None
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GameplanListOut(BaseModel):
    """Paginated list of gameplans."""

    items: list[GameplanOut]
    total: int
    page: int
    page_size: int


class GameplanDeleteAck(BaseModel):
    """Acknowledgement of gameplan archival."""

    gameplan_id: uuid.UUID
    status: str = "archived"


# ---------------------------------------------------------------------------
# Mock store
# ---------------------------------------------------------------------------

_gameplans: dict[uuid.UUID, dict] = {}


def _generate_mock_gameplan(req: GameplanGenerateRequest) -> dict:
    """Simulate GameplanAI producing a gameplan."""
    now = datetime.now(timezone.utc)
    return {
        "id": uuid.uuid4(),
        "user_id": req.user_id,
        "title": req.title,
        "opponent_id": req.opponent_id,
        "plays": [
            {
                "order": 1,
                "name": "Gun Bunch Wk — Mesh Post",
                "situation": "3rd & medium",
                "notes": "High success vs Cover-3; attack the seam.",
            },
            {
                "order": 2,
                "name": "Singleback Ace — HB Dive",
                "situation": "1st & 10",
                "notes": "Establish the run early to open play-action.",
            },
            {
                "order": 3,
                "name": "Shotgun Trips — Corner Strike",
                "situation": "Red zone",
                "notes": "Exploit soft zone coverage inside the 20.",
            },
        ],
        "kill_sheet": {
            "opponent_tendencies": {
                "cover_3_rate": 0.68,
                "blitz_rate": 0.22,
                "run_stuff_tendency": "weak side crash",
            },
            "exploits": [
                "Seam routes vs Cover-3 split-safety look.",
                "RPO left when DE crashes inside.",
            ],
        },
        "meta_snapshot": f"Meta v2026.03 — {req.title} current competitive meta.",
        "expires_at": (now + timedelta(days=7)).isoformat(),
        "is_archived": False,
        "created_at": now,
        "updated_at": now,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/generate",
    response_model=GameplanOut,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a gameplan via GameplanAI",
)
async def generate_gameplan(payload: GameplanGenerateRequest) -> GameplanOut:
    """Call GameplanAI to produce a strategic gameplan with plays and kill sheet."""
    plan = _generate_mock_gameplan(payload)
    _gameplans[plan["id"]] = plan
    return GameplanOut(**plan)


@router.get(
    "",
    response_model=GameplanListOut,
    summary="List user's gameplans",
)
async def list_gameplans(
    title: str | None = Query(default=None, description="Filter by game title."),
    include_archived: bool = Query(default=False, description="Include archived gameplans."),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> GameplanListOut:
    """Return a paginated list of the user's gameplans."""
    items = list(_gameplans.values())

    if not include_archived:
        items = [g for g in items if not g.get("is_archived")]
    if title:
        items = [g for g in items if g["title"] == title]

    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]

    return GameplanListOut(
        items=[GameplanOut(**g) for g in page_items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{gameplan_id}",
    response_model=GameplanOut,
    summary="Get gameplan detail with plays and kill sheet",
)
async def get_gameplan(gameplan_id: uuid.UUID) -> GameplanOut:
    """Retrieve a single gameplan with full plays and kill sheet."""
    plan = _gameplans.get(gameplan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameplan not found.",
        )
    return GameplanOut(**plan)


@router.delete(
    "/{gameplan_id}",
    response_model=GameplanDeleteAck,
    summary="Archive a gameplan",
)
async def archive_gameplan(gameplan_id: uuid.UUID) -> GameplanDeleteAck:
    """Soft-delete (archive) a gameplan. Does not permanently remove data."""
    plan = _gameplans.get(gameplan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameplan not found.",
        )

    plan["is_archived"] = True
    plan["updated_at"] = datetime.now(timezone.utc)
    return GameplanDeleteAck(gameplan_id=gameplan_id)
