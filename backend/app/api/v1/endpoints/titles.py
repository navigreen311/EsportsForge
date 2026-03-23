"""Title info endpoints — supported game titles, meta state, and agents."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["Titles"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TitleInfo(BaseModel):
    """Summary of a supported game title."""

    slug: str
    name: str
    genre: str
    status: str = Field(description="Current support status: active | beta | coming_soon.")
    agent_count: int


class TitleMeta(BaseModel):
    """Current meta snapshot for a title."""

    slug: str
    meta_version: str
    last_updated: str
    top_strategies: list[str]
    patch_notes_url: str | None = None
    summary: str


class TitleAgent(BaseModel):
    """An AI agent available for a specific title."""

    name: str
    capabilities: list[str]
    status: str
    priority: int


# ---------------------------------------------------------------------------
# Mock data — 11 supported titles
# ---------------------------------------------------------------------------

_TITLES: dict[str, dict] = {
    "madden26": {
        "slug": "madden26",
        "name": "Madden NFL 26",
        "genre": "sports",
        "status": "active",
        "agent_count": 4,
    },
    "cfb26": {
        "slug": "cfb26",
        "name": "EA Sports College Football 26",
        "genre": "sports",
        "status": "active",
        "agent_count": 3,
    },
    "eafc26": {
        "slug": "eafc26",
        "name": "EA Sports FC 26",
        "genre": "sports",
        "status": "active",
        "agent_count": 3,
    },
    "nba2k26": {
        "slug": "nba2k26",
        "name": "NBA 2K26",
        "genre": "sports",
        "status": "beta",
        "agent_count": 2,
    },
    "mlb26": {
        "slug": "mlb26",
        "name": "MLB The Show 26",
        "genre": "sports",
        "status": "beta",
        "agent_count": 2,
    },
    "ufc5": {
        "slug": "ufc5",
        "name": "EA Sports UFC 5",
        "genre": "fighting",
        "status": "active",
        "agent_count": 2,
    },
    "undisputed": {
        "slug": "undisputed",
        "name": "Undisputed",
        "genre": "fighting",
        "status": "beta",
        "agent_count": 2,
    },
    "pga2k25": {
        "slug": "pga2k25",
        "name": "PGA Tour 2K25",
        "genre": "sports",
        "status": "active",
        "agent_count": 2,
    },
    "fortnite": {
        "slug": "fortnite",
        "name": "Fortnite",
        "genre": "battle_royale",
        "status": "active",
        "agent_count": 3,
    },
    "warzone": {
        "slug": "warzone",
        "name": "Call of Duty: Warzone",
        "genre": "battle_royale",
        "status": "beta",
        "agent_count": 2,
    },
    "video_poker": {
        "slug": "video_poker",
        "name": "Video Poker",
        "genre": "casino",
        "status": "active",
        "agent_count": 3,
    },
}

_META: dict[str, dict] = {
    slug: {
        "slug": slug,
        "meta_version": "2026.03",
        "last_updated": "2026-03-20T00:00:00Z",
        "top_strategies": ["Strategy data pending — connect title-specific agent."],
        "patch_notes_url": None,
        "summary": f"Current competitive meta snapshot for {info['name']}.",
    }
    for slug, info in _TITLES.items()
}

_AGENTS: dict[str, list[dict]] = {
    slug: [
        {
            "name": f"{slug.capitalize()}MetaAgent",
            "capabilities": ["meta_analysis", "play_recommendation"],
            "status": "active",
            "priority": 1,
        },
        {
            "name": f"{slug.capitalize()}OpponentAgent",
            "capabilities": ["opponent_modeling", "counter_strategy"],
            "status": "active",
            "priority": 2,
        },
    ]
    for slug in _TITLES
}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[TitleInfo],
    summary="List all supported titles",
)
async def list_titles() -> list[TitleInfo]:
    """Return all 11 supported game titles with their current status."""
    return [TitleInfo(**t) for t in _TITLES.values()]


@router.get(
    "/{slug}/meta",
    response_model=TitleMeta,
    summary="Current meta state for a title",
)
async def get_title_meta(slug: str) -> TitleMeta:
    """Return the current competitive meta snapshot for a given title."""
    meta = _META.get(slug)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Title '{slug}' not found.",
        )
    return TitleMeta(**meta)


@router.get(
    "/{slug}/agents",
    response_model=list[TitleAgent],
    summary="List agents available for a title",
)
async def get_title_agents(slug: str) -> list[TitleAgent]:
    """Return the AI agents registered for a given title."""
    agents = _AGENTS.get(slug)
    if agents is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Title '{slug}' not found.",
        )
    return [TitleAgent(**a) for a in agents]
