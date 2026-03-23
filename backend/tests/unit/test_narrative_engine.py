"""Unit tests for the Cross-Session Narrative Engine."""

from __future__ import annotations

import pytest

from app.schemas.mental import (
    MilestoneCategory,
    MomentumDirection,
)
from app.services.backbone import benchmark_ai, confidence_tracker, narrative_engine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_state():
    """Reset all in-memory stores before each test."""
    narrative_engine._reset()
    confidence_tracker._reset()
    benchmark_ai._reset()
    yield
    narrative_engine._reset()
    confidence_tracker._reset()
    benchmark_ai._reset()


# ===========================================================================
# generate_weekly_narrative
# ===========================================================================


class TestGenerateWeeklyNarrative:
    def test_no_data(self):
        result = narrative_engine.generate_weekly_narrative("u1", "madden26")
        assert "No data" in result.narrative
        assert result.user_id == "u1"

    def test_winning_week(self):
        narrative_engine.record_weekly_snapshot("u1", "madden26", {
            "wins": 8,
            "losses": 2,
            "best_moment": "Clutch TD in overtime",
            "improvements": ["read_speed"],
            "declines": [],
        })
        result = narrative_engine.generate_weekly_narrative("u1", "madden26")
        assert "80%" in result.narrative
        assert len(result.highlights) > 0
        assert result.key_stats["wins"] == 8

    def test_losing_week(self):
        narrative_engine.record_weekly_snapshot("u1", "madden26", {
            "wins": 2,
            "losses": 8,
            "best_moment": "",
            "worst_moment": "Blown 14-point lead",
            "improvements": [],
            "declines": ["execution", "mental"],
        })
        result = narrative_engine.generate_weekly_narrative("u1", "madden26")
        assert "learning" in result.narrative.lower() or "tough" in result.narrative.lower()
        assert len(result.lowlights) > 0

    def test_highlights_include_improvements(self):
        narrative_engine.record_weekly_snapshot("u1", "madden26", {
            "wins": 5,
            "losses": 5,
            "improvements": ["clutch", "read_speed"],
            "declines": [],
        })
        result = narrative_engine.generate_weekly_narrative("u1", "madden26")
        assert any("clutch" in h for h in result.highlights)


# ===========================================================================
# detect_milestones
# ===========================================================================


class TestDetectMilestones:
    def test_no_data_no_milestones(self):
        result = narrative_engine.detect_milestones("u1")
        assert result == []

    def test_win_streak_milestone(self):
        for _ in range(5):
            confidence_tracker.record_game("u1", {
                "title": "madden26", "won": True,
                "clutch": False, "close_game": False, "comeback": False,
            })
        milestones = narrative_engine.detect_milestones("u1")
        titles = [m.title for m in milestones]
        assert "3-game win streak" in titles
        assert "5-game win streak" in titles

    def test_game_count_milestone(self):
        for _ in range(10):
            confidence_tracker.record_game("u1", {
                "title": "madden26", "won": True,
                "clutch": False, "close_game": False, "comeback": False,
            })
        milestones = narrative_engine.detect_milestones("u1")
        titles = [m.title for m in milestones]
        assert "10 games played" in titles

    def test_no_duplicate_milestones(self):
        for _ in range(5):
            confidence_tracker.record_game("u1", {
                "title": "madden26", "won": True,
                "clutch": False, "close_game": False, "comeback": False,
            })
        first = narrative_engine.detect_milestones("u1")
        second = narrative_engine.detect_milestones("u1")
        # Second call should return no new milestones
        assert len(second) == 0

    def test_percentile_milestone(self):
        benchmark_ai.record_dimension_snapshot("u1", "madden26", {
            "read_speed": 0.95,
            "user_defense": 0.5,
            "clutch": 0.5,
            "anti_meta": 0.5,
            "execution": 0.5,
            "mental": 0.5,
        })
        # Need at least one game so title is discovered
        confidence_tracker.record_game("u1", {
            "title": "madden26", "won": True,
            "clutch": False, "close_game": False, "comeback": False,
        })
        milestones = narrative_engine.detect_milestones("u1")
        categories = [m.category for m in milestones]
        assert MilestoneCategory.PERCENTILE in categories or MilestoneCategory.STREAK in categories


# ===========================================================================
# get_growth_trajectory
# ===========================================================================


class TestGetGrowthTrajectory:
    def test_no_data(self):
        result = narrative_engine.get_growth_trajectory("u1", "madden26", weeks=4)
        assert result.weeks == 4
        assert result.overall_direction == MomentumDirection.STABLE
        assert result.trends == {}

    def test_rising_trajectory(self):
        for val in [0.3, 0.4, 0.5, 0.6]:
            narrative_engine.record_metric_snapshot("u1", "madden26", {
                "win_rate": val,
                "execution": val,
            })
        result = narrative_engine.get_growth_trajectory("u1", "madden26", weeks=4)
        assert result.overall_direction == MomentumDirection.RISING
        assert "win_rate" in result.trends
        assert len(result.trends["win_rate"]) == 4

    def test_falling_trajectory(self):
        for val in [0.8, 0.6, 0.4, 0.2]:
            narrative_engine.record_metric_snapshot("u1", "madden26", {
                "win_rate": val,
            })
        result = narrative_engine.get_growth_trajectory("u1", "madden26", weeks=4)
        assert result.overall_direction == MomentumDirection.FALLING

    def test_stable_trajectory(self):
        for val in [0.5, 0.5, 0.5, 0.5]:
            narrative_engine.record_metric_snapshot("u1", "madden26", {
                "win_rate": val,
            })
        result = narrative_engine.get_growth_trajectory("u1", "madden26", weeks=4)
        assert result.overall_direction == MomentumDirection.STABLE

    def test_respects_weeks_parameter(self):
        for val in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]:
            narrative_engine.record_metric_snapshot("u1", "madden26", {
                "win_rate": val,
            })
        result = narrative_engine.get_growth_trajectory("u1", "madden26", weeks=3)
        assert result.weeks == 3
        assert len(result.trends["win_rate"]) == 3


# ===========================================================================
# generate_session_summary
# ===========================================================================


class TestGenerateSessionSummary:
    def test_no_data(self):
        result = narrative_engine.generate_session_summary("u1", "sess-1")
        assert "No session data" in result.narrative

    def test_winning_session(self):
        narrative_engine.record_session_data("u1", "sess-1", {
            "wins": 4,
            "losses": 1,
            "best_play": "Intercepted a deep pass on 4th down",
            "key_moments": ["Overtime win", "Perfect drive"],
            "improvements": ["coverage reads"],
            "areas_to_work_on": ["red zone offense"],
        })
        result = narrative_engine.generate_session_summary("u1", "sess-1")
        assert "4W-1L" in result.narrative
        assert result.performance_rating == 0.8
        assert "coverage reads" in result.improvements
        assert len(result.key_moments) == 2

    def test_losing_session(self):
        narrative_engine.record_session_data("u1", "sess-2", {
            "wins": 1,
            "losses": 4,
            "key_moments": [],
            "improvements": [],
            "areas_to_work_on": ["everything"],
        })
        result = narrative_engine.generate_session_summary("u1", "sess-2")
        assert "Challenging" in result.narrative
        assert result.performance_rating == 0.2

    def test_session_id_preserved(self):
        narrative_engine.record_session_data("u1", "my-session", {"wins": 1, "losses": 0})
        result = narrative_engine.generate_session_summary("u1", "my-session")
        assert result.session_id == "my-session"
