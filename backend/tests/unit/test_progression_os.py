"""Tests for ProgressionOS — roadmaps, phases, overload throttling, mastery."""

from __future__ import annotations

import pytest

from app.schemas.install import (
    InstallStatus,
    MasteryPhase,
    OverloadCheck,
    PhaseProgress,
    ProgressionStep,
    WeeklyRoadmap,
)
from app.services.backbone.progression_os import ProgressionOS, PHASE_ORDER


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine() -> ProgressionOS:
    """Fresh ProgressionOS engine per test."""
    return ProgressionOS()


@pytest.fixture
def sample_rankings() -> list[dict]:
    return [
        {"label": "Fix red zone reads", "description": "Improve scoring.", "composite_score": 0.9, "estimated_hours": 2.0},
        {"label": "Master hot routes", "description": "Beat blitz.", "composite_score": 0.7, "estimated_hours": 3.0},
        {"label": "Learn audibles", "description": "Adjust at line.", "composite_score": 0.5, "estimated_hours": 2.5},
    ]


# ---------------------------------------------------------------------------
# Weekly roadmap tests
# ---------------------------------------------------------------------------

class TestWeeklyRoadmap:
    def test_generate_roadmap_structure(self, engine: ProgressionOS):
        roadmap = engine.generate_weekly_roadmap("player-1", "madden26")
        assert isinstance(roadmap, WeeklyRoadmap)
        assert roadmap.user_id == "player-1"
        assert roadmap.title == "madden26"
        assert roadmap.week_number == 1
        assert roadmap.current_phase == MasteryPhase.BASE

    def test_roadmap_with_rankings(self, engine: ProgressionOS, sample_rankings: list[dict]):
        roadmap = engine.generate_weekly_roadmap("player-1", "madden26", sample_rankings)
        assert len(roadmap.steps) == 3
        assert roadmap.steps[0].label == "Fix red zone reads"
        assert roadmap.steps[0].phase == MasteryPhase.BASE

    def test_roadmap_week_increments(self, engine: ProgressionOS):
        r1 = engine.generate_weekly_roadmap("player-1", "madden26")
        r2 = engine.generate_weekly_roadmap("player-1", "madden26")
        assert r1.week_number == 1
        assert r2.week_number == 2

    def test_roadmap_default_steps_when_no_rankings(self, engine: ProgressionOS):
        roadmap = engine.generate_weekly_roadmap("player-1", "madden26")
        assert len(roadmap.steps) > 0
        for step in roadmap.steps:
            assert step.phase == MasteryPhase.BASE

    def test_roadmap_respects_current_phase(self, engine: ProgressionOS, sample_rankings: list[dict]):
        engine._phases[("player-1", "madden26")] = MasteryPhase.PRESSURE
        roadmap = engine.generate_weekly_roadmap("player-1", "madden26", sample_rankings)
        assert roadmap.current_phase == MasteryPhase.PRESSURE
        for step in roadmap.steps:
            assert step.phase == MasteryPhase.PRESSURE


# ---------------------------------------------------------------------------
# Overload throttling tests
# ---------------------------------------------------------------------------

class TestOverloadThrottling:
    def test_throttle_applied_when_over_hours(self, engine: ProgressionOS):
        # Many rankings with high hours
        big_rankings = [
            {"label": f"Step {i}", "composite_score": 0.5, "estimated_hours": 5.0}
            for i in range(10)
        ]
        roadmap = engine.generate_weekly_roadmap("player-1", "madden26", big_rankings)
        assert roadmap.is_overloaded is True
        assert roadmap.total_estimated_hours <= roadmap.max_hours_per_week

    def test_no_throttle_when_under_limit(self, engine: ProgressionOS):
        small_rankings = [
            {"label": "Quick fix", "composite_score": 0.8, "estimated_hours": 1.0}
        ]
        roadmap = engine.generate_weekly_roadmap("player-1", "madden26", small_rankings)
        assert roadmap.is_overloaded is False

    def test_throttle_always_keeps_one_step(self, engine: ProgressionOS):
        engine.configure("player-1", max_hours_per_week=0.1)
        rankings = [{"label": "Big step", "composite_score": 0.9, "estimated_hours": 5.0}]
        roadmap = engine.generate_weekly_roadmap("player-1", "madden26", rankings)
        assert len(roadmap.steps) >= 1

    def test_check_overload_not_overloaded(self, engine: ProgressionOS):
        result = engine.check_overload("player-1")
        assert isinstance(result, OverloadCheck)
        assert result.is_overloaded is False
        assert result.active_installs == 0

    def test_check_overload_too_many_installs(self, engine: ProgressionOS):
        engine.configure("player-1", max_active_installs=2)
        # Generate roadmap with 3 steps
        rankings = [
            {"label": f"Step {i}", "composite_score": 0.5, "estimated_hours": 1.0}
            for i in range(3)
        ]
        engine.generate_weekly_roadmap("player-1", "madden26", rankings)
        result = engine.check_overload("player-1")
        assert result.is_overloaded is True
        assert result.active_installs == 3
        assert "Throttle" in result.recommendation

    def test_check_overload_too_many_hours(self, engine: ProgressionOS):
        engine.configure("player-1", max_hours_per_week=2.0)
        rankings = [
            {"label": "Step 1", "composite_score": 0.9, "estimated_hours": 1.5},
            {"label": "Step 2", "composite_score": 0.8, "estimated_hours": 1.5},
        ]
        engine.generate_weekly_roadmap("player-1", "madden26", rankings)
        result = engine.check_overload("player-1")
        assert result.active_hours == 3.0
        assert result.is_overloaded is True


