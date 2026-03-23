"""Tests for ForgeCore orchestrator — orchestration, context weighting, density filtering."""

from __future__ import annotations

import pytest
import pytest_asyncio

from app.schemas.forgecore import (
    AgentOutput,
    AgentStatus,
    DecisionContext,
    ForgeCoreRequest,
    GameMode,
    PressureState,
)
from app.services.backbone.agent_registry import AgentRegistry, AgentRegistryEntry
from app.services.backbone.conflict_resolver import ConflictResolver
from app.services.backbone.decision_context import ContextBuilder
from app.services.backbone.forgecore import ForgeCore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent_output(
    name: str,
    recommendation: str = "Do the thing",
    confidence: float = 0.80,
    impact_rank: float = 50.0,
    vetoed: bool = False,
    reasoning: str = "Solid reasoning. More details here.",
) -> AgentOutput:
    return AgentOutput(
        agent_name=name,
        recommendation=recommendation,
        confidence=confidence,
        reasoning=reasoning,
        impact_rank_score=impact_rank,
        vetoed=vetoed,
    )


def _make_callable(output: AgentOutput):
    """Return an async callable that yields the given output."""
    async def _call(ctx: DecisionContext) -> AgentOutput:
        return output
    return _call


def _failing_callable():
    """Return an async callable that always raises."""
    async def _call(ctx: DecisionContext) -> AgentOutput:
        raise RuntimeError("Agent crashed!")
    return _call


def _build_registry(*entries: AgentRegistryEntry) -> AgentRegistry:
    reg = AgentRegistry()
    for e in entries:
        reg.register(e)
    return reg


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ranked_ctx() -> DecisionContext:
    return (
        ContextBuilder()
        .mode(GameMode.RANKED)
        .pressure(PressureState.MEDIUM)
        .time("2:30 Q4")
        .opponent({"tendency": "zone_heavy"})
        .player({"fatigue": 0.2})
        .build()
    )


