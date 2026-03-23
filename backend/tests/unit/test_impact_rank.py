"""Tests for ImpactRank AI — ranking, scoring, suppression, recalculation."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.schemas.impact_rank import (
    Fix,
    FixScore,
    ImpactScore,
    OutcomeVerdict,
    Weakness,
    WeaknessCategory,
)
from app.services.backbone.fix_scorer import (
    check_execution_feasibility,
    generate_fixes,
    score_fix_roi,
)
from app.services.backbone.impact_rank import ImpactRank
from app.services.backbone.weakness_detector import (
    categorize_weakness,
    detect_weaknesses,
    estimate_win_rate_damage,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine() -> ImpactRank:
    """Fresh ImpactRank engine per test."""
    return ImpactRank()


@pytest.fixture
def sample_weakness() -> Weakness:
    return Weakness(
        title="madden26",
        category=WeaknessCategory.DECISION,
        label="Poor red-zone playcalling",
        description="Consistently makes bad playcall decisions in the red zone.",
        evidence=["3 turnovers in red zone last 5 games", "12% red zone TD rate"],
    )


@pytest.fixture
def sample_player_data() -> dict:
    return {
        "user_id": "player-123",
        "stats": {"win_rate": 0.45, "games_played": 100},
        "weakness_hints": [
            {
                "label": "Poor red-zone playcalling",
                "description": "Bad decisions in scoring position under pressure.",
                "evidence": ["3 turnovers in red zone", "12% TD rate"],
                "context": {
                    "total_games": 100,
                    "losses_attributed": 15,
                    "avg_severity": 0.7,
                },
            },
            {
                "label": "Slow reaction to blitz",
                "description": "Fails to adjust timing when opponent brings pressure.",
                "evidence": ["Sacked 4+ times in 8 of last 10 games"],
                "context": {
                    "total_games": 100,
                    "losses_attributed": 10,
                    "avg_severity": 0.5,
                },
            },
            {
                "label": "Tilts after early deficit",
                "description": "Performance drops significantly when losing early.",
                "evidence": ["Win rate drops to 15% when trailing after Q1"],
            },
        ],
    }


# ---------------------------------------------------------------------------
# WeaknessDetector tests
# ---------------------------------------------------------------------------

class TestWeaknessDetector:
    def test_categorize_decision(self, sample_weakness: Weakness):
        cat = categorize_weakness(sample_weakness)
        assert cat == WeaknessCategory.DECISION

    def test_categorize_mechanical(self):
        w = Weakness(
            title="madden26",
            category=WeaknessCategory.DECISION,  # will be reclassified
            label="Poor stick accuracy",
            description="Timing and execution of inputs is inconsistent.",
        )
        assert categorize_weakness(w) == WeaknessCategory.MECHANICAL

    def test_categorize_mental(self):
        w = Weakness(
            title="madden26",
            category=WeaknessCategory.DECISION,
            label="Tilt after losses",
            description="Loses composure and patience under pressure.",
        )
        assert categorize_weakness(w) == WeaknessCategory.MENTAL

    def test_categorize_fallback(self):
        w = Weakness(
            title="madden26",
            category=WeaknessCategory.DECISION,
            label="Something vague",
            description="No matching keywords here.",
        )
        assert categorize_weakness(w) == WeaknessCategory.DECISION

    def test_estimate_win_rate_damage_with_context(self, sample_weakness: Weakness):
        context = {"total_games": 100, "losses_attributed": 20, "avg_severity": 0.8}
        score = estimate_win_rate_damage(sample_weakness, context)
        assert score.win_rate_damage > 0
        assert score.frequency == pytest.approx(0.2, abs=0.01)
        assert score.severity == pytest.approx(0.8, abs=0.01)
        assert score.confidence > 0.5  # 100 games = decent confidence

    def test_estimate_win_rate_damage_without_context(self, sample_weakness: Weakness):
        score = estimate_win_rate_damage(sample_weakness)
        assert score.win_rate_damage > 0
        assert score.confidence < 1.0  # lower confidence without real data

    def test_detect_weaknesses(self, sample_player_data: dict):
        weaknesses = detect_weaknesses(sample_player_data, "madden26")
        assert len(weaknesses) == 3
        for w in weaknesses:
            assert w.title == "madden26"
            assert w.impact_score is not None
            assert isinstance(w.category, WeaknessCategory)


# ---------------------------------------------------------------------------
# FixScorer tests
# ---------------------------------------------------------------------------

class TestFixScorer:
    def test_generate_fixes(self, sample_weakness: Weakness):
        fixes = generate_fixes(sample_weakness)
        assert len(fixes) >= 1
        for f in fixes:
            assert f.weakness_id == sample_weakness.id
            assert f.label

    def test_score_fix_roi(self, sample_weakness: Weakness):
        fixes = generate_fixes(sample_weakness)
        score = score_fix_roi(fixes[0])
        assert score.expected_lift > 0
        assert score.time_to_master_hours > 0
        assert 0 < score.execution_transfer_rate <= 1.0
        assert score.roi > 0

    def test_score_fix_roi_skilled_player(self, sample_weakness: Weakness):
        fixes = generate_fixes(sample_weakness)
        low_skill = score_fix_roi(fixes[0], {"skill_level": 0.2})
        high_skill = score_fix_roi(fixes[0], {"skill_level": 0.9})
        # Higher skill = diminishing returns on expected lift
        assert high_skill.expected_lift < low_skill.expected_lift
        # Higher skill = better transfer rate
        assert high_skill.execution_transfer_rate > low_skill.execution_transfer_rate

    def test_check_execution_feasibility(self, sample_weakness: Weakness):
        fix = generate_fixes(sample_weakness)[0]
        fix.fix_score = score_fix_roi(fix)

        # High capability player
        high = check_execution_feasibility(fix, {
            "mechanical_ceiling": 0.9,
            "mental_resilience": 0.8,
            "time_available_hours": 20.0,
        })
        # Low capability player
        low = check_execution_feasibility(fix, {
            "mechanical_ceiling": 0.2,
            "mental_resilience": 0.2,
            "time_available_hours": 1.0,
        })
        assert high > low

    def test_feasibility_default(self, sample_weakness: Weakness):
        fix = generate_fixes(sample_weakness)[0]
        score = check_execution_feasibility(fix)
        assert 0 < score <= 1.0


# ---------------------------------------------------------------------------
# ImpactRank engine tests
# ---------------------------------------------------------------------------

class TestImpactRankEngine:
    def test_score_weakness(self, engine: ImpactRank, sample_weakness: Weakness):
        score = engine.score_weakness(sample_weakness)
        assert isinstance(score, ImpactScore)
        assert score.win_rate_damage >= 0

    def test_score_fix(self, engine: ImpactRank, sample_weakness: Weakness):
        fix = generate_fixes(sample_weakness)[0]
        score = engine.score_fix(fix)
        assert isinstance(score, FixScore)
        assert score.roi > 0

    def test_rank_weaknesses(self, engine: ImpactRank, sample_player_data: dict):
        rankings = engine.rank_weaknesses("player-123", "madden26", sample_player_data)
        assert len(rankings) > 0
        # Check rankings are ordered by rank
        for i, r in enumerate(rankings):
            assert r.rank == i + 1
        # Check composite scores are descending (among non-suppressed)
        active = [r for r in rankings if not r.suppressed]
        for i in range(1, len(active)):
            assert active[i - 1].composite_score >= active[i].composite_score

    def test_rank_weaknesses_empty(self, engine: ImpactRank):
        rankings = engine.rank_weaknesses("player-123", "madden26", {})
        assert rankings == []

    def test_get_top_priority(self, engine: ImpactRank, sample_player_data: dict):
        engine.rank_weaknesses("player-123", "madden26", sample_player_data)
        top = engine.get_top_priority("player-123", "madden26")
        assert top is not None
        assert top.user_id == "player-123"
        assert top.title == "madden26"
        assert top.ranking.rank == 1
        assert "priority" in top.message.lower() or top.ranking.weakness.label in top.message

    def test_get_top_priority_empty(self, engine: ImpactRank):
        top = engine.get_top_priority("player-123", "madden26")
        assert top is None

    def test_suppress_low_roi(self, engine: ImpactRank, sample_player_data: dict):
        rankings = engine.rank_weaknesses(
            "player-123", "madden26", sample_player_data, threshold=0.0
        )
        # With threshold 0, nothing should be suppressed
        assert all(not r.suppressed for r in rankings)

        # With very high threshold, everything should be suppressed
        rankings = engine.suppress_low_roi(rankings, threshold=999.0)
        assert all(r.suppressed for r in rankings)

    def test_suppress_does_not_remove(self, engine: ImpactRank):
        """Suppressed items stay in the list, just flagged."""
        from app.schemas.impact_rank import ImpactRanking

        rankings = [
            ImpactRanking(
                user_id="p1",
                weakness=Weakness(
                    title="madden26",
                    category=WeaknessCategory.DECISION,
                    label="test",
                ),
                rank=1,
                composite_score=0.001,
            ),
        ]
        result = engine.suppress_low_roi(rankings, threshold=0.01)
        assert len(result) == 1
        assert result[0].suppressed is True


# ---------------------------------------------------------------------------
# Outcome learning tests
# ---------------------------------------------------------------------------

class TestOutcomeLearning:
    def test_update_from_outcome_improved(
        self, engine: ImpactRank, sample_player_data: dict
    ):
        rankings = engine.rank_weaknesses("player-123", "madden26", sample_player_data)
        ranking = rankings[0]
        original_damage = ranking.weakness.impact_score.win_rate_damage

        result = engine.update_from_outcome(
            "player-123",
            ranking.id,
            {"verdict": "improved", "observed_lift": 0.05, "games_played": 5},
        )
        assert result is not None
        assert result.weakness.impact_score.win_rate_damage < original_damage

    def test_update_from_outcome_regressed(
        self, engine: ImpactRank, sample_player_data: dict
    ):
        rankings = engine.rank_weaknesses("player-123", "madden26", sample_player_data)
        ranking = rankings[0]
        original_confidence = ranking.weakness.impact_score.confidence

        result = engine.update_from_outcome(
            "player-123",
            ranking.id,
            {"verdict": "regressed", "observed_lift": -0.03, "games_played": 3},
        )
        assert result is not None
        assert result.weakness.impact_score.confidence < original_confidence

    def test_update_from_outcome_no_change(
        self, engine: ImpactRank, sample_player_data: dict
    ):
        rankings = engine.rank_weaknesses("player-123", "madden26", sample_player_data)
        ranking = rankings[0]
        original_confidence = ranking.weakness.impact_score.confidence

        result = engine.update_from_outcome(
            "player-123",
            ranking.id,
            {"verdict": "no_change", "games_played": 5},
        )
        assert result is not None
        # Confidence should increase slightly on no_change
        assert result.weakness.impact_score.confidence >= original_confidence

    def test_update_nonexistent_ranking(self, engine: ImpactRank):
        result = engine.update_from_outcome("player-123", uuid4(), {"verdict": "improved"})
        assert result is None


# ---------------------------------------------------------------------------
# Recalculation tests
# ---------------------------------------------------------------------------

class TestRecalculation:
    def test_recalculate(self, engine: ImpactRank, sample_player_data: dict):
        # Initial ranking
        first = engine.rank_weaknesses("player-123", "madden26", sample_player_data)
        assert len(first) > 0

        # Recalculate (should produce fresh rankings)
        second = engine.recalculate("player-123", "madden26", sample_player_data)
        assert len(second) == len(first)

        # IDs should differ (fresh calculation)
        first_ids = {r.id for r in first}
        second_ids = {r.id for r in second}
        assert first_ids != second_ids

    def test_recalculate_empty(self, engine: ImpactRank):
        result = engine.recalculate("player-123", "madden26", {})
        assert result == []


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------

class TestSchemas:
    def test_impact_score_composite(self):
        score = ImpactScore(
            win_rate_damage=0.15, frequency=0.3, severity=0.5, confidence=0.8
        )
        assert score.composite == pytest.approx(0.3 * 0.5 * 0.8)

    def test_fix_score_roi(self):
        score = FixScore(
            expected_lift=0.1, time_to_master_hours=2.0, execution_transfer_rate=0.8
        )
        assert score.roi == pytest.approx((0.1 * 0.8) / 2.0)

    def test_fix_score_roi_zero_hours(self):
        score = FixScore(
            expected_lift=0.1, time_to_master_hours=0.5, execution_transfer_rate=0.8
        )
        # Should not divide by zero (min is 0.5 via validator)
        assert score.roi > 0

    def test_weakness_category_values(self):
        assert set(WeaknessCategory) == {
            WeaknessCategory.MECHANICAL,
            WeaknessCategory.DECISION,
            WeaknessCategory.KNOWLEDGE,
            WeaknessCategory.MENTAL,
            WeaknessCategory.TACTICAL,
        }
