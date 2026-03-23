"""Unit tests for the Truth Engine, Accuracy Tracker, and Rollback Manager."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.schemas.truth_engine import (
    AccuracyFilters,
    DegradationSeverity,
    OutcomeVerdict,
    PredictionContext,
)
from app.services.backbone.accuracy_tracker import AccuracyTracker
from app.services.backbone.rollback_manager import RollbackManager
from app.services.backbone.truth_engine import TruthEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_context(title: str = "madden26", **kwargs) -> PredictionContext:
    return PredictionContext(title=title, **kwargs)


def _seed_predictions(
    tracker: AccuracyTracker,
    agent: str = "play_caller",
    count: int = 10,
    correct_ratio: float = 0.8,
    title: str = "madden26",
    confidence: float = 0.9,
):
    """Seed *count* predictions with the given correct ratio."""
    correct_count = int(count * correct_ratio)
    records = []
    for i in range(count):
        ctx = _make_context(title=title, mode="h2h", situation_type="play_call")
        rec = tracker.track_prediction(
            agent=agent,
            prediction={"play": f"play_{i}"},
            confidence=confidence,
            context=ctx,
        )
        is_correct = i < correct_count
        outcome = {"play": f"play_{i}"} if is_correct else {"play": "other"}
        tracker.record_outcome(rec.id, outcome)
        records.append(rec)
    return records


# ===========================================================================
# AccuracyTracker tests
# ===========================================================================


class TestAccuracyTracker:
    def test_track_and_record_outcome(self):
        tracker = AccuracyTracker()
        ctx = _make_context()
        rec = tracker.track_prediction("agent_a", {"pick": "X"}, 0.85, ctx)
        assert rec.verdict is None
        assert rec.outcome is None

        updated = tracker.record_outcome(rec.id, {"pick": "X"})
        assert updated.verdict == OutcomeVerdict.CORRECT
        assert updated.outcome == {"pick": "X"}

    def test_record_outcome_incorrect(self):
        tracker = AccuracyTracker()
        ctx = _make_context()
        rec = tracker.track_prediction("agent_a", {"pick": "X"}, 0.85, ctx)
        updated = tracker.record_outcome(rec.id, {"pick": "Y"})
        assert updated.verdict == OutcomeVerdict.INCORRECT

    def test_record_outcome_partial(self):
        tracker = AccuracyTracker()
        ctx = _make_context()
        rec = tracker.track_prediction(
            "agent_a", {"pick": "X", "confidence_tier": "high"}, 0.85, ctx
        )
        updated = tracker.record_outcome(
            rec.id, {"pick": "X", "confidence_tier": "low"}
        )
        assert updated.verdict == OutcomeVerdict.PARTIALLY_CORRECT

    def test_record_outcome_explicit_verdict(self):
        tracker = AccuracyTracker()
        ctx = _make_context()
        rec = tracker.track_prediction("agent_a", {"pick": "X"}, 0.85, ctx)
        updated = tracker.record_outcome(
            rec.id, {"pick": "Z"}, verdict=OutcomeVerdict.CORRECT
        )
        assert updated.verdict == OutcomeVerdict.CORRECT

    def test_record_outcome_not_found(self):
        tracker = AccuracyTracker()
        with pytest.raises(KeyError):
            tracker.record_outcome(uuid4(), {"pick": "X"})

    def test_calculate_accuracy(self):
        tracker = AccuracyTracker()
        _seed_predictions(tracker, correct_ratio=0.8, count=10)
        accuracy = tracker.calculate_accuracy("play_caller")
        assert accuracy.correct == 8
        assert accuracy.incorrect == 2
        assert accuracy.accuracy_rate == 0.8

    def test_calculate_accuracy_with_title_filter(self):
        tracker = AccuracyTracker()
        _seed_predictions(tracker, title="madden26", count=5, correct_ratio=1.0)
        _seed_predictions(tracker, title="cfb26", count=5, correct_ratio=0.0)

        madden = tracker.calculate_accuracy(
            "play_caller", AccuracyFilters(title="madden26")
        )
        cfb = tracker.calculate_accuracy(
            "play_caller", AccuracyFilters(title="cfb26")
        )
        assert madden.accuracy_rate == 1.0
        assert cfb.accuracy_rate == 0.0

    def test_get_accuracy_trend(self):
        tracker = AccuracyTracker()
        _seed_predictions(tracker, count=5, correct_ratio=0.6)
        trend = tracker.get_accuracy_trend("play_caller", periods=2, period_days=7)
        assert trend.agent_name == "play_caller"
        assert len(trend.periods) == 2
        assert trend.trend_direction in ("improving", "stable", "declining")

    def test_get_prediction(self):
        tracker = AccuracyTracker()
        ctx = _make_context()
        rec = tracker.track_prediction("a", {"x": 1}, 0.5, ctx)
        assert tracker.get_prediction(rec.id) is rec
        assert tracker.get_prediction(uuid4()) is None


# ===========================================================================
# RollbackManager tests
# ===========================================================================


class TestRollbackManager:
    def test_snapshot_and_retrieve(self):
        mgr = RollbackManager()
        snap = mgr.snapshot_agent_state("agent_a", {"version": 1}, accuracy=0.9)
        assert snap.agent_name == "agent_a"
        assert mgr.get_active_snapshot("agent_a") == snap
        assert len(mgr.get_snapshots("agent_a")) == 1

    def test_rollback_to_previous(self):
        mgr = RollbackManager()
        snap1 = mgr.snapshot_agent_state("agent_a", {"version": 1}, accuracy=0.9)
        snap2 = mgr.snapshot_agent_state("agent_a", {"version": 2}, accuracy=0.6)
        assert mgr.get_active_snapshot("agent_a").id == snap2.id

        event = mgr.rollback_agent("agent_a", reason="accuracy dropped")
        # Should roll back to snap1 (higher accuracy)
        assert event.to_snapshot_id == snap1.id
        assert mgr.get_active_snapshot("agent_a").id == snap1.id

    def test_rollback_to_specific_snapshot(self):
        mgr = RollbackManager()
        snap1 = mgr.snapshot_agent_state("agent_a", {"v": 1}, accuracy=0.85)
        snap2 = mgr.snapshot_agent_state("agent_a", {"v": 2}, accuracy=0.90)
        snap3 = mgr.snapshot_agent_state("agent_a", {"v": 3}, accuracy=0.70)

        event = mgr.rollback_agent("agent_a", "test", to_snapshot_id=snap1.id)
        assert event.to_snapshot_id == snap1.id

    def test_rollback_no_snapshots_raises(self):
        mgr = RollbackManager()
        with pytest.raises(ValueError, match="No snapshots"):
            mgr.rollback_agent("nonexistent", "reason")

    def test_rollback_history(self):
        mgr = RollbackManager()
        mgr.snapshot_agent_state("agent_a", {"v": 1}, accuracy=0.9)
        mgr.snapshot_agent_state("agent_a", {"v": 2}, accuracy=0.5)
        mgr.rollback_agent("agent_a", "bad update")

        history = mgr.get_rollback_history("agent_a")
        assert history.agent_name == "agent_a"
        assert len(history.events) == 1
        assert history.events[0].reason == "bad update"

    def test_recent_rollback_count(self):
        mgr = RollbackManager()
        mgr.snapshot_agent_state("a", {"v": 1}, accuracy=0.9)
        mgr.snapshot_agent_state("a", {"v": 2}, accuracy=0.5)
        mgr.rollback_agent("a", "reason1")

        count = mgr.get_recent_rollback_count("a", datetime.utcnow() - timedelta(hours=1))
        assert count == 1

        count_old = mgr.get_recent_rollback_count("a", datetime.utcnow() + timedelta(hours=1))
        assert count_old == 0


# ===========================================================================
# TruthEngine tests
# ===========================================================================


class TestTruthEngine:
    def _build_engine_with_data(
        self,
        correct_ratio: float = 0.8,
        count: int = 20,
    ) -> TruthEngine:
        engine = TruthEngine()
        _seed_predictions(engine.tracker, correct_ratio=correct_ratio, count=count)
        return engine

    def test_audit_recommendation_correct(self):
        engine = TruthEngine()
        ctx = _make_context()
        rec = engine.tracker.track_prediction("agent_a", {"pick": "X"}, 0.9, ctx)

        result = engine.audit_recommendation(rec.id, {"pick": "X"})
        assert result.verdict == OutcomeVerdict.CORRECT
        assert result.agent_name == "agent_a"

    def test_audit_recommendation_incorrect(self):
        engine = TruthEngine()
        ctx = _make_context()
        rec = engine.tracker.track_prediction("agent_a", {"pick": "X"}, 0.9, ctx)

        result = engine.audit_recommendation(rec.id, {"pick": "WRONG"})
        assert result.verdict == OutcomeVerdict.INCORRECT

    def test_audit_recommendation_not_found(self):
        engine = TruthEngine()
        with pytest.raises(KeyError):
            engine.audit_recommendation(uuid4(), {"pick": "X"})

    def test_get_agent_accuracy(self):
        engine = self._build_engine_with_data(correct_ratio=0.75, count=20)
        accuracy = engine.get_agent_accuracy("play_caller")
        assert accuracy.accuracy_rate == 0.75
        assert accuracy.total_predictions == 20

    def test_get_agent_accuracy_with_title(self):
        engine = TruthEngine()
        _seed_predictions(engine.tracker, title="madden26", count=10, correct_ratio=1.0)
        _seed_predictions(engine.tracker, title="cfb26", count=10, correct_ratio=0.5)

        acc = engine.get_agent_accuracy("play_caller", title="madden26")
        assert acc.accuracy_rate == 1.0

    def test_detect_degradation_none(self):
        engine = self._build_engine_with_data(correct_ratio=0.9, count=20)
        report = engine.detect_degradation("play_caller", "madden26")
        # All predictions are recent, so baseline == recent — no degradation
        assert report.severity == DegradationSeverity.NONE
        assert report.is_degrading is False

    def test_detect_degradation_severity_classification(self):
        engine = TruthEngine()
        # Directly test the classifier
        assert engine._classify_severity(0.03) == DegradationSeverity.NONE
        assert engine._classify_severity(0.06) == DegradationSeverity.MILD
        assert engine._classify_severity(0.12) == DegradationSeverity.MODERATE
        assert engine._classify_severity(0.22) == DegradationSeverity.SEVERE
        assert engine._classify_severity(0.35) == DegradationSeverity.CRITICAL

    def test_trigger_rollback(self):
        engine = TruthEngine()
        engine.rollback.snapshot_agent_state("agent_a", {"v": 1}, accuracy=0.9)
        engine.rollback.snapshot_agent_state("agent_a", {"v": 2}, accuracy=0.5)

        event = engine.trigger_rollback("agent_a", "accuracy tanked")
        assert event.reason == "accuracy tanked"
        assert engine.rollback.get_active_snapshot("agent_a").config == {"v": 1}

    def test_trigger_rollback_no_snapshots(self):
        engine = TruthEngine()
        with pytest.raises(ValueError):
            engine.trigger_rollback("ghost_agent", "no snapshots")

    def test_confidence_calibration(self):
        engine = TruthEngine()
        # Seed predictions with high confidence that are mostly correct
        for i in range(20):
            ctx = _make_context()
            rec = engine.tracker.track_prediction(
                "agent_a",
                {"pick": str(i)},
                confidence=0.9,
                context=ctx,
            )
            outcome = {"pick": str(i)} if i < 16 else {"pick": "wrong"}
            engine.tracker.record_outcome(rec.id, outcome)

        cal = engine.get_confidence_calibration("agent_a", num_buckets=5)
        assert cal.agent_name == "agent_a"
        assert len(cal.buckets) == 5
        assert cal.calibration_error >= 0

    def test_confidence_calibration_empty_agent(self):
        engine = TruthEngine()
        cal = engine.get_confidence_calibration("nonexistent")
        assert cal.calibration_error == 0.0
        assert len(cal.buckets) == 5

    def test_flag_stale_logic(self):
        engine = TruthEngine()
        _seed_predictions(engine.tracker, agent="agent_a", count=5)
        flag = engine.flag_stale_logic("madden26", "1.2.0")
        assert flag.title == "madden26"
        assert flag.patch_version == "1.2.0"
        assert "agent_a" in flag.affected_agents

    def test_flag_stale_logic_specific_agents(self):
        engine = TruthEngine()
        flag = engine.flag_stale_logic("cfb26", "2.0.0", affected_agents=["agent_x"])
        assert flag.affected_agents == ["agent_x"]

    def test_generate_weekly_report(self):
        engine = self._build_engine_with_data(correct_ratio=0.9, count=20)
        report = engine.generate_weekly_report()
        assert report.total_predictions == 20
        assert report.total_resolved == 20
        assert report.overall_accuracy == 0.9
        assert len(report.agents) == 1
        assert report.agents[0].agent_name == "play_caller"

    def test_generate_weekly_report_multiple_agents(self):
        engine = TruthEngine()
        _seed_predictions(engine.tracker, agent="agent_a", count=10, correct_ratio=1.0)
        _seed_predictions(engine.tracker, agent="agent_b", count=10, correct_ratio=0.5)

        report = engine.generate_weekly_report()
        assert report.total_predictions == 20
        assert len(report.agents) == 2

        names = {a.agent_name for a in report.agents}
        assert names == {"agent_a", "agent_b"}

    def test_generate_weekly_report_empty(self):
        engine = TruthEngine()
        report = engine.generate_weekly_report()
        assert report.total_predictions == 0
        assert report.overall_accuracy == 0.0
        assert len(report.agents) == 0

    def test_get_all_agent_names(self):
        engine = TruthEngine()
        _seed_predictions(engine.tracker, agent="alpha", count=3)
        _seed_predictions(engine.tracker, agent="beta", count=2)
        names = engine.get_all_agent_names()
        assert set(names) == {"alpha", "beta"}
