"""Tests for the ForgeCore conflict resolution engine."""

from __future__ import annotations

import pytest

from app.schemas.forgecore import (
    AgentOutput,
    DecisionContext,
    GameMode,
    PressureState,
)
from app.services.backbone.conflict_resolver import ConflictResolver


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def resolver() -> ConflictResolver:
    return ConflictResolver()


@pytest.fixture
def ctx_tournament_critical() -> DecisionContext:
    return DecisionContext(
        mode=GameMode.TOURNAMENT,
        pressure_state=PressureState.CRITICAL,
    )


@pytest.fixture
def ctx_training_low() -> DecisionContext:
    return DecisionContext(
        mode=GameMode.TRAINING,
        pressure_state=PressureState.LOW,
    )


@pytest.fixture
def ctx_ranked_medium() -> DecisionContext:
    return DecisionContext(
        mode=GameMode.RANKED,
        pressure_state=PressureState.MEDIUM,
    )


def _output(
    name: str = "meta_bot",
    confidence: float = 0.80,
    recommendation: str = "Run play X",
    impact_rank: float = 50.0,
    vetoed: bool = False,
    veto_reason: str | None = None,
) -> AgentOutput:
    return AgentOutput(
        agent_name=name,
        recommendation=recommendation,
        confidence=confidence,
        reasoning="Some reasoning.",
        impact_rank_score=impact_rank,
        vetoed=vetoed,
        veto_reason=veto_reason,
    )


# ---------------------------------------------------------------------------
# PlayerTwin veto
# ---------------------------------------------------------------------------

class TestPlayerTwinVeto:
    def test_vetoed_outputs_are_removed(self, resolver: ConflictResolver):
        outputs = [
            _output("meta_bot", vetoed=True, veto_reason="Player fatigued"),
            _output("impact_rank"),
        ]
        surviving, vetoed = resolver.apply_player_twin_veto(outputs)
        assert len(surviving) == 1
        assert surviving[0].agent_name == "impact_rank"
        assert len(vetoed) == 1
        assert vetoed[0].agent_name == "meta_bot"

    def test_player_twin_itself_never_vetoed(self, resolver: ConflictResolver):
        outputs = [
            _output("player_twin", vetoed=True),  # should NOT be dropped
        ]
        surviving, vetoed = resolver.apply_player_twin_veto(outputs)
        assert len(surviving) == 1
        assert surviving[0].agent_name == "player_twin"
        assert len(vetoed) == 0

    def test_no_vetoes_passes_all(self, resolver: ConflictResolver):
        outputs = [_output("a"), _output("b")]
        surviving, vetoed = resolver.apply_player_twin_veto(outputs)
        assert len(surviving) == 2
        assert len(vetoed) == 0


# ---------------------------------------------------------------------------
# Confidence threshold
# ---------------------------------------------------------------------------

class TestConfidenceThreshold:
    def test_tournament_critical_requires_high_confidence(
        self, resolver: ConflictResolver, ctx_tournament_critical: DecisionContext
    ):
        outputs = [
            _output("meta_bot", confidence=0.75),   # above 0.70
            _output("loop_ai", confidence=0.60),     # below 0.70
        ]
        passing, filtered = resolver.filter_by_confidence(outputs, ctx_tournament_critical)
        assert len(passing) == 1
        assert passing[0].agent_name == "meta_bot"
        assert len(filtered) == 1

    def test_training_low_accepts_low_confidence(
        self, resolver: ConflictResolver, ctx_training_low: DecisionContext
    ):
        outputs = [_output("meta_bot", confidence=0.25)]  # above 0.20
        passing, filtered = resolver.filter_by_confidence(outputs, ctx_training_low)
        assert len(passing) == 1
        assert len(filtered) == 0

    def test_default_threshold_applies(self, resolver: ConflictResolver):
        ctx = DecisionContext(mode=GameMode.CASUAL, pressure_state=PressureState.MEDIUM)
        outputs = [
            _output("a", confidence=0.50),  # above 0.40 default
            _output("b", confidence=0.30),  # below 0.40 default
        ]
        passing, filtered = resolver.filter_by_confidence(outputs, ctx)
        assert len(passing) == 1
        assert len(filtered) == 1


# ---------------------------------------------------------------------------
# Context weighting
# ---------------------------------------------------------------------------

