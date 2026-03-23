"""Identity Engine — personal philosophy layer for each player.

Captures *how* a player wants to play (risk tolerance, aggression, pace, style)
and detects when their stated preferences diverge from actual behavior.
Recommendations are filtered through identity so advice feels natural.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.schemas.player_twin import (
    CanExecuteResponse,
    PlayerIdentity,
    PlayStyle,
    PressureLevel,
    RecommendationInput,
    SessionData,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory store  (user_id -> title -> PlayerIdentity)
# ---------------------------------------------------------------------------
_identities: dict[str, dict[str, PlayerIdentity]] = {}

# Exponential-moving-average weight for new observations
_EMA_ALPHA = 0.3


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _default_identity(user_id: str, title: str) -> PlayerIdentity:
    return PlayerIdentity(user_id=user_id, title=title, last_updated=_now())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_identity(user_id: str, title: str) -> PlayerIdentity:
    """Return the current identity profile for a player + title.

    If none exists yet, a neutral-baseline identity is returned.
    """
    return (
        _identities.get(user_id, {}).get(title)
        or _default_identity(user_id, title)
    )


def update_identity(user_id: str, observed_behavior: dict[str, Any]) -> PlayerIdentity:
    """Adjust identity dimensions based on observed in-game behavior.

    ``observed_behavior`` is a dict with optional keys matching identity
    dimensions (risk_tolerance, aggression, pace, creativity, adaptability)
    and a required ``title`` key.

    Uses an exponential moving average so recent sessions carry more weight
    while older tendencies are not immediately erased.
    """
    title = observed_behavior.get("title", "unknown")
    current = get_identity(user_id, title)

    dims = ["risk_tolerance", "aggression", "pace", "creativity", "adaptability"]
    gaps: list[float] = []

    for dim in dims:
        if dim in observed_behavior:
            old_val = getattr(current, dim)
            new_val = float(observed_behavior[dim])
            blended = old_val * (1 - _EMA_ALPHA) + new_val * _EMA_ALPHA
            blended = max(0.0, min(1.0, round(blended, 4)))
            setattr(current, dim, blended)
            gaps.append(abs(old_val - new_val))

    # Recompute stated-vs-actual gap (average divergence over updated dims)
    if gaps:
        current.stated_vs_actual_gap = round(sum(gaps) / len(gaps), 4)

    # Derive dominant style from dimensions
    current.style = _derive_style(current)
    current.last_updated = _now()

    # Persist
    _identities.setdefault(user_id, {})[title] = current

    logger.info("IdentityEngine updated user=%s title=%s style=%s", user_id, title, current.style)
    return current


def derive_identity_from_session(user_id: str, session: SessionData) -> PlayerIdentity:
    """Infer identity signals from raw session data and update the profile."""
    plays = session.plays
    if not plays:
        return get_identity(user_id, session.title)

    # Simple heuristics — real implementation will use Claude analysis
    aggressive_count = sum(1 for p in plays if p.get("aggressive", False))
    risky_count = sum(1 for p in plays if p.get("risky", False))
    fast_count = sum(1 for p in plays if p.get("fast", False))
    creative_count = sum(1 for p in plays if p.get("creative", False))
    total = len(plays) or 1

    observed = {
        "title": session.title,
        "aggression": aggressive_count / total,
        "risk_tolerance": risky_count / total,
        "pace": fast_count / total,
        "creativity": creative_count / total,
    }
    return update_identity(user_id, observed)


def filter_recommendation(
    recommendation: RecommendationInput,
    identity: PlayerIdentity,
) -> CanExecuteResponse:
    """Evaluate whether a recommendation aligns with the player's identity.

    Does NOT check execution ability — only philosophical fit.
    Returns can_execute=True if the recommendation fits the player's style.
    """
    # Difficulty vs risk tolerance
    risk_ok = recommendation.difficulty <= identity.risk_tolerance + 0.2

    # Pressure alignment
    pressure_penalty = 0.0
    if recommendation.pressure_context in (PressureLevel.HIGH, PressureLevel.CLUTCH):
        pressure_penalty = 0.2 * (1 - identity.adaptability)

    fit_score = 1.0
    if not risk_ok:
        fit_score -= 0.3
    fit_score -= pressure_penalty
    fit_score = max(0.0, min(1.0, round(fit_score, 4)))

    can_do = fit_score >= 0.5
    limiting: list[str] = []
    if not risk_ok:
        limiting.append("risk_tolerance")
    if pressure_penalty > 0.1:
        limiting.append("pressure_adaptability")

    suggestion = None
    if not can_do:
        suggestion = (
            "This recommendation may not match the player's natural style. "
            "Consider a lower-risk alternative or build up gradually."
        )

    return CanExecuteResponse(
        can_execute=can_do,
        confidence=fit_score,
        limiting_skills=limiting,
        suggestion=suggestion,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _derive_style(identity: PlayerIdentity) -> PlayStyle:
    """Map continuous dimensions to a discrete style label."""
    if identity.aggression > 0.7 and identity.risk_tolerance > 0.6:
        return PlayStyle.AGGRESSIVE
    if identity.aggression < 0.3 and identity.risk_tolerance < 0.4:
        return PlayStyle.CONSERVATIVE
    if identity.adaptability > 0.7:
        return PlayStyle.ADAPTIVE
    if identity.creativity > 0.7 and identity.risk_tolerance > 0.6:
        return PlayStyle.CHAOTIC
    return PlayStyle.BALANCED


# ---------------------------------------------------------------------------
# Testing helpers
# ---------------------------------------------------------------------------

def reset_store() -> None:
    """Clear all in-memory identity data. For testing only."""
    _identities.clear()
