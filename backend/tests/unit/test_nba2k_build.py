"""Tests for BuildForge — meta analysis, badge optimization, attribute thresholds, comparison."""

from __future__ import annotations

import pytest

from app.schemas.nba2k26.builds import (
    Archetype,
    BadgeCategory,
    BadgeTier,
    Build,
    BuildAttributes,
    MetaTier,
    Position,
)
from app.services.agents.nba2k26.build_forge import BuildForge


@pytest.fixture
def engine() -> BuildForge:
    """Fresh BuildForge instance per test."""
    return BuildForge()


def _make_build(**overrides) -> Build:
    """Helper to build a Build with sensible defaults."""
    defaults = {
        "name": "Test Build",
        "position": Position.SG,
        "archetype": Archetype.TWO_WAY,
        "height_inches": 78,
        "weight_lbs": 200,
        "wingspan_inches": 82,
        "overall_rating": 90,
        "attributes": BuildAttributes(
            close_shot=80, driving_layup=85, driving_dunk=88,
            three_point_shot=78, mid_range_shot=80, ball_handle=82,
            speed_with_ball=84, perimeter_defense=88, steal=85,
            speed=90, acceleration=88, vertical=85, stamina=88,
            pass_accuracy=75, interior_defense=70, block=72,
            offensive_rebound=50, defensive_rebound=65,
            standing_dunk=60, free_throw=75, strength=70,
        ),
    }
    defaults.update(overrides)
    return Build(**defaults)


# ---------------------------------------------------------------------------
# Build analysis
# ---------------------------------------------------------------------------

class TestAnalyzeBuild:
    """Tests for analyze_build."""

    def test_returns_analysis_result(self, engine: BuildForge) -> None:
        build = _make_build()
        result = engine.analyze_build(build)
        assert result.build.name == "Test Build"
        assert result.meta_tier is not None
        assert result.badge_allocation is not None
        assert result.attribute_thresholds is not None

    def test_high_attribute_build_gets_high_tier(self, engine: BuildForge) -> None:
        build = _make_build(
            attributes=BuildAttributes(
                three_point_shot=92, ball_handle=90, speed=95,
                perimeter_defense=92, driving_dunk=90, mid_range_shot=88,
                driving_layup=85, close_shot=80, speed_with_ball=90,
                steal=88, acceleration=92, vertical=88, stamina=90,
            ),
        )
        result = engine.analyze_build(build)
        assert result.meta_tier in (MetaTier.S_TIER, MetaTier.A_TIER)

    def test_low_attribute_build_gets_low_tier(self, engine: BuildForge) -> None:
        build = _make_build(
            overall_rating=65,
            attributes=BuildAttributes(
                three_point_shot=50, ball_handle=55, speed=60,
                perimeter_defense=50, driving_dunk=55, mid_range_shot=50,
            ),
        )
        result = engine.analyze_build(build)
        assert result.meta_tier in (MetaTier.C_TIER, MetaTier.D_TIER)

    def test_optimization_tips_not_empty(self, engine: BuildForge) -> None:
        build = _make_build()
        result = engine.analyze_build(build)
        assert len(result.optimization_tips) > 0


# ---------------------------------------------------------------------------
# Badge optimization
# ---------------------------------------------------------------------------

class TestOptimizeBadges:
    """Tests for optimize_badges."""

    def test_badges_allocated_based_on_attributes(self, engine: BuildForge) -> None:
        build = _make_build()
        alloc = engine.optimize_badges(build)
        assert alloc.build_id == build.id
        assert alloc.total_badge_points_used > 0

    def test_high_dunk_gets_posterizer(self, engine: BuildForge) -> None:
        build = _make_build(
            attributes=BuildAttributes(driving_dunk=92, driving_layup=85),
        )
        alloc = engine.optimize_badges(build)
        finishing_names = [b.name for b in alloc.finishing_badges]
        assert "Posterizer" in finishing_names

    def test_high_three_gets_limitless(self, engine: BuildForge) -> None:
        build = _make_build(
            attributes=BuildAttributes(three_point_shot=88),
        )
        alloc = engine.optimize_badges(build)
        shooting_names = [b.name for b in alloc.shooting_badges]
        assert "Limitless Range" in shooting_names

    def test_high_perimeter_gets_clamps(self, engine: BuildForge) -> None:
        build = _make_build(
            attributes=BuildAttributes(perimeter_defense=90),
        )
        alloc = engine.optimize_badges(build)
        defense_names = [b.name for b in alloc.defense_badges]
        assert "Clamps" in defense_names

    def test_badge_tier_scales_with_attribute(self, engine: BuildForge) -> None:
        build_low = _make_build(attributes=BuildAttributes(driving_dunk=84))
        build_high = _make_build(attributes=BuildAttributes(driving_dunk=92))
        alloc_low = engine.optimize_badges(build_low)
        alloc_high = engine.optimize_badges(build_high)
        # Higher dunk should get gold posterizer vs silver
        low_poster = [b for b in alloc_low.finishing_badges if b.name == "Posterizer"]
        high_poster = [b for b in alloc_high.finishing_badges if b.name == "Posterizer"]
        assert low_poster and high_poster
        assert high_poster[0].tier.value >= low_poster[0].tier.value


