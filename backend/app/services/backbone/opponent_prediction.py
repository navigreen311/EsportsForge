"""Opponent Prediction Engine — Predict what an opponent will do next.

Uses historical play data and situational context to build a frequency-based
prediction model.  Learns from actual calls to refine accuracy over time.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime
from typing import Any

from app.schemas.opponent import Prediction

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory model store  (will be replaced with persistent storage)
# ---------------------------------------------------------------------------

# Key: opponent_id -> situation -> list of actions observed
_model_store: dict[str, dict[str, list[str]]] = {}


def _ensure_opponent(opponent_id: str) -> dict[str, list[str]]:
    """Return (and lazily create) the model dict for an opponent."""
    if opponent_id not in _model_store:
        _model_store[opponent_id] = {}
    return _model_store[opponent_id]


def _reset_store() -> None:
    """Clear the model store (test helper)."""
    _model_store.clear()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict_next_call(
    opponent_id: str,
    situation: str,
    history: list[dict[str, Any]] | None = None,
) -> Prediction:
    """Predict what *opponent_id* will do next in *situation*.

    Uses the internal model if it has data for this opponent + situation,
    falling back to inline *history* if provided.

    Parameters
    ----------
    opponent_id:
        Unique identifier for the opponent.
    situation:
        Current game situation string (e.g. ``"3rd & 7"``).
    history:
        Optional list of ``{"situation": ..., "action": ...}`` dicts to
        bootstrap the model on-the-fly.
    """
    model = _ensure_opponent(opponent_id)

    # Bootstrap from inline history if provided
    if history:
        for entry in history:
            sit = entry.get("situation", "")
            act = entry.get("action", "")
            if sit and act:
                model.setdefault(sit, []).append(act)

    actions = model.get(situation, [])

    if not actions:
        return Prediction(
            opponent_id=opponent_id,
            situation=situation,
            predicted_action="unknown",
            confidence=0.0,
            reasoning="No data for this situation.",
        )

    counter = Counter(actions)
    total = len(actions)
    most_common_action, most_common_count = counter.most_common(1)[0]
    confidence = most_common_count / total

    alternatives = [
        {"action": action, "probability": round(count / total, 3)}
        for action, count in counter.most_common()
        if action != most_common_action
    ]

    reasoning = (
        f"Based on {total} observations in '{situation}', "
        f"'{most_common_action}' occurs {most_common_count} times ({confidence:.0%})."
    )

    return Prediction(
        opponent_id=opponent_id,
        situation=situation,
        predicted_action=most_common_action,
        confidence=round(confidence, 3),
        alternatives=alternatives,
        reasoning=reasoning,
    )


def get_prediction_confidence(prediction: Prediction) -> float:
    """Return the confidence score for a prediction.

    Applies a penalty when the sample size is very small (< 5 observations
    mentioned in reasoning).
    """
    base = prediction.confidence

    # If we parsed "0 observations" the confidence should be 0
    if prediction.predicted_action == "unknown":
        return 0.0

    # Light penalty for sparse data — extract sample size from reasoning
    try:
        # reasoning format: "Based on N observations ..."
        parts = prediction.reasoning.split()
        idx = parts.index("observations")
        n = int(parts[idx - 1])
        if n < 5:
            base *= n / 5
    except (ValueError, IndexError):
        pass

    return round(min(1.0, max(0.0, base)), 3)


def update_model(opponent_id: str, actual_call: dict[str, Any]) -> None:
    """Learn from an actual call to improve future predictions.

    Parameters
    ----------
    actual_call:
        ``{"situation": "...", "action": "..."}``
    """
    situation = actual_call.get("situation", "")
    action = actual_call.get("action", "")
    if not situation or not action:
        logger.warning("update_model called with incomplete data: %s", actual_call)
        return

    model = _ensure_opponent(opponent_id)
    model.setdefault(situation, []).append(action)
    logger.debug(
        "Model updated for %s in '%s': added '%s'",
        opponent_id, situation, action,
    )
