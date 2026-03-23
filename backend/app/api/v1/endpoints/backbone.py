"""Backbone status endpoints — system health and registered agents."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["Backbone"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class BackboneSystemStatus(BaseModel):
    """Health state of a single backbone system."""

    name: str
    display_name: str
    status: str = Field(description="Status: operational | degraded | offline | initializing.")
    last_heartbeat: str
    description: str


class BackboneStatusResponse(BaseModel):
    """Aggregate status of all 6 backbone systems."""

    overall: str
    systems: list[BackboneSystemStatus]


class RegisteredAgent(BaseModel):
    """An agent registered in the backbone."""

    name: str
    titles: list[str]
    capabilities: list[str]
    status: str
    priority: int
    last_heartbeat: str


class AgentListResponse(BaseModel):
    """List of all registered agents with health."""

    total: int
    agents: list[RegisteredAgent]


# ---------------------------------------------------------------------------
# Mock backbone state
# ---------------------------------------------------------------------------

_now_iso = datetime.now(timezone.utc).isoformat()

_BACKBONE_SYSTEMS: list[dict] = [
    {
        "name": "forge_data_fabric",
        "display_name": "Forge Data Fabric",
        "status": "operational",
        "last_heartbeat": _now_iso,
        "description": "Unified data layer — ingests, normalizes, and distributes game data to all agents.",
    },
    {
        "name": "forge_core",
        "display_name": "ForgeCore Orchestrator",
        "status": "operational",
        "last_heartbeat": _now_iso,
        "description": "Central AI orchestrator — resolves conflicts and delivers ONE decision.",
    },
    {
        "name": "player_twin",
        "display_name": "Player Twin",
        "status": "operational",
        "last_heartbeat": _now_iso,
        "description": "Digital twin of the player — models preferences, fatigue, tilt, and style.",
    },
    {
        "name": "impact_rank",
        "display_name": "ImpactRank",
        "status": "operational",
        "last_heartbeat": _now_iso,
        "description": "Scoring engine that ranks recommendation impact for tie-breaking.",
    },
    {
        "name": "truth_engine",
        "display_name": "Truth Engine",
        "status": "operational",
        "last_heartbeat": _now_iso,
        "description": "Audit system — tracks prediction accuracy and agent trustworthiness.",
    },
    {
        "name": "loop_ai",
        "display_name": "LoopAI",
        "status": "operational",
        "last_heartbeat": _now_iso,
        "description": "Continuous learning loop — retrains models based on session outcomes.",
    },
]

_REGISTERED_AGENTS: list[dict] = [
    {
        "name": "MetaVersionAgent",
        "titles": ["madden26", "cfb26", "eafc26"],
        "capabilities": ["meta_analysis", "formation_tracking", "play_recommendation"],
        "status": "active",
        "priority": 1,
        "last_heartbeat": _now_iso,
    },
    {
        "name": "OpponentModelAgent",
        "titles": ["madden26", "cfb26", "eafc26", "nba2k26"],
        "capabilities": ["opponent_modeling", "tendency_detection", "counter_strategy"],
        "status": "active",
        "priority": 2,
        "last_heartbeat": _now_iso,
    },
    {
        "name": "CoachAgent",
        "titles": ["madden26", "cfb26"],
        "capabilities": ["play_calling", "situational_awareness", "adjustment_suggestion"],
        "status": "active",
        "priority": 3,
        "last_heartbeat": _now_iso,
    },
    {
        "name": "DrillAgent",
        "titles": ["madden26", "cfb26", "fortnite", "ufc5"],
        "capabilities": ["skill_assessment", "drill_generation", "progression_tracking"],
        "status": "active",
        "priority": 4,
        "last_heartbeat": _now_iso,
    },
    {
        "name": "MentalGameAgent",
        "titles": ["madden26", "cfb26", "fortnite", "ufc5", "nba2k26"],
        "capabilities": ["tilt_detection", "confidence_modeling", "reset_protocol"],
        "status": "active",
        "priority": 5,
        "last_heartbeat": _now_iso,
    },
    {
        "name": "FilmStudyAgent",
        "titles": ["madden26", "cfb26"],
        "capabilities": ["replay_analysis", "tendency_charting", "highlight_extraction"],
        "status": "active",
        "priority": 6,
        "last_heartbeat": _now_iso,
    },
    {
        "name": "BuildStrategyAgent",
        "titles": ["fortnite"],
        "capabilities": ["build_optimization", "edit_sequencing", "material_management"],
        "status": "active",
        "priority": 2,
        "last_heartbeat": _now_iso,
    },
    {
        "name": "VideoPokerStrategyAgent",
        "titles": ["video_poker"],
        "capabilities": ["optimal_hold", "pay_table_analysis", "bankroll_management"],
        "status": "active",
        "priority": 1,
        "last_heartbeat": _now_iso,
    },
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/status",
    response_model=BackboneStatusResponse,
    summary="All 6 backbone system states",
)
async def backbone_status() -> BackboneStatusResponse:
    """Return the health status of every backbone system."""
    systems = [BackboneSystemStatus(**s) for s in _BACKBONE_SYSTEMS]

    statuses = {s.status for s in systems}
    if statuses == {"operational"}:
        overall = "operational"
    elif "offline" in statuses:
        overall = "degraded"
    else:
        overall = "partial"

    return BackboneStatusResponse(overall=overall, systems=systems)


@router.get(
    "/agents",
    response_model=AgentListResponse,
    summary="List all registered agents with health",
)
async def list_backbone_agents() -> AgentListResponse:
    """Return every agent registered in the backbone with current health."""
    agents = [RegisteredAgent(**a) for a in _REGISTERED_AGENTS]
    return AgentListResponse(total=len(agents), agents=agents)
