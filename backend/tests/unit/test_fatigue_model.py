"""Unit tests for the Predictive Fatigue Model service."""

from __future__ import annotations

import pytest

from app.schemas.mental import (
    DeclineReport,
    FatigueLevel,
    SessionRecommendation,
    TournamentDayPlan,
)
from app.services.backbone.fatigue_model import FatigueModel, _session_history


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_stores():
    """Reset in-memory stores between tests."""
    _session_history.clear()
    yield
    _session_history.clear()


# ---------------------------------------------------------------------------
# Fatigue prediction
# ---------------------------------------------------------------------------

class TestPredictFatigue:
    """Tests for FatigueModel.predict_fatigue."""

    def test_short_session_returns_fresh(self):
        level = FatigueModel.predict_fatigue("p1", session_length_minutes=5, time_of_day=12)
        assert level == FatigueLevel.FRESH

    def test_long_session_returns_high_fatigue(self):
        level = FatigueModel.predict_fatigue("p1", session_length_minutes=300, time_of_day=12)
        assert level in (FatigueLevel.SEVERE, FatigueLevel.CRITICAL)

    def test_late_night_increases_fatigue(self):
        level_day = FatigueModel.predict_fatigue("p1", session_length_minutes=90, time_of_day=12)
        level_night = FatigueModel.predict_fatigue("p1", session_length_minutes=90, time_of_day=2)
        assert level_night.value >= level_day.value or level_night != FatigueLevel.FRESH

    def test_personal_history_affects_prediction(self):
        _session_history["p1"] = [
            {"decline_at_minutes": 45},
            {"decline_at_minutes": 50},
        ]
        # With a low personal decline point, even moderate sessions should fatigue
        level = FatigueModel.predict_fatigue("p1", session_length_minutes=60, time_of_day=12)
        assert level != FatigueLevel.FRESH


# ---------------------------------------------------------------------------
# Optimal session length
# ---------------------------------------------------------------------------

class TestGetOptimalSessionLength:
    """Tests for FatigueModel.get_optimal_session_length."""

    def test_no_history_returns_defaults(self):
        rec = FatigueModel.get_optimal_session_length("new_player")
        assert isinstance(rec, SessionRecommendation)
        assert rec.optimal_minutes == 90
        assert rec.max_before_decline == 150

    def test_with_history_personalises(self):
        _session_history["p1"] = [
            {"decline_at_minutes": 60},
            {"decline_at_minutes": 80},
            {"decline_at_minutes": 70},
        ]
        rec = FatigueModel.get_optimal_session_length("p1")
        # Average decline is ~70, optimal should be 80% of that = 56
        assert rec.optimal_minutes < 70
        assert rec.max_before_decline <= 70
        assert "3 sessions" in rec.reasoning

    def test_break_interval_is_reasonable(self):
        _session_history["p1"] = [{"decline_at_minutes": 120}]
        rec = FatigueModel.get_optimal_session_length("p1")
        assert rec.suggested_break_interval >= 15


# ---------------------------------------------------------------------------
# Tournament-day planning
# ---------------------------------------------------------------------------

class TestModelTournamentDay:
    """Tests for FatigueModel.model_tournament_day."""

    def test_basic_schedule(self):
        schedule = [
            {"start_hour": 10, "duration_minutes": 60, "label": "Match 1"},
            {"start_hour": 14, "duration_minutes": 60, "label": "Match 2"},
        ]
        plan = FatigueModel.model_tournament_day("p1", schedule)
        assert isinstance(plan, TournamentDayPlan)
        assert len(plan.peak_windows) == 2
        assert plan.total_play_minutes == 120

    def test_rest_windows_between_matches(self):
        schedule = [
            {"start_hour": 10, "duration_minutes": 60, "label": "Match 1"},
            {"start_hour": 14, "duration_minutes": 60, "label": "Match 2"},
        ]
        plan = FatigueModel.model_tournament_day("p1", schedule)
        assert len(plan.rest_windows) >= 1

    def test_warmup_plan_populated(self):
        plan = FatigueModel.model_tournament_day("p1", [
            {"start_hour": 12, "duration_minutes": 45, "label": "Finals"},
        ])
        assert plan.warmup_plan != ""

    def test_empty_schedule(self):
        plan = FatigueModel.model_tournament_day("p1", [])
        assert plan.total_play_minutes == 0
        assert plan.peak_windows == []


# ---------------------------------------------------------------------------
# Cognitive decline detection
# ---------------------------------------------------------------------------

class TestDetectCognitiveDecline:
    """Tests for FatigueModel.detect_cognitive_decline."""

    def test_stable_metrics_no_decline(self):
        metrics = {
            "reaction_time_ms": 200,
            "baseline_reaction_ms": 200,
            "error_rate": 0.05,
            "baseline_error_rate": 0.05,
            "session_elapsed_minutes": 30,
        }
        report = FatigueModel.detect_cognitive_decline(metrics)
        assert isinstance(report, DeclineReport)
        assert report.is_declining is False

    def test_slow_reactions_trigger_decline(self):
        metrics = {
            "reaction_time_ms": 300,
            "baseline_reaction_ms": 200,
            "error_rate": 0.05,
            "baseline_error_rate": 0.05,
            "session_elapsed_minutes": 60,
        }
        report = FatigueModel.detect_cognitive_decline(metrics)
        assert report.is_declining is True
        assert "reaction_time" in report.affected_metrics

    def test_high_error_rate_triggers_decline(self):
        metrics = {
            "reaction_time_ms": 200,
            "baseline_reaction_ms": 200,
            "error_rate": 0.20,
            "baseline_error_rate": 0.05,
            "session_elapsed_minutes": 45,
        }
        report = FatigueModel.detect_cognitive_decline(metrics)
        assert report.is_declining is True
        assert "error_rate" in report.affected_metrics

    def test_both_metrics_declining(self):
        metrics = {
            "reaction_time_ms": 350,
            "baseline_reaction_ms": 200,
            "error_rate": 0.25,
            "baseline_error_rate": 0.05,
            "session_elapsed_minutes": 90,
        }
        report = FatigueModel.detect_cognitive_decline(metrics)
        assert report.is_declining is True
        assert len(report.affected_metrics) == 2
        assert report.decline_rate > 0

    def test_minutes_until_critical_estimated(self):
        metrics = {
            "reaction_time_ms": 260,
            "baseline_reaction_ms": 200,
            "error_rate": 0.05,
            "baseline_error_rate": 0.05,
            "session_elapsed_minutes": 60,
        }
        report = FatigueModel.detect_cognitive_decline(metrics)
        assert report.is_declining is True
        assert report.minutes_until_critical is not None
        assert report.minutes_until_critical > 0


# ---------------------------------------------------------------------------
# Session recording
# ---------------------------------------------------------------------------

class TestRecordSession:
    """Tests for FatigueModel.record_session."""

    def test_record_and_retrieve(self):
        FatigueModel.record_session("p1", {"decline_at_minutes": 75})
        assert len(_session_history["p1"]) == 1

    def test_multiple_records(self):
        FatigueModel.record_session("p1", {"decline_at_minutes": 60})
        FatigueModel.record_session("p1", {"decline_at_minutes": 80})
        assert len(_session_history["p1"]) == 2
