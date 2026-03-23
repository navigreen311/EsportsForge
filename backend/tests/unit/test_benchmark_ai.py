"""Unit tests for the BenchmarkAI service."""

from __future__ import annotations

import pytest

from app.schemas.mental import DimensionScores, StandoutSkill
from app.services.backbone import benchmark_ai


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_state():
    """Reset in-memory stores before each test."""
    benchmark_ai._reset()
    yield
    benchmark_ai._reset()


def _seed_snapshot(user_id: str, title: str, **scores):
    """Record a dimension snapshot with the given scores."""
    defaults = {
        "read_speed": 0.5,
        "user_defense": 0.5,
        "clutch": 0.5,
        "anti_meta": 0.5,
        "execution": 0.5,
        "mental": 0.5,
    }
    defaults.update(scores)
    return benchmark_ai.record_dimension_snapshot(user_id, title, defaults)


# ===========================================================================
# get_dimension_scores
# ===========================================================================


class TestGetDimensionScores:
    def test_no_data_returns_defaults(self):
        result = benchmark_ai.get_dimension_scores("u1", "madden26")
        assert result.read_speed == 0.5
        assert result.user_defense == 0.5
        assert result.computed_at is not None

    def test_returns_latest_snapshot(self):
        _seed_snapshot("u1", "madden26", read_speed=0.6)
        _seed_snapshot("u1", "madden26", read_speed=0.8)
        result = benchmark_ai.get_dimension_scores("u1", "madden26")
        assert result.read_speed == 0.8

    def test_title_isolation(self):
        _seed_snapshot("u1", "madden26", execution=0.9)
        _seed_snapshot("u1", "fc25", execution=0.3)
        m = benchmark_ai.get_dimension_scores("u1", "madden26")
        f = benchmark_ai.get_dimension_scores("u1", "fc25")
        assert m.execution == 0.9
        assert f.execution == 0.3


# ===========================================================================
# compare_to_percentile
# ===========================================================================


class TestCompareToPercentile:
    def test_default_comparison(self):
        _seed_snapshot("u1", "madden26", read_speed=0.7, clutch=0.8)
        result = benchmark_ai.compare_to_percentile("u1", "madden26")
        assert result.target_percentile == 95
        assert isinstance(result.dimensions, dict)
        assert isinstance(result.gaps, dict)
        assert len(result.summary) > 0

    def test_high_scores_small_gaps(self):
        _seed_snapshot("u1", "madden26",
                       read_speed=0.9, user_defense=0.9, clutch=0.9,
                       anti_meta=0.9, execution=0.9, mental=0.9)
        result = benchmark_ai.compare_to_percentile("u1", "madden26", percentile=50)
        # All gaps should be zero or negative (player exceeds target)
        for dim, gap in result.gaps.items():
            assert gap <= 0.01, f"{dim} gap should be <= 0 for high-scoring player"

    def test_low_scores_large_gaps(self):
        _seed_snapshot("u1", "madden26",
                       read_speed=0.1, user_defense=0.1, clutch=0.1,
                       anti_meta=0.1, execution=0.1, mental=0.1)
        result = benchmark_ai.compare_to_percentile("u1", "madden26", percentile=95)
        for dim, gap in result.gaps.items():
            assert gap > 0, f"{dim} gap should be positive for low-scoring player"

    def test_custom_percentile(self):
        _seed_snapshot("u1", "madden26")
        result = benchmark_ai.compare_to_percentile("u1", "madden26", percentile=50)
        assert result.target_percentile == 50


# ===========================================================================
# identify_standout_skills
# ===========================================================================


class TestIdentifyStandoutSkills:
    def test_no_standouts_at_baseline(self):
        # Default 0.5 scores are below the 0.6 threshold
        result = benchmark_ai.identify_standout_skills("u1", "madden26")
        assert len(result.standout_skills) == 0
        assert result.top_skill == ""

    def test_identifies_standouts(self):
        _seed_snapshot("u1", "madden26",
                       read_speed=0.85, clutch=0.75, execution=0.4)
        result = benchmark_ai.identify_standout_skills("u1", "madden26")
        dims = [s.dimension for s in result.standout_skills]
        assert "read_speed" in dims
        assert "clutch" in dims
        assert "execution" not in dims
        assert result.top_skill == "read_speed"

    def test_standouts_sorted_by_score(self):
        _seed_snapshot("u1", "madden26",
                       read_speed=0.7, clutch=0.9, mental=0.8)
        result = benchmark_ai.identify_standout_skills("u1", "madden26")
        scores = [s.score for s in result.standout_skills]
        assert scores == sorted(scores, reverse=True)


# ===========================================================================
# get_improvement_velocity
# ===========================================================================


class TestGetImprovementVelocity:
    def test_no_data(self):
        result = benchmark_ai.get_improvement_velocity("u1", "madden26")
        assert result.velocity_7d == 0.0
        assert result.velocity_30d == 0.0
        assert result.velocity_90d == 0.0

    def test_single_snapshot_no_velocity(self):
        _seed_snapshot("u1", "madden26")
        result = benchmark_ai.get_improvement_velocity("u1", "madden26")
        assert result.velocity_7d == 0.0

    def test_improving_positive_velocity(self):
        _seed_snapshot("u1", "madden26", read_speed=0.3, clutch=0.3)
        _seed_snapshot("u1", "madden26", read_speed=0.5, clutch=0.5)
        _seed_snapshot("u1", "madden26", read_speed=0.7, clutch=0.7)
        result = benchmark_ai.get_improvement_velocity("u1", "madden26")
        assert result.velocity_7d > 0

    def test_declining_negative_velocity(self):
        _seed_snapshot("u1", "madden26", read_speed=0.8, execution=0.8)
        _seed_snapshot("u1", "madden26", read_speed=0.5, execution=0.5)
        _seed_snapshot("u1", "madden26", read_speed=0.3, execution=0.3)
        result = benchmark_ai.get_improvement_velocity("u1", "madden26")
        assert result.velocity_7d < 0

    def test_identifies_fastest_improving(self):
        _seed_snapshot("u1", "madden26", read_speed=0.3, clutch=0.3)
        _seed_snapshot("u1", "madden26", read_speed=0.9, clutch=0.4)
        result = benchmark_ai.get_improvement_velocity("u1", "madden26")
        assert result.fastest_improving == "read_speed"
