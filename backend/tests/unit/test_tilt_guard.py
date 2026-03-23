"""Unit tests for the TiltGuard service."""

from __future__ import annotations

import pytest

from app.schemas.mental import (
    CheckinResult,
    InterventionKind,
    TiltOrFatigue,
    TiltStatus,
    TiltType,
)
from app.services.backbone.tilt_guard import (
    TiltGuard,
    _checkin_store,
    _session_metrics_store,
    _tilt_history,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_stores():
    """Reset in-memory stores between tests."""
    _checkin_store.clear()
    _tilt_history.clear()
    _session_metrics_store.clear()
    yield
    _checkin_store.clear()
    _tilt_history.clear()
    _session_metrics_store.clear()


# ---------------------------------------------------------------------------
# Pre-session check-in
# ---------------------------------------------------------------------------

class TestPreSessionCheckin:
    """Tests for TiltGuard.pre_session_checkin."""

    def test_high_mood_energy_returns_low_risk(self):
        result = TiltGuard.pre_session_checkin("player1", mood=8.0, energy=9.0)
        assert isinstance(result, CheckinResult)
        assert result.risk_level == "low"
        assert result.user_id == "player1"

    def test_medium_mood_energy_returns_medium_risk(self):
        result = TiltGuard.pre_session_checkin("player1", mood=5.0, energy=4.0)
        assert result.risk_level == "medium"

    def test_low_mood_energy_returns_high_risk(self):
        result = TiltGuard.pre_session_checkin("player1", mood=2.0, energy=1.0)
        assert result.risk_level == "high"

    def test_checkin_is_stored(self):
        TiltGuard.pre_session_checkin("player1", mood=7.0, energy=7.0)
        assert len(_checkin_store.get("player1", [])) == 1

    def test_default_values(self):
        result = TiltGuard.pre_session_checkin("player1")
        assert result.mood_score == 5.0
        assert result.energy_score == 5.0


# ---------------------------------------------------------------------------
# Monitor performance
# ---------------------------------------------------------------------------

class TestMonitorPerformance:
    """Tests for TiltGuard.monitor_performance."""

    def test_stable_metrics_no_tilt(self):
        metrics = {
            "win_rate": 0.55,
            "baseline_win_rate": 0.55,
            "error_count": 5,
            "baseline_errors": 5,
            "decision_accuracy": 0.8,
            "baseline_decision_accuracy": 0.8,
        }
        status = TiltGuard.monitor_performance("player1", metrics)
        assert isinstance(status, TiltStatus)
        assert status.is_tilted is False

    def test_single_signal_no_tilt(self):
        metrics = {
            "win_rate": 0.40,
            "baseline_win_rate": 0.55,
            "error_count": 5,
            "baseline_errors": 5,
            "decision_accuracy": 0.8,
            "baseline_decision_accuracy": 0.8,
        }
        status = TiltGuard.monitor_performance("player1", metrics)
        assert status.is_tilted is False

    def test_multiple_signals_trigger_tilt(self):
        metrics = {
            "win_rate": 0.30,
            "baseline_win_rate": 0.55,
            "error_count": 15,
            "baseline_errors": 5,
            "decision_accuracy": 0.5,
            "baseline_decision_accuracy": 0.8,
        }
        status = TiltGuard.monitor_performance("player1", metrics)
        assert status.is_tilted is True
        assert status.severity > 0
        assert status.tilt_type is not None

    def test_tilt_event_recorded_in_history(self):
        metrics = {
            "win_rate": 0.20,
            "baseline_win_rate": 0.55,
            "error_count": 20,
            "baseline_errors": 5,
            "decision_accuracy": 0.3,
            "baseline_decision_accuracy": 0.8,
        }
        TiltGuard.monitor_performance("player1", metrics)
        history = TiltGuard.get_tilt_history("player1")
        assert len(history) == 1

    def test_error_spike_classified_as_rage(self):
        metrics = {
            "win_rate": 0.30,
            "baseline_win_rate": 0.55,
            "error_count": 20,
            "baseline_errors": 5,
            "decision_accuracy": 0.8,
            "baseline_decision_accuracy": 0.8,
        }
        status = TiltGuard.monitor_performance("player1", metrics)
        assert status.is_tilted is True
        assert status.tilt_type == TiltType.RAGE


# ---------------------------------------------------------------------------
# Tilt vs fatigue detection
# ---------------------------------------------------------------------------

class TestDetectTiltVsFatigue:
    """Tests for TiltGuard.detect_tilt_vs_fatigue."""

    def test_clean_metrics_returns_none(self):
        metrics = {
            "error_count": 5,
            "baseline_errors": 5,
            "win_rate": 0.5,
            "baseline_win_rate": 0.5,
            "reaction_time_ms": 200,
            "baseline_reaction_ms": 200,
            "decision_accuracy": 0.8,
            "baseline_decision_accuracy": 0.8,
        }
        result = TiltGuard.detect_tilt_vs_fatigue(metrics)
        assert isinstance(result, TiltOrFatigue)
        assert result.classification == "none"

    def test_tilt_signals_classify_as_tilt(self):
        metrics = {
            "error_count": 15,
            "baseline_errors": 5,
            "win_rate": 0.30,
            "baseline_win_rate": 0.55,
            "risky_play_ratio": 0.5,
            "reaction_time_ms": 200,
            "baseline_reaction_ms": 200,
        }
        result = TiltGuard.detect_tilt_vs_fatigue(metrics)
        assert result.classification == "tilt"
        assert result.tilt_probability > 0

    def test_fatigue_signals_classify_as_fatigue(self):
        metrics = {
            "error_count": 5,
            "baseline_errors": 5,
            "win_rate": 0.5,
            "baseline_win_rate": 0.5,
            "reaction_time_ms": 300,
            "baseline_reaction_ms": 200,
            "decision_accuracy": 0.5,
            "baseline_decision_accuracy": 0.8,
            "apm": 40,
            "baseline_apm": 80,
        }
        result = TiltGuard.detect_tilt_vs_fatigue(metrics)
        assert result.classification == "fatigue"
        assert result.fatigue_probability > 0

    def test_both_signals_classify_as_both(self):
        metrics = {
            "error_count": 15,
            "baseline_errors": 5,
            "win_rate": 0.30,
            "baseline_win_rate": 0.55,
            "risky_play_ratio": 0.5,
            "reaction_time_ms": 300,
            "baseline_reaction_ms": 200,
            "decision_accuracy": 0.5,
            "baseline_decision_accuracy": 0.8,
            "apm": 40,
            "baseline_apm": 80,
        }
        result = TiltGuard.detect_tilt_vs_fatigue(metrics)
        assert result.classification == "both"


# ---------------------------------------------------------------------------
# Interventions
# ---------------------------------------------------------------------------

class TestTriggerIntervention:
    """Tests for TiltGuard.trigger_intervention."""

    def test_no_tilt_returns_empty(self):
        status = TiltStatus(user_id="p1", is_tilted=False)
        interventions = TiltGuard.trigger_intervention("p1", status)
        assert interventions == []

    def test_low_severity_returns_breathing(self):
        status = TiltStatus(
            user_id="p1",
            is_tilted=True,
            severity=0.2,
            tilt_type=TiltType.FRUSTRATION,
        )
        interventions = TiltGuard.trigger_intervention("p1", status)
        assert len(interventions) >= 1
        assert interventions[0].kind == InterventionKind.BREATHING

    def test_high_severity_returns_multiple(self):
        status = TiltStatus(
            user_id="p1",
            is_tilted=True,
            severity=0.9,
            tilt_type=TiltType.RAGE,
        )
        interventions = TiltGuard.trigger_intervention("p1", status)
        assert len(interventions) >= 4
        kinds = {i.kind for i in interventions}
        assert InterventionKind.BREAK in kinds
        assert InterventionKind.SESSION_END in kinds

    def test_medium_severity_includes_mode_switch(self):
        status = TiltStatus(
            user_id="p1",
            is_tilted=True,
            severity=0.6,
            tilt_type=TiltType.ANXIETY,
        )
        interventions = TiltGuard.trigger_intervention("p1", status)
        kinds = {i.kind for i in interventions}
        assert InterventionKind.MODE_SWITCH in kinds


# ---------------------------------------------------------------------------
# Peak hours & tilt history
# ---------------------------------------------------------------------------

class TestPeakHoursAndHistory:
    """Tests for peak hours analysis and tilt history."""

    def test_no_history_returns_empty(self):
        result = TiltGuard.get_mental_peak_hours("new_player")
        assert result.user_id == "new_player"
        assert result.best_hours == []

    def test_get_tilt_history_empty(self):
        assert TiltGuard.get_tilt_history("nobody") == []

    def test_peak_hours_with_data(self):
        _session_metrics_store["p1"] = [
            {"hour_of_day": 14, "win_rate": 0.7},
            {"hour_of_day": 14, "win_rate": 0.8},
            {"hour_of_day": 22, "win_rate": 0.3},
            {"hour_of_day": 10, "win_rate": 0.6},
        ]
        result = TiltGuard.get_mental_peak_hours("p1")
        assert 14 in result.best_hours