# ---------------------------------------------------------------------------
# Phase management tests
# ---------------------------------------------------------------------------

class TestPhaseManagement:
    def test_default_phase_is_base(self, engine: ProgressionOS):
        phase = engine.get_current_phase("player-1", "madden26")
        assert phase == MasteryPhase.BASE

    def test_advance_phase_progression(self, engine: ProgressionOS):
        assert engine.advance_phase("player-1", "madden26") == MasteryPhase.PRESSURE
        assert engine.advance_phase("player-1", "madden26") == MasteryPhase.ANTI_META
        assert engine.advance_phase("player-1", "madden26") == MasteryPhase.TOURNAMENT

    def test_advance_phase_caps_at_tournament(self, engine: ProgressionOS):
        engine._phases[("player-1", "madden26")] = MasteryPhase.TOURNAMENT
        result = engine.advance_phase("player-1", "madden26")
        assert result == MasteryPhase.TOURNAMENT

    def test_phase_order_is_correct(self):
        assert PHASE_ORDER == [
            MasteryPhase.BASE,
            MasteryPhase.PRESSURE,
            MasteryPhase.ANTI_META,
            MasteryPhase.TOURNAMENT,
        ]

    def test_get_current_phase_after_advance(self, engine: ProgressionOS):
        engine.advance_phase("player-1", "madden26")
        assert engine.get_current_phase("player-1", "madden26") == MasteryPhase.PRESSURE


# ---------------------------------------------------------------------------
# Next steps tests
# ---------------------------------------------------------------------------

class TestNextSteps:
    def test_get_next_steps_returns_pending(self, engine: ProgressionOS, sample_rankings: list[dict]):
        engine.generate_weekly_roadmap("player-1", "madden26", sample_rankings)
        steps = engine.get_next_steps("player-1", "madden26")
        assert len(steps) == 3
        for step in steps:
            assert step.status == InstallStatus.PENDING

    def test_get_next_steps_respects_count(self, engine: ProgressionOS, sample_rankings: list[dict]):
        engine.generate_weekly_roadmap("player-1", "madden26", sample_rankings)
        steps = engine.get_next_steps("player-1", "madden26", count=1)
        assert len(steps) == 1

    def test_get_next_steps_sorted_by_impact(self, engine: ProgressionOS, sample_rankings: list[dict]):
        engine.generate_weekly_roadmap("player-1", "madden26", sample_rankings)
        steps = engine.get_next_steps("player-1", "madden26")
        scores = [s.impact_rank_score for s in steps]
        assert scores == sorted(scores, reverse=True)

    def test_get_next_steps_empty_when_no_roadmap(self, engine: ProgressionOS):
        steps = engine.get_next_steps("player-1", "madden26")
        assert steps == []

    def test_get_next_steps_filters_by_current_phase(self, engine: ProgressionOS, sample_rankings: list[dict]):
        engine.generate_weekly_roadmap("player-1", "madden26", sample_rankings)
        # Advance to PRESSURE — BASE steps should not appear
        engine.advance_phase("player-1", "madden26")
        steps = engine.get_next_steps("player-1", "madden26")
        # No PRESSURE steps were generated yet, so should be empty
        assert len(steps) == 0


# ---------------------------------------------------------------------------
# Mastery progress tests
# ---------------------------------------------------------------------------

class TestMasteryProgress:
    def test_progress_all_phases_returned(self, engine: ProgressionOS):
        progress = engine.get_mastery_progress("player-1", "madden26")
        assert len(progress) == 4
        phases = [p.phase for p in progress]
        assert phases == PHASE_ORDER

    def test_progress_base_is_current_by_default(self, engine: ProgressionOS):
        progress = engine.get_mastery_progress("player-1", "madden26")
        base = progress[0]
        assert base.is_current is True
        assert base.is_unlocked is True
        # Later phases not unlocked
        assert progress[1].is_unlocked is False
        assert progress[1].is_current is False

    def test_progress_tracks_mastery_pct(self, engine: ProgressionOS, sample_rankings: list[dict]):
        engine.generate_weekly_roadmap("player-1", "madden26", sample_rankings)
        # Mark one step as mastered
        steps = engine._steps[("player-1", "madden26")]
        steps[0].status = InstallStatus.MASTERED

        progress = engine.get_mastery_progress("player-1", "madden26")
        base = progress[0]
        assert base.total_steps == 3
        assert base.completed_steps == 1
        assert base.mastery_pct == pytest.approx(33.3, abs=0.1)

    def test_progress_unlocked_after_advance(self, engine: ProgressionOS):
        engine.advance_phase("player-1", "madden26")
        progress = engine.get_mastery_progress("player-1", "madden26")
        # BASE and PRESSURE should both be unlocked
        assert progress[0].is_unlocked is True
        assert progress[1].is_unlocked is True
        assert progress[1].is_current is True
        assert progress[2].is_unlocked is False


# ---------------------------------------------------------------------------
# Configuration tests
# ---------------------------------------------------------------------------

class TestConfiguration:
    def test_configure_max_hours(self, engine: ProgressionOS):
        engine.configure("player-1", max_hours_per_week=5.0)
        assert engine._config["player-1"]["max_hours_per_week"] == 5.0

    def test_configure_max_installs(self, engine: ProgressionOS):
        engine.configure("player-1", max_active_installs=3)
        assert engine._config["player-1"]["max_active_installs"] == 3

    def test_configure_partial_update(self, engine: ProgressionOS):
        engine.configure("player-1", max_hours_per_week=5.0)
        engine.configure("player-1", max_active_installs=3)
        assert engine._config["player-1"]["max_hours_per_week"] == 5.0
        assert engine._config["player-1"]["max_active_installs"] == 3