class TestContextWeighting:
    def test_tournament_mode_boosts_confidence(
        self, resolver: ConflictResolver, ctx_tournament_critical: DecisionContext
    ):
        outputs = [_output("meta_bot", confidence=0.80)]
        weighted = resolver.apply_context_weights(outputs, ctx_tournament_critical)
        # Tournament weight = 1.20, so 0.80 * 1.20 = 0.96
        assert weighted[0].confidence == pytest.approx(0.96, abs=0.01)

    def test_training_mode_reduces_confidence(
        self, resolver: ConflictResolver, ctx_training_low: DecisionContext
    ):
        outputs = [_output("meta_bot", confidence=0.80)]
        weighted = resolver.apply_context_weights(outputs, ctx_training_low)
        # Training weight = 0.60, so 0.80 * 0.60 = 0.48
        assert weighted[0].confidence == pytest.approx(0.48, abs=0.01)

    def test_confidence_capped_at_1(
        self, resolver: ConflictResolver, ctx_tournament_critical: DecisionContext
    ):
        outputs = [_output("meta_bot", confidence=0.95)]
        weighted = resolver.apply_context_weights(outputs, ctx_tournament_critical)
        # 0.95 * 1.20 = 1.14 -> capped to 1.0
        assert weighted[0].confidence == 1.0

    def test_original_not_mutated(
        self, resolver: ConflictResolver, ctx_tournament_critical: DecisionContext
    ):
        original = _output("meta_bot", confidence=0.80)
        resolver.apply_context_weights([original], ctx_tournament_critical)
        assert original.confidence == 0.80  # unchanged


# ---------------------------------------------------------------------------
# Priority resolution
# ---------------------------------------------------------------------------

class TestPriorityResolution:
    def test_higher_priority_wins(self, resolver: ConflictResolver):
        outputs = [
            _output("loop_ai", confidence=0.90),       # priority 50
            _output("player_twin", confidence=0.70),    # priority 10 — wins
        ]
        winner, conflicts = resolver.resolve(outputs)
        assert winner.agent_name == "player_twin"
        assert len(conflicts) == 1
        assert conflicts[0].resolution_method == "priority"

    def test_impact_rank_breaks_ties(self, resolver: ConflictResolver):
        # Two agents with same default priority (50)
        custom = ConflictResolver(agent_priorities={"agent_a": 30, "agent_b": 30})
        outputs = [
            _output("agent_a", impact_rank=40.0),
            _output("agent_b", impact_rank=80.0),  # higher IR wins
        ]
        winner, conflicts = custom.resolve(outputs)
        assert winner.agent_name == "agent_b"
        assert conflicts[0].resolution_method == "impact_rank"

    def test_single_output_no_conflicts(self, resolver: ConflictResolver):
        outputs = [_output("meta_bot")]
        winner, conflicts = resolver.resolve(outputs)
        assert winner.agent_name == "meta_bot"
        assert len(conflicts) == 0

    def test_empty_raises(self, resolver: ConflictResolver):
        with pytest.raises(ValueError, match="zero agent outputs"):
            resolver.resolve([])


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

class TestFullPipeline:
    def test_full_run_happy_path(
        self, resolver: ConflictResolver, ctx_ranked_medium: DecisionContext
    ):
        outputs = [
            _output("meta_bot", confidence=0.85, impact_rank=60.0),
            _output("player_twin", confidence=0.75, impact_rank=30.0),
        ]
        winner, conflicts, filtered = resolver.run(outputs, ctx_ranked_medium)
        assert winner is not None
        assert winner.agent_name == "player_twin"  # priority 10 beats 20
        assert filtered == 0

    def test_all_vetoed_returns_none(
        self, resolver: ConflictResolver, ctx_ranked_medium: DecisionContext
    ):
        outputs = [
            _output("meta_bot", vetoed=True),
            _output("loop_ai", vetoed=True),
        ]
        winner, conflicts, filtered = resolver.run(outputs, ctx_ranked_medium)
        assert winner is None
        assert filtered == 2

    def test_all_below_confidence_returns_none(
        self, resolver: ConflictResolver, ctx_tournament_critical: DecisionContext
    ):
        outputs = [
            _output("meta_bot", confidence=0.30),
            _output("loop_ai", confidence=0.20),
        ]
        winner, conflicts, filtered = resolver.run(outputs, ctx_tournament_critical)
        assert winner is None
        assert filtered == 2

    def test_empty_inputs(
        self, resolver: ConflictResolver, ctx_ranked_medium: DecisionContext
    ):
        winner, conflicts, filtered = resolver.run([], ctx_ranked_medium)
        assert winner is None
        assert filtered == 0
