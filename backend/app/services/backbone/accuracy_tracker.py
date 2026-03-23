"""Accuracy Tracker — records predictions, outcomes, and computes accuracy metrics.

This module is the bookkeeping layer of the Truth Engine.  Every agent
prediction flows through here so the platform can measure what is working
and what is not.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from uuid import UUID

from app.schemas.truth_engine import (
    AccuracyFilters,
    AccuracyPeriod,
    AccuracyTrend,
    AgentAccuracy,
    OutcomeVerdict,
    PredictionContext,
    PredictionRecord,
)

logger = logging.getLogger(__name__)


class AccuracyTracker:
    """In-memory accuracy tracker.

    Production note: swap the internal dict store for a database-backed
    repository when ready.  The public API stays the same.
    """

    def __init__(self) -> None:
        # prediction_id -> PredictionRecord
        self._predictions: dict[UUID, PredictionRecord] = {}

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def track_prediction(
        self,
        agent: str,
        prediction: dict,
        confidence: float,
        context: PredictionContext,
    ) -> PredictionRecord:
        """Record a new prediction made by an agent."""
        record = PredictionRecord(
            agent_name=agent,
            prediction=prediction,
            confidence=confidence,
            context=context,
        )
        self._predictions[record.id] = record
        logger.info(
            "Tracked prediction %s from agent=%s title=%s",
            record.id,
            agent,
            context.title,
        )
        return record

    def record_outcome(
        self,
        prediction_id: UUID,
        actual_outcome: dict,
        verdict: OutcomeVerdict | None = None,
    ) -> PredictionRecord:
        """Attach an actual outcome to a previously tracked prediction.

        If *verdict* is ``None`` a simple equality check is used.
        """
        record = self._predictions.get(prediction_id)
        if record is None:
            raise KeyError(f"Prediction {prediction_id} not found")

        record.outcome = actual_outcome
        record.resolved_at = datetime.utcnow()

        if verdict is not None:
            record.verdict = verdict
        else:
            record.verdict = self._auto_judge(record.prediction, actual_outcome)

        logger.info(
            "Recorded outcome for prediction %s — verdict=%s",
            prediction_id,
            record.verdict,
        )
        return record

    # ------------------------------------------------------------------
    # Accuracy computation
    # ------------------------------------------------------------------

    def calculate_accuracy(
        self,
        agent: str,
        filters: AccuracyFilters | None = None,
    ) -> AgentAccuracy:
        """Compute accuracy stats for *agent* with optional filters."""
        records = self._filter_records(agent, filters)
        resolved = [r for r in records if r.verdict is not None]

        correct = sum(1 for r in resolved if r.verdict == OutcomeVerdict.CORRECT)
        partial = sum(1 for r in resolved if r.verdict == OutcomeVerdict.PARTIALLY_CORRECT)
        incorrect = sum(1 for r in resolved if r.verdict == OutcomeVerdict.INCORRECT)
        indeterminate = sum(1 for r in resolved if r.verdict == OutcomeVerdict.INDETERMINATE)

        denominator = correct + partial + incorrect  # exclude indeterminate
        accuracy_rate = correct / denominator if denominator else 0.0

        # Confidence-weighted accuracy
        weighted_num = sum(
            r.confidence for r in resolved if r.verdict == OutcomeVerdict.CORRECT
        )
        weighted_den = sum(r.confidence for r in resolved if r.verdict != OutcomeVerdict.INDETERMINATE)
        weighted_accuracy = weighted_num / weighted_den if weighted_den else 0.0

        return AgentAccuracy(
            agent_name=agent,
            total_predictions=len(records),
            correct=correct,
            partially_correct=partial,
            incorrect=incorrect,
            indeterminate=indeterminate,
            accuracy_rate=round(accuracy_rate, 4),
            weighted_accuracy=round(weighted_accuracy, 4),
            filters_applied=filters,
        )

    def get_accuracy_trend(
        self,
        agent: str,
        periods: int = 4,
        period_days: int = 7,
    ) -> AccuracyTrend:
        """Return accuracy bucketed into *periods* windows of *period_days*."""
        now = datetime.utcnow()
        buckets: list[AccuracyPeriod] = []

        for i in range(periods):
            end = now - timedelta(days=i * period_days)
            start = end - timedelta(days=period_days)
            filters = AccuracyFilters(time_range_days=period_days)

            records = [
                r
                for r in self._filter_records(agent, filters=None)
                if r.created_at >= start and r.created_at < end and r.verdict is not None
            ]

            resolved = [r for r in records if r.verdict != OutcomeVerdict.INDETERMINATE]
            correct = sum(1 for r in resolved if r.verdict == OutcomeVerdict.CORRECT)
            acc = correct / len(resolved) if resolved else 0.0

            buckets.append(
                AccuracyPeriod(
                    period_start=start,
                    period_end=end,
                    accuracy_rate=round(acc, 4),
                    total_predictions=len(records),
                )
            )

        # Determine trend from first (oldest) to last (newest) bucket
        buckets.reverse()  # oldest first
        direction = self._compute_trend_direction(buckets)

        return AccuracyTrend(
            agent_name=agent,
            periods=buckets,
            trend_direction=direction,
        )

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def get_prediction(self, prediction_id: UUID) -> PredictionRecord | None:
        return self._predictions.get(prediction_id)

    def get_agent_predictions(self, agent: str) -> list[PredictionRecord]:
        return [r for r in self._predictions.values() if r.agent_name == agent]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _filter_records(
        self,
        agent: str,
        filters: AccuracyFilters | None,
    ) -> list[PredictionRecord]:
        records = [r for r in self._predictions.values() if r.agent_name == agent]

        if filters is None:
            return records

        if filters.title:
            records = [r for r in records if r.context.title == filters.title]
        if filters.mode:
            records = [r for r in records if r.context.mode == filters.mode]
        if filters.patch_version:
            records = [r for r in records if r.context.patch_version == filters.patch_version]
        if filters.situation_type:
            records = [r for r in records if r.context.situation_type == filters.situation_type]
        if filters.time_range_days:
            cutoff = datetime.utcnow() - timedelta(days=filters.time_range_days)
            records = [r for r in records if r.created_at >= cutoff]

        return records

    @staticmethod
    def _auto_judge(prediction: dict, outcome: dict) -> OutcomeVerdict:
        """Naive equality judge.  Override with domain-specific logic."""
        if prediction == outcome:
            return OutcomeVerdict.CORRECT
        # Check for partial overlap
        shared_keys = set(prediction.keys()) & set(outcome.keys())
        if shared_keys:
            matches = sum(1 for k in shared_keys if prediction[k] == outcome[k])
            ratio = matches / len(shared_keys)
            if ratio >= 0.5:
                return OutcomeVerdict.PARTIALLY_CORRECT
        return OutcomeVerdict.INCORRECT

    @staticmethod
    def _compute_trend_direction(buckets: list[AccuracyPeriod]) -> str:
        """Simple linear trend from the accuracy periods."""
        rates = [b.accuracy_rate for b in buckets if b.total_predictions > 0]
        if len(rates) < 2:
            return "stable"
        delta = rates[-1] - rates[0]
        if delta > 0.05:
            return "improving"
        if delta < -0.05:
            return "declining"
        return "stable"
