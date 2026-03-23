"""LangGraph-based multi-agent orchestrator for ForgeCore.

Defines a StateGraph that routes through:
  collect_data → run_agents → resolve_conflicts → filter_density → deliver

Each agent node calls Claude with an agent-specific system prompt.
ForgeCore acts as the final reducer node that merges all agent outputs
into one decisive recommendation.
"""

from __future__ import annotations

import json
from typing import Any, TypedDict

import structlog
from langgraph.graph import END, StateGraph

from app.core.config import settings
from app.schemas.forgecore import GameMode, PressureState
from app.services.ai.agent_prompts import AGENT_PROMPTS
from app.services.ai.claude_client import ClaudeClient

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------

class ForgeState(TypedDict, total=False):
    """Shared state flowing through the LangGraph graph."""

    user_id: str
    title: str
    context: dict[str, Any]
    agent_outputs: list[dict[str, Any]]
    conflicts: list[dict[str, Any]]
    final_decision: dict[str, Any]
    density: str
    error: str | None


# ---------------------------------------------------------------------------
# Node helpers
# ---------------------------------------------------------------------------

def _context_prompt(context: dict[str, Any]) -> str:
    """Serialise context dict into the user-message for an agent call."""
    return json.dumps(context, default=str)


def _density_for_pressure(pressure: str) -> str:
    mapping = {
        PressureState.CRITICAL: "minimal",
        PressureState.HIGH: "minimal",
        PressureState.MEDIUM: "standard",
        PressureState.LOW: "detailed",
    }
    return mapping.get(PressureState(pressure), "standard")


# ---------------------------------------------------------------------------
# Agents to run per mode
# ---------------------------------------------------------------------------

_DEFAULT_AGENTS = ["gameplan", "scout", "impact_rank", "player_twin"]

_TOURNAMENT_AGENTS = ["scout", "impact_rank", "player_twin"]  # skip gameplan — too slow in tourney

_AGENT_SKIP_MAP: dict[str, list[str]] = {
    GameMode.TOURNAMENT: _TOURNAMENT_AGENTS,
    GameMode.SCRIM: _DEFAULT_AGENTS,
    GameMode.RANKED: _DEFAULT_AGENTS,
    GameMode.TRAINING: ["gameplan", "player_twin"],
    GameMode.CASUAL: ["gameplan"],
}


def _agents_for_mode(mode: str) -> list[str]:
    """Return the list of agents that should run for a given game mode."""
    try:
        return _AGENT_SKIP_MAP.get(GameMode(mode), _DEFAULT_AGENTS)
    except ValueError:
        return _DEFAULT_AGENTS


# ---------------------------------------------------------------------------
# Graph node functions
# ---------------------------------------------------------------------------

async def collect_data(state: ForgeState) -> ForgeState:
    """Prepare the shared state — determine density, pick agents."""
    context = state.get("context", {})
    pressure = context.get("pressure_state", "medium")
    state["density"] = _density_for_pressure(pressure)
    state["agent_outputs"] = []
    state["conflicts"] = []
    state["error"] = None
    logger.info("graph.collect_data", density=state["density"])
    return state


async def run_agents(state: ForgeState) -> ForgeState:
    """Execute each selected agent by calling Claude with its system prompt."""
    context = state.get("context", {})
    mode = context.get("mode", "ranked")
    agents = _agents_for_mode(mode)

    client = ClaudeClient()
    outputs: list[dict[str, Any]] = []

    for agent_name in agents:
        system_prompt = AGENT_PROMPTS.get(agent_name)
        if not system_prompt:
            logger.warning("graph.agent_prompt_missing", agent=agent_name)
            continue
        try:
            result = await client.generate_json(
                _context_prompt(context),
                system=system_prompt,
                temperature=0.3,
            )
            result["agent_name"] = agent_name
            outputs.append(result)
            logger.info("graph.agent_done", agent=agent_name, confidence=result.get("confidence"))
        except Exception:
            logger.exception("graph.agent_error", agent=agent_name)
            # Non-fatal — other agents continue
            continue

    state["agent_outputs"] = outputs
    return state


async def resolve_conflicts(state: ForgeState) -> ForgeState:
    """Detect and resolve conflicts between agent outputs using Claude."""
    outputs = state.get("agent_outputs", [])
    if len(outputs) <= 1:
        return state

    # Build a conflict detection prompt
    recommendations = [
        {"agent": o["agent_name"], "recommendation": o.get("recommendation", "")}
        for o in outputs
    ]

    client = ClaudeClient()
    detect_prompt = json.dumps({
        "task": "Identify any conflicting recommendations among these agents.",
        "agent_recommendations": recommendations,
        "output_format": {
            "conflicts": [
                {
                    "conflicting_agents": ["agent_a", "agent_b"],
                    "description": "what the conflict is",
                }
            ]
        },
    })

    try:
        conflict_result = await client.generate_json(
            detect_prompt,
            system=(
                "You detect conflicts between agent recommendations. "
                "Respond with valid JSON only — no markdown fences."
            ),
            temperature=0.1,
        )
        state["conflicts"] = conflict_result.get("conflicts", [])
    except Exception:
        logger.exception("graph.conflict_detection_error")
        state["conflicts"] = []

    return state