# ---------------------------------------------------------------------------
# Attribute thresholds
# ---------------------------------------------------------------------------

class TestAttributeThresholds:
    """Tests for get_attribute_thresholds."""

    def test_returns_thresholds_sorted_by_priority(self, engine: BuildForge) -> None:
        build = _make_build(
            attributes=BuildAttributes(ball_handle=78, driving_dunk=82, three_point_shot=74),
        )
        thresholds = engine.get_attribute_thresholds(build)
        assert len(thresholds) > 0
        # Should be sorted descending by priority
        for i in range(len(thresholds) - 1):
            assert thresholds[i].priority >= thresholds[i + 1].priority

    def test_near_threshold_gets_high_priority(self, engine: BuildForge) -> None:
        build = _make_build(attributes=BuildAttributes(ball_handle=79))
        thresholds = engine.get_attribute_thresholds(build)
        bh_thresholds = [t for t in thresholds if t.attribute_name == "ball_handle"]
        assert len(bh_thresholds) > 0
        assert bh_thresholds[0].next_threshold == 80
        assert bh_thresholds[0].priority > 0.5

    def test_maxed_attribute_has_no_threshold(self, engine: BuildForge) -> None:
        build = _make_build(attributes=BuildAttributes(ball_handle=99))
        thresholds = engine.get_attribute_thresholds(build)
        bh_thresholds = [t for t in thresholds if t.attribute_name == "ball_handle"]
        assert len(bh_thresholds) == 0


# ---------------------------------------------------------------------------
# Build comparison
# ---------------------------------------------------------------------------

class TestCompareBuild:
    """Tests for compare_builds."""

    def test_comparison_identifies_advantages(self, engine: BuildForge) -> None:
        build_a = _make_build(name="Slasher", attributes=BuildAttributes(driving_dunk=95, three_point_shot=60))
        build_b = _make_build(name="Shooter", attributes=BuildAttributes(driving_dunk=60, three_point_shot=95))
        result = engine.compare_builds(build_a, build_b)
        assert "driving_dunk" in result.attribute_advantages_a
        assert "three_point_shot" in result.attribute_advantages_b

    def test_equal_builds_are_even(self, engine: BuildForge) -> None:
        build = _make_build()
        result = engine.compare_builds(build, build)
        assert result.matchup_prediction == "Even matchup"
        assert len(result.attribute_advantages_a) == 0
        assert len(result.attribute_advantages_b) == 0


# ---------------------------------------------------------------------------
# Meta builds
# ---------------------------------------------------------------------------

class TestMetaBuilds:
    """Tests for meta build retrieval."""

    def test_get_all_meta_builds(self, engine: BuildForge) -> None:
        builds = engine.get_meta_builds()
        assert len(builds) >= 3

    def test_filter_by_position(self, engine: BuildForge) -> None:
        builds = engine.get_meta_builds(position=Position.PG)
        for b in builds:
            assert b.position == Position.PG

    def test_filter_by_tier(self, engine: BuildForge) -> None:
        builds = engine.get_meta_builds(tier=MetaTier.S_TIER)
        for b in builds:
            assert b.meta_tier == MetaTier.S_TIER

    def test_counter_builds_returns_results(self, engine: BuildForge) -> None:
        counters = engine.get_counter_builds(Archetype.SLASHER)
        assert len(counters) > 0
