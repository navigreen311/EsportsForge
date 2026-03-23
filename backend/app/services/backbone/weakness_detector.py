"""Weakness detection — identifies and scores player weaknesses from game data."""

from __future__ import annotations

import logging
from uuid import uuid4

from app.schemas.impact_rank import (
    ImpactScore,
    Weakness,
    WeaknessCategory,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Category detection heuristics (keyword → category mapping)
# ---------------------------------------------------------------------------

_CATEGORY_KEYWORDS: dict[WeaknessCategory, set[str]] = {
    WeaknessCategory.MECHANICAL: {
        "accuracy", "timing", "execution", "input", "combo",
        "reaction", "speed", "apm", "micro", "stick",
    },
    WeaknessCategory.DECISION: {
        "playcall", "read", "audible", "adjustment", "choice",
        "option", "decision", "route", "coverage", "formation",
    },
    WeaknessCategory.KNOWLEDGE: {
        "matchup", "meta", "counter", "scheme", "playbook",
        "roster", "rating", "stat", "rule", "mechanic",
    },
    WeaknessCategory.MENTAL: {
        "tilt", "rage", "patience", "composure", "focus",
        "consistency", "choke", "pressure", "clutch", "momentum",
    },
    WeaknessCategory.TACTICAL: {
        "positioning", "spacing", "tempo", "clock", "field",
        "zone", "blitz", "coverage", "alignment", "personnel",
    },
}


def categorize_weakness(weakness: Weakness) -> WeaknessCategory:
    """Classify a weakness into a category based on its label and description.

    Uses keyword matching against the weakness text.  Falls back to DECISION
    if nothing matches (most common catch-all in competitive gaming).
    """
    text = f"{weakness.label} {weakness.description}".lower()
    scores: dict[WeaknessCategory, int] = {cat: 0 for cat in WeaknessCategory}
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[cat] += 1
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[best] == 0:
        return WeaknessCategory.DECISION
    return best


def estimate_win_rate_damage(
    weakness: Weakness,
    context: dict | None = None,
) -> ImpactScore:
    """Estimate how much win-rate this weakness is costing.

    In production this would query LoopAI outcome data and statistical models.
    Current implementation uses heuristic scoring based on category weights and
    evidence density.

    Args:
        weakness: The weakness to score.
        context: Optional dict with ``total_games``, ``losses_attributed``,
            ``avg_severity`` keys for richer estimation.
    """
    context = context or {}

    # Base weights per category (empirically tuned for competitive games)
    category_base: dict[WeaknessCategory, float] = {
        WeaknessCategory.MECHANICAL: 0.15,
        WeaknessCategory.DECISION: 0.25,
        WeaknessCategory.KNOWLEDGE: 0.10,
        WeaknessCategory.MENTAL: 0.20,
        WeaknessCategory.TACTICAL: 0.18,
    }

    base = category_base.get(weakness.category, 0.15)

    # Adjust by evidence density — more evidence = higher confidence
    evidence_factor = min(len(weakness.evidence) / 10.0, 1.0)

    # If real stats provided, override heuristic
    total_games = context.get("total_games", 0)
    losses_attributed = context.get("losses_attributed", 0)
    avg_severity = context.get("avg_severity", 0.5)

    if total_games > 0 and losses_attributed > 0:
        frequency = min(losses_attributed / total_games, 1.0)
        severity = min(avg_severity, 1.0)
        win_rate_damage = frequency * severity
        confidence = min(total_games / 50.0, 1.0)  # 50+ games = full confidence
    else:
        frequency = base
        severity = 0.5 + (evidence_factor * 0.3)
        win_rate_damage = frequency * severity
        confidence = 0.3 + (evidence_factor * 0.4)

    return ImpactScore(
        win_rate_damage=round(min(win_rate_damage, 1.0), 4),
        frequency=round(min(frequency, 1.0), 4),
        severity=round(min(severity, 1.0), 4),
        confidence=round(min(confidence, 1.0), 4),
    )


def detect_weaknesses(
    player_data: dict,
    title: str,
) -> list[Weakness]:
    """Analyze player data and return detected weaknesses.

    In production this would invoke ML models / LLM analysis on replay data.
    Current implementation processes structured weakness hints from player_data.

    Expected ``player_data`` shape::

        {
            "user_id": "abc",
            "stats": { ... },
            "recent_games": [ ... ],
            "weakness_hints": [
                {"label": "Poor red-zone efficiency", "description": "...", "evidence": [...]},
                ...
            ]
        }
    """
    hints = player_data.get("weakness_hints", [])
    weaknesses: list[Weakness] = []

    for hint in hints:
        w = Weakness(
            id=uuid4(),
            title=title,
            category=WeaknessCategory.DECISION,  # placeholder
            label=hint.get("label", "Unknown weakness"),
            description=hint.get("description", ""),
            evidence=hint.get("evidence", []),
        )
        # Categorize
        w.category = categorize_weakness(w)
        # Score
        w.impact_score = estimate_win_rate_damage(w, hint.get("context"))

        weaknesses.append(w)

    logger.info(
        "Detected %d weaknesses for title=%s user=%s",
        len(weaknesses),
        title,
        player_data.get("user_id", "unknown"),
    )
    return weaknesses
