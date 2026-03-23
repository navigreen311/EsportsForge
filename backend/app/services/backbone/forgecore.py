"""ForgeCore Orchestrator — the master decision layer for EsportsForge.

ForgeCore receives output from every active agent, resolves conflicts,
weights by context, filters by information density, and delivers ONE
decisive recommendation to the player.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Callable, Awaitable

import structlog

from app.schemas.forgecore import (
    AgentOutput,
    AgentStatus,
    ConflictResolution,
    DecisionContext,
    ForgeCoreDecision,
    ForgeCoreRequest,
    GameMode,
    PressureState,
)
from app.services.backbone.agent_registry import AgentRegistry, AgentRegistryEntry
from app.services.backbone.conflict_resolver import ConflictResolver

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Type alias for pluggable agent callables
# ---------------------------------------------------------------------------
AgentCallable = Callable[[DecisionContext], Awaitable[AgentOutput]]

# ---------------------------------------------------------------------------
# Information density rules
# ---------------------------------------------------------------------------
DENSITY_MAP: dict[PressureState, str] = {
    PressureState.CRITICAL: "minimal",   # clock is ticking — fewest words possible
    PressureState.HIGH: "minimal",
    PressureState.MEDIUM: "standard",
    PressureState.LOW: "detailed",       # plenty of time — give the deep reasoning
}


class ForgeCore:
    """Master orchestrator that turns N agent voices into one decisive answer."""

    def __init__(
        self,
        registry: AgentRegistry,
        resolver: ConflictResolver | None = None,
        agent_callables: dict[str, AgentCallable] | None = None,
    ) -> None:
        self._registry = registry
        self._resolver = resolver or ConflictResolver()
        self._callables: dict[str, AgentCallable] = agent_callables or {}

    # -- public: register agent callables -----------------------------------

    def register_callable(self, name: str, fn: AgentCallable) -> None:
        """Register an async callable that produces an AgentOutput."""
        self._callables[name] = fn

    # -- master orchestration -----------------------------------------------

    async def orchestrate(
        self,
        user_id: str,
        title: str,
        context: DecisionContext,
        requested_agents: list[str] | None = None,
    ) -> ForgeCoreDecision:
        """End-to-end orchestration: collect -> resolve -> weight -> filter -> deliver."""

        log = logger.bind(user_id=user_id, title=title, mode=context.mode)
        log.info("forgecore.orchestrate.start")

        # 1. Gather agent outputs
        agents = self._registry.get_for_decision(title, context, requested_agents)
        outputs = await self.collect_agent_outputs(agents, context)
        log.info("forgecore.collected", agent_count=len(outputs))

        if not outputs:
            return self._empty_decision(user_id, title, context)

        # 2. Full conflict resolution pipeline (veto, confidence, weight, priority)
        winner, conflicts, filtered_count = self._resolver.run(outputs, context)

        if winner is None:
            log.warning("forgecore.all_filtered", filtered=filtered_count)
            return self._empty_decision(user_id, title, context, filtered_count=filtered_count)

        # 3. Density filtering on the winning output
        density = self._density_for(context)
        recommendation, reasoning = self.filter_by_density(
            winner.recommendation, winner.reasoning, density,
        )

        # 4. Build final decision
        decision = ForgeCoreDecision(
            decision_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            recommendation=recommendation,
            reasoning=reasoning,
            confidence=winner.confidence,
            context_used=context,
            contributing_agents=[o.agent_name for o in outputs if not o.vetoed],
            conflicts_resolved=conflicts,
            filtered_count=filtered_count,
            information_density=density,
            timestamp=datetime.utcnow(),
        )

        log.info(
            "forgecore.decision",
            winner=winner.agent_name,
            confidence=winner.confidence,
            conflicts=len(conflicts),
        )
        return decision

    # -- collect ------------------------------------------------------------

    async def collect_agent_outputs(
        self,
        agents: list[AgentRegistryEntry],
        context: DecisionContext,
    ) -> list[AgentOutput]:
        """Call every eligible agent and gather outputs.

        Agents that raise exceptions are logged and skipped — a single
        failing agent must never block the entire decision cycle.
        """
        outputs: list[AgentOutput] = []
        for agent in agents:
            fn = self._callables.get(agent.name)
            if fn is None:
                logger.warning("forgecore.no_callable", agent=agent.name)
                continue
            try:
                result = await fn(context)
                outputs.append(result)
            except Exception:
                logger.exception("forgecore.agent_error", agent=agent.name)
                self._registry.update_status(agent.name, AgentStatus.DEGRADED)
        return outputs

    # -- density filter -----------------------------------------------------

    @staticmethod
    def _density_for(context: DecisionContext) -> str:
        return DENSITY_MAP.get(context.pressure_state, "standard")

    @staticmethod
    def filter_by_density(
        recommendation: str,
        reasoning: str,
        density: str,
    ) -> tuple[str, str]:
        """Trim output to match the target information density.

        * **minimal** — recommendation only, no reasoning (time-critical).
        * **standard** — recommendation + first sentence of reasoning.
        * **detailed** — everything.
        """
        if density == "minimal":
            return recommendation, ""
        if density == "standard":
            # Keep first sentence of reasoning
            first_sentence = reasoning.split(". ")[0]
            if first_sentence and not first_sentence.endswith("."):
                first_sentence += "."
            return recommendation, first_sentence
        # detailed
        return recommendation, reasoning

    # -- deliver (hook point for future WebSocket / push) -------------------

    @staticmethod
    def deliver_decision(decision: ForgeCoreDecision) -> dict[str, Any]:
        """Serialize the decision for API delivery.

        This is a thin wrapper today; in the future it will push via
        WebSocket and write to the decision log.
        """
        return decision.model_dump(mode="json")

    # -- helpers ------------------------------------------------------------

    def _empty_decision(
        self,
        user_id: str,
        title: str,
        context: DecisionContext,
        filtered_count: int = 0,
    ) -> ForgeCoreDecision:
        return ForgeCoreDecision(
            decision_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            recommendation="No actionable recommendation available at this time.",
            reasoning="All agent outputs were filtered or no agents were available.",
            confidence=0.0,
            context_used=context,
            contributing_agents=[],
            conflicts_resolved=[],
            filtered_count=filtered_count,
            information_density=self._density_for(context),
            timestamp=datetime.utcnow(),
        )

    async def orchestrate_from_request(self, request: ForgeCoreRequest) -> ForgeCoreDecision:
        """Convenience wrapper that unpacks a ``ForgeCoreRequest``."""
        return await self.orchestrate(
            user_id=request.user_id,
            title=request.title,
            context=request.context,
            requested_agents=request.requested_agents,
        )
