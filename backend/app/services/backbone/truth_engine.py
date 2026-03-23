"""Truth Engine — the platform's immune system.

Prevents confident-but-wrong recommendations, the most dangerous failure
mode of any AI advisory system.  The Truth Engine:

- Audits every recommendation once the real outcome is known.
- Tracks per-agent accuracy across titles, modes, patches, and situations.
- Detects accuracy degradation and triggers automatic rollbacks.
- Flags potentially stale logic after game-patch releases.
- Produces a weekly internal performance report on the AI platform itself.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from uuid import UUID

from app.schemas.truth_engine import (
    AccuracyFilters,
    AgentAccuracy,
    AgentReportEntry,
    AuditResponse,
    CalibrationBucket,
    ConfidenceCalibration,
    DegradationReport,
    DegradationSeverity,
    OutcomeVerdict,
    PredictionContext,
    PredictionRecord,
    StaleLogicFlag,
    TruthReport,
)
from app.services.backbone.accuracy_tracker import AccuracyTracker
from app.services.backbone.rollback_manager import RollbackManager

logger = logging.getLogger(__name__)

# Degradation thresholds
_MILD_THRESHOLD = 0.05
_MODERATE_THRESHOLD = 0.10
_SEVERE_THRESHOLD = 0.20
_CRITICAL_THRESHOLD = 0.30
_AUTO_ROLLBACK_THRESHOLD = _SEVERE_THRESHOLD


class TruthEngine:
    """Orchestrates auditing, degradation detection, rollbacks, and reporting."""

    def __init__(
        self,
        accuracy_tracker: AccuracyTracker | None = None,
        rollback_manager: RollbackManager | None = None,
    ) -> None:
        self.tracker = accuracy_tracker or AccuracyTracker()
        self.rollback = rollback_manager or RollbackManager()
        self._stale_flags: list[StaleLogicFlag] = []

    # ------------------------------------------------------------------
    # Auditing
    # ------------------------------------------------------------------

    def audit_recommendation(
        self,
        recommendation_id: UUID,
        outcome: dict,
        verdict: OutcomeVerdict | None = None,
    ) -> AuditResponse:
        """Compare expected vs actual result after LoopAI closes the loop.

        Returns an :class:`AuditResponse` summarising the verdict and its
        impact on the agent's rolling accuracy.
        """
        record = self.tracker.record_outcome(recommendation_id, outcome, verdict)
        accuracy = self.tracker.calculate_accuracy(record.agent_name)

        impact = (
            f"Agent '{record.agent_name}' accuracy now {accuracy.accuracy_rate:.1%} "
            f"({accuracy.correct}/{accuracy.correct + accuracy.incorrect + accuracy.partially_correct} resolved)"
        )

        logger.info(
            "Audit complete: recommendation=%s verdict=%s impact=%s",
            recommendation_id,
            record.verdict,
            impact,
        )

        return AuditResponse(
            recommendation_id=recommendation_id,
            verdict=record.verdict,  # type: ignore[arg-type]
            agent_name=record.agent_name,
            accuracy_impact=impact,
        )

    # ------------------------------------------------------------------
    # Agent accuracy
    # ------------------------------------------------------------------

    def get_agent_accuracy(
        self,
        agent_name: str,
        title: str | None = None,
        time_range_days: int | None = None,
    ) -> AgentAccuracy:
        """Retrieve accuracy stats for a specific agent."""
        filters = AccuracyFilters(title=title, time_range_days=time_range_days)
        return self.tracker.calculate_accuracy(agent_name, filters)

    def get_all_agent_names(self) -> list[str]:
        """Return distinct agent names that have predictions."""
        return list(
            {r.agent_name for r in self.tracker._predictions.values()}
        )

    # ------------------------------------------------------------------
    # Degradation detection
    # ------------------------------------------------------------------

    def detect_degradation(
        self,
        agent_name: str,
        title: str,
        recent_days: int = 7,
        baseline_days: int = 30,
    ) -> DegradationReport:
        """Determine whether *agent_name* is degrading for *title*.

        Compares recent accuracy (last *recent_days*) against a longer
        baseline window (*baseline_days*).
        """
        recent = self.tracker.calculate_accuracy(
            agent_name,
            AccuracyFilters(title=title, time_range_days=recent_days),
        )
        baseline = self.tracker.calculate_accuracy(
            agent_name,
            AccuracyFilters(title=title, time_range_days=baseline_days),
        )

        delta = baseline.accuracy_rate - recent.accuracy_rate
        severity = self._classify_severity(delta)
        is_degrading = severity != DegradationSeverity.NONE

        recommendation = ""
        if severity == DegradationSeverity.MILD:
            recommendation = "Monitor closely over the next week."
        elif severity == DegradationSeverity.MODERATE:
            recommendation = "Investigate recent patches and data quality."
        elif severity == DegradationSeverity.SEVERE:
            recommendation = "Consider automatic rollback to last known-good state."
        elif severity == DegradationSeverity.CRITICAL:
            recommendation = "URGENT: Agent should be disabled or rolled back immediately."

        report = DegradationReport(
            agent_name=agent_name,
            title=title,
            is_degrading=is_degrading,
            severity=severity,
            current_accuracy=recent.accuracy_rate,
            baseline_accuracy=baseline.accuracy_rate,
            accuracy_delta=round(delta, 4),
            recent_window_days=recent_days,
            baseline_window_days=baseline_days,
            recommendation=recommendation,
        )

        if is_degrading:
            logger.warning(
                "Degradation detected: agent=%s title=%s severity=%s delta=%.2f%%",
                agent_name,
                title,
                severity.value,
                delta * 100,
            )

        return report

    # ------------------------------------------------------------------
    # Rollback protocol
    # ------------------------------------------------------------------

    def trigger_rollback(
        self,
        agent_name: str,
        reason: str,
        to_snapshot_id: UUID | None = None,
    ):
        """Trigger a rollback for an agent to a previous logic version."""
        event = self.rollback.rollback_agent(
            agent_name=agent_name,
            reason=reason,
            to_snapshot_id=to_snapshot_id,
        )
        logger.warning(
            "Rollback triggered for agent=%s reason='%s' target_snapshot=%s",
            agent_name,
            reason,
            event.to_snapshot_id,
        )
        return event

    # ------------------------------------------------------------------
    # Confidence calibration
    # ------------------------------------------------------------------

    def get_confidence_calibration(
        self,
        agent_name: str,
        num_buckets: int = 5,
    ) -> ConfidenceCalibration:
        """Evaluate whether the agent's confidence scores match reality.

        Splits resolved predictions into *num_buckets* confidence ranges
        and compares predicted vs actual accuracy in each.
        """
        records = [
            r
            for r in self.tracker.get_agent_predictions(agent_name)
            if r.verdict is not None and r.verdict != OutcomeVerdict.INDETERMINATE
        ]

        bucket_size = 1.0 / num_buckets
        buckets: list[CalibrationBucket] = []
        total_abs_error = 0.0

        for i in range(num_buckets):
            low = round(i * bucket_size, 2)
            high = round((i + 1) * bucket_size, 2)
            in_bucket = [r for r in records if low <= r.confidence < high or (i == num_buckets - 1 and r.confidence == high)]

            if not in_bucket:
                buckets.append(
                    CalibrationBucket(
                        confidence_range_low=low,
                        confidence_range_high=high,
                        predicted_accuracy=round((low + high) / 2, 2),
                        actual_accuracy=0.0,
                        count=0,
                    )
                )
                continue

            predicted = sum(r.confidence for r in in_bucket) / len(in_bucket)
            actual = sum(
                1 for r in in_bucket if r.verdict == OutcomeVerdict.CORRECT
            ) / len(in_bucket)

            total_abs_error += abs(predicted - actual) * len(in_bucket)

            buckets.append(
                CalibrationBucket(
                    confidence_range_low=low,
                    confidence_range_high=high,
                    predicted_accuracy=round(predicted, 4),
                    actual_accuracy=round(actual, 4),
                    count=len(in_bucket),
                )
            )

        total_counted = sum(b.count for b in buckets)
        calibration_error = total_abs_error / total_counted if total_counted else 0.0

        # Determine overconfidence / underconfidence
        weighted_predicted = sum(b.predicted_accuracy * b.count for b in buckets if b.count)
        weighted_actual = sum(b.actual_accuracy * b.count for b in buckets if b.count)

        return ConfidenceCalibration(
            agent_name=agent_name,
            buckets=buckets,
            calibration_error=round(calibration_error, 4),
            is_overconfident=weighted_predicted > weighted_actual + 0.05 if total_counted else False,
            is_underconfident=weighted_actual > weighted_predicted + 0.05 if total_counted else False,
        )

    # ------------------------------------------------------------------
    # Stale logic flagging
    # ------------------------------------------------------------------

    def flag_stale_logic(
        self,
        title: str,
        patch_version: str,
        affected_agents: list[str] | None = None,
    ) -> StaleLogicFlag:
        """Mark advice as potentially stale after a game patch."""
        if affected_agents is None:
            affected_agents = self.get_all_agent_names()

        flag = StaleLogicFlag(
            title=title,
            patch_version=patch_version,
            affected_agents=affected_agents,
        )
        self._stale_flags.append(flag)

        logger.warning(
            "Stale logic flagged: title=%s patch=%s agents=%s",
            title,
            patch_version,
            affected_agents,
        )
        return flag

    # ------------------------------------------------------------------
    # Weekly report
    # ------------------------------------------------------------------

    def generate_weekly_report(
        self,
        period_days: int = 7,
    ) -> TruthReport:
        """Generate a platform-wide accuracy and reliability report."""
        now = datetime.utcnow()
        period_start = now - timedelta(days=period_days)

        agent_names = self.get_all_agent_names()
        agent_entries: list[AgentReportEntry] = []
        total_predictions = 0
        total_resolved = 0
        total_correct = 0

        for name in agent_names:
            accuracy = self.tracker.calculate_accuracy(
                name,
                AccuracyFilters(time_range_days=period_days),
            )

            # Degradation — check across all titles
            titles = list(
                {
                    r.context.title
                    for r in self.tracker.get_agent_predictions(name)
                }
            )
            worst_severity = DegradationSeverity.NONE
            for t in titles:
                deg = self.detect_degradation(name, t)
                if deg.severity.value > worst_severity.value:
                    worst_severity = deg.severity

            calibration = self.get_confidence_calibration(name)
            rollback_count = self.rollback.get_recent_rollback_count(name, period_start)

            # Identify top failure modes
            failures = [
                r
                for r in self.tracker.get_agent_predictions(name)
                if r.verdict == OutcomeVerdict.INCORRECT and r.created_at >= period_start
            ]
            failure_situations = [
                r.context.situation_type or "unknown" for r in failures
            ]
            top_failures = self._top_n(failure_situations, 3)

            agent_entries.append(
                AgentReportEntry(
                    agent_name=name,
                    accuracy_rate=accuracy.accuracy_rate,
                    predictions_count=accuracy.total_predictions,
                    degradation_severity=worst_severity,
                    rollbacks_this_period=rollback_count,
                    confidence_calibration_error=calibration.calibration_error,
                    top_failure_modes=top_failures,
                )
            )

            total_predictions += accuracy.total_predictions
            resolved = accuracy.correct + accuracy.partially_correct + accuracy.incorrect
            total_resolved += resolved
            total_correct += accuracy.correct

        overall_accuracy = total_correct / total_resolved if total_resolved else 0.0

        # Gather stale flags in the period
        recent_stale = [
            f for f in self._stale_flags if f.flagged_at >= period_start
        ]
        # Gather rollback events in the period
        recent_rollbacks = [
            e
            for name in agent_names
            for e in self.rollback.get_rollback_history(name).events
            if e.created_at >= period_start
        ]

        report = TruthReport(
            period_start=period_start,
            period_end=now,
            overall_accuracy=round(overall_accuracy, 4),
            total_predictions=total_predictions,
            total_resolved=total_resolved,
            agents=agent_entries,
            stale_logic_flags=recent_stale,
            rollback_events=recent_rollbacks,
        )

        logger.info(
            "Weekly truth report generated: accuracy=%.1f%% predictions=%d resolved=%d",
            overall_accuracy * 100,
            total_predictions,
            total_resolved,
        )
        return report

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_severity(delta: float) -> DegradationSeverity:
        """Map an accuracy drop (baseline - recent) to a severity level."""
        if delta >= _CRITICAL_THRESHOLD:
            return DegradationSeverity.CRITICAL
        if delta >= _SEVERE_THRESHOLD:
            return DegradationSeverity.SEVERE
        if delta >= _MODERATE_THRESHOLD:
            return DegradationSeverity.MODERATE
        if delta >= _MILD_THRESHOLD:
            return DegradationSeverity.MILD
        return DegradationSeverity.NONE

    @staticmethod
    def _top_n(items: list[str], n: int) -> list[str]:
        """Return the *n* most frequent items."""
        from collections import Counter

        return [item for item, _ in Counter(items).most_common(n)]