async def filter_density(state: ForgeState) -> ForgeState:
    """Apply information density filtering to agent outputs."""
    density = state.get("density", "standard")
    outputs = state.get("agent_outputs", [])

    if density == "minimal":
        # Strip reasoning for minimal density
        for o in outputs:
            o["reasoning"] = ""
    elif density == "standard":
        # Keep first sentence of reasoning
        for o in outputs:
            reasoning = o.get("reasoning", "")
            if reasoning:
                first = reasoning.split(". ")[0]
                if not first.endswith("."):
                    first += "."
                o["reasoning"] = first

    state["agent_outputs"] = outputs
    return state


async def deliver(state: ForgeState) -> ForgeState:
    """ForgeCore reducer: merge all agent outputs into one decision via Claude."""
    outputs = state.get("agent_outputs", [])
    context = state.get("context", {})
    conflicts = state.get("conflicts", [])

    if not outputs:
        state["final_decision"] = {
            "recommendation": "No actionable recommendation available at this time.",
            "reasoning": "All agent outputs were filtered or no agents were available.",
            "confidence": 0.0,
            "contributing_agents": [],
            "conflicts_resolved": [],
        }
        return state

    forgecore_prompt = AGENT_PROMPTS.get("forgecore", "")
    user_payload = json.dumps(
        {
            "agent_outputs": outputs,
            "context": context,
            "conflicts": conflicts,
        },
        default=str,
    )

    client = ClaudeClient()
    try:
        decision = await client.generate_json(
            user_payload,
            system=forgecore_prompt,
            temperature=0.2,
        )
        state["final_decision"] = decision
    except Exception:
        logger.exception("graph.deliver_error")
        # Fallback: pick highest-confidence agent output
        best = max(outputs, key=lambda o: o.get("confidence", 0))
        state["final_decision"] = {
            "recommendation": best.get("recommendation", "Unable to generate recommendation."),
            "reasoning": best.get("reasoning", ""),
            "confidence": best.get("confidence", 0.0),
            "contributing_agents": [best.get("agent_name", "unknown")],
            "conflicts_resolved": [],
        }

    return state


# ---------------------------------------------------------------------------
# Conditional edge: skip low-priority agents in tournament mode
# ---------------------------------------------------------------------------

def _should_resolve_conflicts(state: ForgeState) -> str:
    """Route after run_agents: go to conflict resolution or straight to deliver."""
    outputs = state.get("agent_outputs", [])
    if len(outputs) <= 1:
        return "filter_density"
    return "resolve_conflicts"


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_forge_graph() -> StateGraph:
    """Construct and compile the ForgeCore LangGraph state graph."""
    graph = StateGraph(ForgeState)

    graph.add_node("collect_data", collect_data)
    graph.add_node("run_agents", run_agents)
    graph.add_node("resolve_conflicts", resolve_conflicts)
    graph.add_node("filter_density", filter_density)
    graph.add_node("deliver", deliver)

    graph.set_entry_point("collect_data")
    graph.add_edge("collect_data", "run_agents")
    graph.add_conditional_edges(
        "run_agents",
        _should_resolve_conflicts,
        {
            "resolve_conflicts": "resolve_conflicts",
            "filter_density": "filter_density",
        },
    )
    graph.add_edge("resolve_conflicts", "filter_density")
    graph.add_edge("filter_density", "deliver")
    graph.add_edge("deliver", END)

    return graph


# ---------------------------------------------------------------------------
# High-level orchestrator class
# ---------------------------------------------------------------------------

class ForgeOrchestrator:
    """High-level wrapper that runs the LangGraph ForgeCore pipeline."""

    def __init__(self) -> None:
        self._graph = build_forge_graph().compile()

    async def run(
        self,
        user_id: str,
        title: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the full ForgeCore pipeline and return the final decision."""
        initial_state: ForgeState = {
            "user_id": user_id,
            "title": title,
            "context": context,
            "agent_outputs": [],
            "conflicts": [],
            "final_decision": {},
            "density": "standard",
            "error": None,
        }

        result = await self._graph.ainvoke(initial_state)
        return result.get("final_decision", {})