@pytest.fixture
def critical_ctx() -> DecisionContext:
    return DecisionContext(
        mode=GameMode.TOURNAMENT,
        pressure_state=PressureState.CRITICAL,
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

class TestOrchestration:
    @pytest.mark.asyncio
    async def test_single_agent_returns_its_recommendation(self, ranked_ctx):
        entry = AgentRegistryEntry(name="meta_bot", titles=["madden26"], priority=20)
        registry = _build_registry(entry)
        output = _make_agent_output("meta_bot", recommendation="Run Mesh Concept")

        core = ForgeCore(registry=registry)
        core.register_callable("meta_bot", _make_callable(output))

        decision = await core.orchestrate("user-1", "madden26", ranked_ctx)
        assert decision.recommendation == "Run Mesh Concept"
        assert decision.confidence > 0
        assert "meta_bot" in decision.contributing_agents

    @pytest.mark.asyncio
    async def test_multiple_agents_conflict_resolved(self, ranked_ctx):
        entries = [
            AgentRegistryEntry(name="meta_bot", titles=["madden26"], priority=20),
            AgentRegistryEntry(name="player_twin", titles=["madden26"], priority=10),
        ]
        registry = _build_registry(*entries)

        meta_out = _make_agent_output("meta_bot", "Blitz heavy", confidence=0.90)
        twin_out = _make_agent_output("player_twin", "Play conservative", confidence=0.75)

        core = ForgeCore(registry=registry)
        core.register_callable("meta_bot", _make_callable(meta_out))
        core.register_callable("player_twin", _make_callable(twin_out))

        decision = await core.orchestrate("user-1", "madden26", ranked_ctx)
        # player_twin has priority 10 (higher) so it wins
        assert decision.recommendation == "Play conservative"
        assert len(decision.conflicts_resolved) >= 1

    @pytest.mark.asyncio
    async def test_no_agents_returns_empty_decision(self, ranked_ctx):
        registry = AgentRegistry()
        core = ForgeCore(registry=registry)

        decision = await core.orchestrate("user-1", "madden26", ranked_ctx)
        assert decision.confidence == 0.0
        assert "no actionable" in decision.recommendation.lower()

    @pytest.mark.asyncio
    async def test_agent_crash_is_gracefully_handled(self, ranked_ctx):
        entries = [
            AgentRegistryEntry(name="meta_bot", titles=["madden26"], priority=20),
            AgentRegistryEntry(name="loop_ai", titles=["madden26"], priority=50),
        ]
        registry = _build_registry(*entries)

        good_out = _make_agent_output("loop_ai", "Safe choice", confidence=0.60)
        core = ForgeCore(registry=registry)
        core.register_callable("meta_bot", _failing_callable())
        core.register_callable("loop_ai", _make_callable(good_out))

        decision = await core.orchestrate("user-1", "madden26", ranked_ctx)
        # meta_bot crashed, loop_ai's output should win
        assert decision.recommendation == "Safe choice"
        # meta_bot should be marked degraded
        assert registry.get("meta_bot").status == AgentStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_requested_agents_filter(self, ranked_ctx):
        entries = [
            AgentRegistryEntry(name="meta_bot", titles=["madden26"], priority=20),
            AgentRegistryEntry(name="loop_ai", titles=["madden26"], priority=50),
        ]
        registry = _build_registry(*entries)

        meta_out = _make_agent_output("meta_bot", "Meta play")
        loop_out = _make_agent_output("loop_ai", "Loop play")

        core = ForgeCore(registry=registry)
        core.register_callable("meta_bot", _make_callable(meta_out))
        core.register_callable("loop_ai", _make_callable(loop_out))

        decision = await core.orchestrate(
            "user-1", "madden26", ranked_ctx, requested_agents=["loop_ai"],
        )
        assert decision.recommendation == "Loop play"
        assert "meta_bot" not in decision.contributing_agents


# ---------------------------------------------------------------------------
# Density filtering
# ---------------------------------------------------------------------------

class TestDensityFiltering:
    def test_minimal_strips_reasoning(self):
        rec, reason = ForgeCore.filter_by_density(
            "Run play X", "Because the opponent is weak. Also blitz rate is low.", "minimal",
        )
        assert rec == "Run play X"
        assert reason == ""

    def test_standard_keeps_first_sentence(self):
        rec, reason = ForgeCore.filter_by_density(
            "Run play X", "Because the opponent is weak. Also blitz rate is low.", "standard",
        )
        assert rec == "Run play X"
        assert reason == "Because the opponent is weak."

    def test_detailed_keeps_everything(self):
        full_reasoning = "Because the opponent is weak. Also blitz rate is low."
        rec, reason = ForgeCore.filter_by_density("Run play X", full_reasoning, "detailed")
        assert reason == full_reasoning

    @pytest.mark.asyncio
    async def test_critical_pressure_uses_minimal(self, critical_ctx):
        entry = AgentRegistryEntry(name="meta_bot", titles=["madden26"], priority=20)
        registry = _build_registry(entry)
        output = _make_agent_output(
            "meta_bot", "Audible to Slant", confidence=0.85,
            reasoning="Zone coverage detected. Slant beats it. Also consider hot route.",
        )
        core = ForgeCore(registry=registry)
        core.register_callable("meta_bot", _make_callable(output))

        decision = await core.orchestrate("user-1", "madden26", critical_ctx)
        assert decision.information_density == "minimal"
        assert decision.reasoning == ""  # stripped for critical pressure


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------

class TestContextBuilder:
    def test_fluent_builder(self):
        ctx = (
            ContextBuilder()
            .mode(GameMode.TOURNAMENT)
            .pressure(PressureState.HIGH)
            .time("0:42 Q4")
            .opponent({"blitz_rate": 0.68})
            .player({"fatigue": 0.3})
            .session("sess-123")
            .build()
        )
        assert ctx.mode == GameMode.TOURNAMENT
        assert ctx.pressure_state == PressureState.HIGH
        assert ctx.time_context == "0:42 Q4"
        assert ctx.opponent_info["blitz_rate"] == 0.68
        assert ctx.session_id == "sess-123"

    def test_from_session_data(self):
        data = {
            "mode": "training",
            "pressure_state": "low",
            "time_context": "Pregame",
            "opponent_info": {},
            "player_state": {"tilt": 0.0},
        }
        ctx = ContextBuilder.from_session_data(data)
        assert ctx.mode == GameMode.TRAINING
        assert ctx.pressure_state == PressureState.LOW

    def test_defaults(self):
        ctx = ContextBuilder().build()
        assert ctx.mode == GameMode.RANKED
        assert ctx.pressure_state == PressureState.MEDIUM


# ---------------------------------------------------------------------------
# Agent Registry (basic coverage — thorough tests in test_conflict_resolver)
# ---------------------------------------------------------------------------

class TestAgentRegistry:
    def test_register_and_get(self):
        registry = AgentRegistry()
        entry = AgentRegistryEntry(name="meta_bot", titles=["madden26"])
        registry.register(entry)
        assert registry.get("meta_bot") is not None
        assert registry.count == 1

    def test_unregister(self):
        registry = AgentRegistry()
        entry = AgentRegistryEntry(name="meta_bot", titles=["madden26"])
        registry.register(entry)
        assert registry.unregister("meta_bot") is True
        assert registry.get("meta_bot") is None
        assert registry.unregister("meta_bot") is False

    def test_query_by_title(self):
        registry = _build_registry(
            AgentRegistryEntry(name="a", titles=["madden26"]),
            AgentRegistryEntry(name="b", titles=["cfb26"]),
            AgentRegistryEntry(name="c", titles=["madden26", "cfb26"]),
        )
        results = registry.query(title="madden26")
        names = {e.name for e in results}
        assert names == {"a", "c"}

    def test_offline_excluded_from_decision(self):
        registry = _build_registry(
            AgentRegistryEntry(name="a", titles=["madden26"], status=AgentStatus.ACTIVE),
            AgentRegistryEntry(name="b", titles=["madden26"], status=AgentStatus.OFFLINE),
        )
        ctx = DecisionContext()
        eligible = registry.get_for_decision("madden26", ctx)
        assert len(eligible) == 1
        assert eligible[0].name == "a"

    def test_update_status(self):
        registry = AgentRegistry()
        registry.register(AgentRegistryEntry(name="x", titles=["madden26"]))
        registry.update_status("x", AgentStatus.DEGRADED)
        assert registry.get("x").status == AgentStatus.DEGRADED


# ---------------------------------------------------------------------------
# Deliver decision
# ---------------------------------------------------------------------------

class TestDeliverDecision:
    @pytest.mark.asyncio
    async def test_deliver_returns_serializable_dict(self, ranked_ctx):
        entry = AgentRegistryEntry(name="meta_bot", titles=["madden26"], priority=20)
        registry = _build_registry(entry)
        output = _make_agent_output("meta_bot")

        core = ForgeCore(registry=registry)
        core.register_callable("meta_bot", _make_callable(output))

        decision = await core.orchestrate("user-1", "madden26", ranked_ctx)
        payload = ForgeCore.deliver_decision(decision)
        assert isinstance(payload, dict)
        assert "recommendation" in payload
        assert "decision_id" in payload
