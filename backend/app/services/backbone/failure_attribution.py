"""Failure Attribution Engine — diagnoses *why* recommendations fail.

Every missed recommendation gets a root-cause classification so the
platform learns the right lesson, not just "it didn't work."
"""

from __future__ import annotations

import logging
from collections import Counter
from uuid import UUID

from app.schemas.loop_ai import (
    AttributionDistribution,
    FailureAttribution,
    FailureType,
    InterventionType,
    RecommendationOutcome,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Heuristic thresholds (will be replaced by ML scoring over time)
# ---------------------------------------------------------------------------
_HIGH_CONFIDENCE_THRESHOLD = 0.80
_LOW_CONFIDENCE_THRESHOLD = 0.40
_PRESSURE_INDICATOR_KEYWORDS = {
    "clutch",
    "overtime",
    "final_drive",
    "elimination",
    "tiebreaker",
    "comeback",
    "late_game",
}
_META_STALENESS_DAYS = 14


class AttributionEngine:
    """Classifies recommendation failures and suggests interventions.

    The engine applies a cascade of heuristic checks against the outcome
    context to produce a ranked ``FailureType``.  As the platform collects
    more data, these heuristics will be replaced by a trained classifier
    that LoopAI retrains automatically.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify_failure(
        self,
        recommendation: RecommendationOutcome,
        outcome: dict,
        context: dict,
    ) -> FailureAttribution:
        """Determine the most likely reason a recommendation failed.

        Parameters
        ----------
        recommendation:
            The evaluated recommendation outcome.
        outcome:
            Post-game result data (score, stats, opponent actions).
        context:
            Broader context: meta snapshot, player state, opponent model.

        Returns
        -------
        FailureAttribution with type, confidence, evidence, and
        suggested intervention.
        """
        failure_type, confidence, evidence = self._run_cascade(
            recommendation, outcome, context
        )

        intervention = self._map_intervention(failure_type)
        detail = self._build_intervention_detail(
            failure_type, recommendation, context
        )

        attribution = FailureAttribution(
            recommendation_id=recommendation.recommendation_id,
            failure_type=failure_type,
            confidence=confidence,
            evidence=evidence,
            suggested_intervention=intervention,
            intervention_detail=detail,
        )

        logger.info(
            "Failure attributed: rec=%s type=%s conf=%.2f",
            recommendation.recommendation_id,
            failure_type.value,
            confidence,
        )
        return attribution

    def get_attribution_distribution(
        self,
        user_id: UUID,
        title: str,
        attributions: list[FailureAttribution],
    ) -> AttributionDistribution:
        """Aggregate failure types across a player's history.

        Parameters
        ----------
        user_id:
            The player identifier.
        title:
            Game title to filter on.
        attributions:
            All attributions for this player / title.

        Returns
        -------
        AttributionDistribution with counts, most-common type, and trend.
        """
        counts: Counter[FailureType] = Counter()
        for attr in attributions:
            counts[attr.failure_type] += 1

        total = sum(counts.values())
        most_common = counts.most_common(1)[0][0] if counts else FailureType.unknown

        # Simple trend heuristic: compare first-half vs second-half failure rates
        trend = self._compute_trend(attributions)

        return AttributionDistribution(
            user_id=user_id,
            title=title,
            total_failures=total,
            distribution=dict(counts),
            most_common=most_common,
            trend=trend,
        )

    def suggest_intervention(
        self,
        failure_type: FailureType,
        player_data: dict,
    ) -> dict:
        """Return a structured intervention recommendation.

        Parameters
        ----------
        failure_type:
            The classified failure.
        player_data:
            Current player twin / profile data.

        Returns
        -------
        dict with ``intervention_type``, ``priority``, ``description``,
        and ``parameters``.
        """
        intervention = self._map_intervention(failure_type)
        priority = self._intervention_priority(failure_type, player_data)

        descriptions: dict[InterventionType | None, str] = {
            InterventionType.drill_assignment: (
                "Assign targeted drills to address execution gaps."
            ),
            InterventionType.confidence_recalibration: (
                "Recalibrate confidence model — predictions were off."
            ),
            InterventionType.opponent_model_refresh: (
                "Refresh opponent model with latest data."
            ),
            InterventionType.meta_update: (
                "Update meta snapshot — current data is stale."
            ),
            InterventionType.gameplan_revision: (
                "Revise gameplan to account for misread tendencies."
            ),
            InterventionType.mental_reset: (
                "Trigger mental-reset flow — pressure collapse detected."
            ),
            InterventionType.review_session: (
                "Schedule review session — failure cause unclear."
            ),
            None: "No specific intervention required.",
        }

        return {
            "intervention_type": intervention.value if intervention else None,
            "priority": priority,
            "description": descriptions.get(intervention, "Review recommended."),
            "failure_type": failure_type.value,
            "parameters": self._intervention_params(failure_type, player_data),
        }

    # ------------------------------------------------------------------
    # Internal cascade
    # ------------------------------------------------------------------

    def _run_cascade(
        self,
        rec: RecommendationOutcome,
        outcome: dict,
        context: dict,
    ) -> tuple[FailureType, float, list[str]]:
        """Apply ordered heuristic checks and return best match."""

        # 1. Pressure collapse — high-pressure context + player folded
        if self._check_pressure_collapse(rec, outcome, context):
            return (
                FailureType.pressure_collapse,
                0.85,
                ["High-pressure situation detected", "Performance dropped under pressure"],
            )

        # 2. Stale meta — meta data is outdated
        if self._check_stale_meta(context):
            return (
                FailureType.stale_meta,
                0.80,
                ["Meta snapshot older than threshold", "Opponent used off-meta strategy"],
            )

        # 3. Wrong opponent model — opponent behaved differently than predicted
        if self._check_wrong_opponent_model(rec, outcome, context):
            return (
                FailureType.wrong_opponent_model,
                0.75,
                ["Opponent deviated from predicted behavior", "Model prediction mismatch"],
            )

        # 4. Wrong confidence — model was overconfident or underconfident
        if self._check_wrong_confidence(rec, outcome):
            return (
                FailureType.wrong_confidence,
                0.70,
                [
                    f"Confidence was {rec.confidence_at_time:.0%} but outcome was negative",
                    "Confidence calibration error",
                ],
            )

        # 5. Bad execution — player followed rec but executed poorly
        if rec.was_followed and not rec.was_successful:
            return (
                FailureType.bad_execution,
                0.65,
                ["Recommendation was followed", "Execution quality was poor"],
            )

        # 6. Bad read — recommendation itself was wrong
        if not rec.was_followed:
            return (
                FailureType.bad_read,
                0.60,
                ["Player chose not to follow recommendation", "Rec may not have fit situation"],
            )

        # Fallback
        return (
            FailureType.unknown,
            0.30,
            ["No clear failure pattern identified"],
        )

    # ------------------------------------------------------------------
    # Heuristic checks
    # ------------------------------------------------------------------

    def _check_pressure_collapse(
        self,
        rec: RecommendationOutcome,
        outcome: dict,
        context: dict,
    ) -> bool:
        game_state = context.get("game_state", {})
        tags = set(game_state.get("tags", []))
        pressure_detected = bool(tags & _PRESSURE_INDICATOR_KEYWORDS)
        performance_drop = outcome.get("performance_delta", 0) < -0.15
        return pressure_detected and performance_drop

    def _check_stale_meta(self, context: dict) -> bool:
        meta_age_days = context.get("meta_age_days", 0)
        return meta_age_days > _META_STALENESS_DAYS

    def _check_wrong_opponent_model(
        self,
        rec: RecommendationOutcome,
        outcome: dict,
        context: dict,
    ) -> bool:
        predicted = context.get("predicted_opponent_action")
        actual = outcome.get("actual_opponent_action")
        if predicted and actual:
            return predicted != actual
        return False

    def _check_wrong_confidence(
        self,
        rec: RecommendationOutcome,
        outcome: dict,
    ) -> bool:
        if rec.confidence_at_time > _HIGH_CONFIDENCE_THRESHOLD and not rec.was_successful:
            return True
        if rec.confidence_at_time < _LOW_CONFIDENCE_THRESHOLD and rec.was_successful:
            return True
        return False

    # ------------------------------------------------------------------
    # Intervention mapping
    # ------------------------------------------------------------------

    _FAILURE_TO_INTERVENTION: dict[FailureType, InterventionType] = {
        FailureType.bad_read: InterventionType.gameplan_revision,
        FailureType.bad_execution: InterventionType.drill_assignment,
        FailureType.wrong_confidence: InterventionType.confidence_recalibration,
        FailureType.wrong_opponent_model: InterventionType.opponent_model_refresh,
        FailureType.pressure_collapse: InterventionType.mental_reset,
        FailureType.stale_meta: InterventionType.meta_update,
        FailureType.unknown: InterventionType.review_session,
    }

    def _map_intervention(self, failure_type: FailureType) -> InterventionType:
        return self._FAILURE_TO_INTERVENTION.get(
            failure_type, InterventionType.review_session
        )

    def _intervention_priority(
        self, failure_type: FailureType, player_data: dict
    ) -> str:
        """Return 'critical' | 'high' | 'medium' | 'low'."""
        critical = {FailureType.pressure_collapse, FailureType.stale_meta}
        high = {FailureType.wrong_opponent_model, FailureType.wrong_confidence}
        if failure_type in critical:
            return "critical"
        if failure_type in high:
            return "high"
        return "medium"

    def _intervention_params(
        self, failure_type: FailureType, player_data: dict
    ) -> dict:
        """Build type-specific parameters for the intervention."""
        base: dict = {"failure_type": failure_type.value}
        if failure_type == FailureType.bad_execution:
            base["drill_focus"] = player_data.get("weakest_skill", "general")
        elif failure_type == FailureType.stale_meta:
            base["refresh_scope"] = "full"
        elif failure_type == FailureType.wrong_opponent_model:
            base["opponent_id"] = player_data.get("last_opponent_id")
        return base

    def _build_intervention_detail(
        self,
        failure_type: FailureType,
        rec: RecommendationOutcome,
        context: dict,
    ) -> str:
        return (
            f"Failure type '{failure_type.value}' on recommendation "
            f"'{rec.description}'. Intervention: "
            f"{self._map_intervention(failure_type).value}."
        )

    # ------------------------------------------------------------------
    # Trend analysis
    # ------------------------------------------------------------------

    def _compute_trend(self, attributions: list[FailureAttribution]) -> str:
        """Compare failure counts in first vs second half of history."""
        if len(attributions) < 4:
            return "stable"

        sorted_attrs = sorted(attributions, key=lambda a: a.created_at)
        mid = len(sorted_attrs) // 2
        first_half = len(sorted_attrs[:mid])
        second_half = len(sorted_attrs[mid:])

        if second_half < first_half * 0.75:
            return "improving"
        if second_half > first_half * 1.25:
            return "declining"
        return "stable"
