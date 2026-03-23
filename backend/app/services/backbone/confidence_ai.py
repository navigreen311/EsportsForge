"""ConfidenceAI — confidence scoring and calibration for recommendations.

Every recommendation the platform makes gets a confidence score.
ConfidenceAI evaluates data quality, sample size, historical accuracy,
and situational novelty to produce a calibrated confidence percentage
and risk level. Integrates with the Truth Engine to learn from
past prediction accuracy.
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID, uuid4

from app.schemas.drill import (
    ConfidenceFactor,
    ConfidenceScore,
    RiskLevel,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_CONFIDENCE = 50.0
_HIGH_CONFIDENCE_THRESHOLD = 75.0
_LOW_CONFIDENCE_THRESHOLD = 35.0

# Risk thresholds
_RISK_THRESHOLDS = {
    RiskLevel.LOW: 70.0,
    RiskLevel.MODERATE: 50.0,
    RiskLevel.HIGH: 30.0,
    RiskLevel.CRITICAL: 0.0,  # Anything below HIGH threshold
}

# Factor weights for confidence calculation
_FACTOR_WEIGHTS = {
    "data_quality": 0.25,
    "sample_size": 0.20,
    "historical_accuracy": 0.25,
    "situational_match": 0.15,
    "recency": 0.15,
}

# ---------------------------------------------------------------------------
# In-memory calibration store
# ---------------------------------------------------------------------------

# agent_name -> calibration multiplier
_calibrations: dict[str, float] = {}

# agent_name -> historical accuracy records
_accuracy_history: dict[str, list[float]] = {}


def _classify_risk(confidence_pct: float) -> RiskLevel:
    """Map confidence percentage to a risk level."""
    if confidence_pct >= _RISK_THRESHOLDS[RiskLevel.LOW]:
        return RiskLevel.LOW
    if confidence_pct >= _RISK_THRESHOLDS[RiskLevel.MODERATE]:
        return RiskLevel.MODERATE
    if confidence_pct >= _RISK_THRESHOLDS[RiskLevel.HIGH]:
        return RiskLevel.HIGH
    return RiskLevel.CRITICAL


class ConfidenceAI:
    """Scores recommendation confidence and calibrates via Truth Engine feedback.

    Every recommendation passes through ConfidenceAI to get a confidence
    percentage and risk level before being shown to the player.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Core scoring
    # ------------------------------------------------------------------

    def score_recommendation(
        self,
        recommendation: dict,
        context: dict | None = None,
    ) -> ConfidenceScore:
        """Score a recommendation's confidence and risk level.

        Parameters
        ----------
        recommendation:
            Dict with at least 'agent_name' and 'content' keys.
        context:
            Optional context dict with 'data_quality', 'sample_size',
            'historical_accuracy', 'situational_match', 'recency'.

        Returns
        -------
        ConfidenceScore
            Confidence percentage, risk level, and contributing factors.
        """
        ctx = context or {}
        agent_name = recommendation.get("agent_name", "unknown")

        # Evaluate each confidence factor
        factors = self.get_confidence_factors(recommendation, ctx)

        # Calculate weighted confidence
        weighted_sum = 0.0
        total_weight = 0.0
        for factor in factors:
            weight = _FACTOR_WEIGHTS.get(factor.factor, 0.1)
            if factor.direction == "positive":
                weighted_sum += weight * factor.weight * 100
            else:
                weighted_sum += weight * (1.0 - factor.weight) * 100
            total_weight += weight

        if total_weight > 0:
            raw_confidence = weighted_sum / total_weight
        else:
            raw_confidence = _DEFAULT_CONFIDENCE

        # Apply calibration multiplier if available
        calibration = _calibrations.get(agent_name, 1.0)
        calibrated_confidence = max(0.0, min(100.0, raw_confidence * calibration))
        is_calibrated = agent_name in _calibrations

        risk = _classify_risk(calibrated_confidence)

        explanation = self._build_explanation(calibrated_confidence, risk, factors)

        recommendation_id = recommendation.get("id", uuid4())
        if isinstance(recommendation_id, str):
            recommendation_id = UUID(recommendation_id)

        score = ConfidenceScore(
            recommendation_id=recommendation_id,
            confidence_pct=round(calibrated_confidence, 1),
            risk_level=risk,
            factors=factors,
            calibrated=is_calibrated,
            explanation=explanation,
        )

        logger.info(
            "Confidence score for %s: %.1f%% (%s risk, calibrated=%s)",
            agent_name, calibrated_confidence, risk.value, is_calibrated,
        )
        return score

    # ------------------------------------------------------------------
    # Factor analysis
    # ------------------------------------------------------------------

    def get_confidence_factors(
        self,
        recommendation: dict,
        context: dict | None = None,
    ) -> list[ConfidenceFactor]:
        """Identify factors driving confidence up or down.

        Parameters
        ----------
        recommendation:
            The recommendation to evaluate.
        context:
            Optional context with factor values.

        Returns
        -------
        list[ConfidenceFactor]
            Factors with direction, weight, and explanation.
        """
        ctx = context or {}
        factors: list[ConfidenceFactor] = []

        # Data quality factor
        data_quality = ctx.get("data_quality", 0.5)
        factors.append(ConfidenceFactor(
            factor="data_quality",
            direction="positive" if data_quality >= 0.5 else "negative",
            weight=data_quality,
            explanation=(
                f"Data quality is {'strong' if data_quality >= 0.7 else 'moderate' if data_quality >= 0.4 else 'weak'} "
                f"({data_quality:.0%})."
            ),
        ))

        # Sample size factor
        sample_size = ctx.get("sample_size", 0)
        sample_weight = min(1.0, sample_size / 50) if sample_size > 0 else 0.2
        factors.append(ConfidenceFactor(
            factor="sample_size",
            direction="positive" if sample_weight >= 0.5 else "negative",
            weight=sample_weight,
            explanation=(
                f"Based on {sample_size} data points "
                f"({'sufficient' if sample_weight >= 0.5 else 'limited'} sample)."
            ),
        ))

        # Historical accuracy factor
        agent_name = recommendation.get("agent_name", "unknown")
        hist = _accuracy_history.get(agent_name, [])
        if hist:
            avg_accuracy = sum(hist) / len(hist)
        else:
            avg_accuracy = ctx.get("historical_accuracy", 0.5)
        factors.append(ConfidenceFactor(
            factor="historical_accuracy",
            direction="positive" if avg_accuracy >= 0.6 else "negative",
            weight=avg_accuracy,
            explanation=(
                f"Agent '{agent_name}' historical accuracy: {avg_accuracy:.0%} "
                f"({'reliable' if avg_accuracy >= 0.7 else 'average' if avg_accuracy >= 0.5 else 'unreliable'})."
            ),
        ))

        # Situational match factor
        sit_match = ctx.get("situational_match", 0.5)
        factors.append(ConfidenceFactor(
            factor="situational_match",
            direction="positive" if sit_match >= 0.5 else "negative",
            weight=sit_match,
            explanation=(
                f"Situation {'closely matches' if sit_match >= 0.7 else 'partially matches' if sit_match >= 0.4 else 'poorly matches'} "
                f"known patterns ({sit_match:.0%})."
            ),
        ))

        # Recency factor
        recency = ctx.get("recency", 0.5)
        factors.append(ConfidenceFactor(
            factor="recency",
            direction="positive" if recency >= 0.5 else "negative",
            weight=recency,
            explanation=(
                f"Data recency is {'current' if recency >= 0.7 else 'somewhat dated' if recency >= 0.4 else 'stale'} "
                f"({recency:.0%})."
            ),
        ))

        return factors

    # ------------------------------------------------------------------
    # Calibration via Truth Engine
    # ------------------------------------------------------------------

    def calibrate_confidence(
        self,
        agent_name: str,
        historical_accuracy: float,
    ) -> float:
        """Adjust confidence calibration based on Truth Engine feedback.

        If an agent's historical accuracy is lower than its average
        confidence, the calibration multiplier is reduced (and vice
        versa).

        Parameters
        ----------
        agent_name:
            Name of the agent to calibrate.
        historical_accuracy:
            Actual accuracy rate from Truth Engine (0-1).

        Returns
        -------
        float
            The new calibration multiplier.
        """
        # Record accuracy
        _accuracy_history.setdefault(agent_name, []).append(historical_accuracy)

        # Calculate calibration multiplier
        # If agent predicts at 80% confidence but is only 60% accurate,
        # multiplier = 0.60 / 0.80 = 0.75 (scale down)
        current_cal = _calibrations.get(agent_name, 1.0)

        # Blend new accuracy with existing calibration (exponential smoothing)
        alpha = 0.3  # Learning rate
        new_cal = current_cal * (1 - alpha) + (historical_accuracy / max(0.01, current_cal)) * alpha

        # Clamp between 0.5 and 1.5
        new_cal = max(0.5, min(1.5, new_cal))
        _calibrations[agent_name] = round(new_cal, 4)

        logger.info(
            "Calibrated %s: accuracy=%.2f, multiplier=%.4f -> %.4f",
            agent_name, historical_accuracy, current_cal, new_cal,
        )
        return new_cal

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_explanation(
        confidence: float,
        risk: RiskLevel,
        factors: list[ConfidenceFactor],
    ) -> str:
        """Build a human-readable confidence explanation."""
        positive = [f.factor for f in factors if f.direction == "positive"]
        negative = [f.factor for f in factors if f.direction == "negative"]

        parts = [f"Confidence: {confidence:.1f}% ({risk.value} risk)."]
        if positive:
            parts.append(f"Positive factors: {', '.join(positive)}.")
        if negative:
            parts.append(f"Concerns: {', '.join(negative)}.")

        return " ".join(parts)
