"""ForgeCore API endpoints — the single interface to the orchestrator."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.forgecore import (
    AgentStatus,
    ForgeCoreDecision,
    ForgeCoreRequest,
)
from app.services.backbone.agent_registry import AgentRegistry, AgentRegistryEntry
from app.services.backbone.conflict_resolver import ConflictResolver
from app.services.backbone.forgecore import ForgeCore

router = APIRouter(prefix="/forgecore", tags=["ForgeCore"])

# ---------------------------------------------------------------------------
# Singleton instances (replaced by DI in production)
# ---------------------------------------------------------------------------
_registry = AgentRegistry()
_resolver = ConflictResolver()
_forgecore = ForgeCore(registry=_registry, resolver=_resolver)


def get_registry() -> AgentRegistry:
    """Accessor for the global registry (test-friendly)."""
    return _registry


def get_forgecore() -> ForgeCore:
    """Accessor for the global ForgeCore instance (test-friendly)."""
    return _forgecore


# ---------------------------------------------------------------------------
# POST /forgecore/decide
# ---------------------------------------------------------------------------

@router.post("/decide", response_model=ForgeCoreDecision)
async def request_decision(request: ForgeCoreRequest) -> ForgeCoreDecision:
    """Request a unified decision from ForgeCore.

    ForgeCore will:
    1. Query all active agents for the given title + context.
    2. Resolve conflicts via priority, ImpactRank, and PlayerTwin veto.
    3. Apply context weighting (mode, pressure, confidence).
    4. Filter by information density.
    5. Return ONE decisive recommendation.
    """
    decision = await _forgecore.orchestrate_from_request(request)
    return decision


# ---------------------------------------------------------------------------
# GET /forgecore/agents
# ---------------------------------------------------------------------------

@router.get("/agents")
async def list_agents(
    title: str | None = None,
    status: AgentStatus | None = None,
) -> list[dict]:
    """List registered agents, optionally filtered by title or status."""
    entries = _registry.query(title=title, status=status)
    return [
        {
            "name": e.name,
            "titles": e.titles,
            "capabilities": e.capabilities,
            "priority": e.priority,
            "status": e.status.value,
            "last_heartbeat": e.last_heartbeat.isoformat(),
        }
        for e in entries
    ]


# ---------------------------------------------------------------------------
# GET /forgecore/agents/{name}/status
# ---------------------------------------------------------------------------

@router.get("/agents/{name}/status")
async def agent_status(name: str) -> dict:
    """Return health status for a single agent."""
    entry: AgentRegistryEntry | None = _registry.get(name)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found.")
    return {
        "name": entry.name,
        "status": entry.status.value,
        "last_heartbeat": entry.last_heartbeat.isoformat(),
        "priority": entry.priority,
        "titles": entry.titles,
        "capabilities": entry.capabilities,
    }
