"""BenchmarkAI — percentile comparisons, dimension scores, standout skills, improvement velocity.

Compares player performance against population baselines stored in memory.
In production, baselines would come from an analytics database; here we use
configurable reference distributions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.schemas.mental import (
    DimensionScores,
    ImprovementVelocity,
    PercentileComparison,
    StandoutSkill,
    StandoutSkillsReport,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

# user_id -> title -> list of DimensionScores snapshots (time series)
_score_history: dict[str, dict[str, list[dict[str, Any]]]] = {}

# Population baselines: dimension -> {mean, std} (normal approximation)
_POPULATION_BASELINES: dict[str, dict[str, float]] = {
    "read_speed": {"mean": 0.50, "std": 0.15},
    "user_defense": {"mean": 0.50, "std": 0.15},
    "clutch": {"mean": 0.45, "std": 0.18},
    "anti_meta": {"mean": 0.40, "std": 0.20},
    "execution": {"mean": 0.50, "std": 0.15},
    "mental": {"mean": 0.50, "std": 0.17},
}

# Percentile lookup (z-score -> percentile, simplified)
_Z_TO_PERCENTILE = [
    (-3.0, 1), (-2.5, 1), (-2.0, 2), (-1.5, 7), (-1.0, 16),
    (-0.5, 31), (0.0, 50), (0.5, 69), (1.0, 84), (1.5, 93),
    (2.0, 98), (2.5, 99), (3.0, 100),
]

# Percentile to z-score (reverse)
_PERCENTILE_TO_Z = {p: z for z, p in _Z_TO_PERCENTILE}

_STANDOUT_THRESHOLD = 0.60  # above this is considered "above average"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _z_to_percentile(z: float) -> int:
    """Convert a z-score to an approximate percentile."""
    for z_val, pct in _Z_TO_PERCENTILE:
        if z <= z_val:
            return pct
    return 100


def _percentile_to_z(pct: int) -> float:
    """Convert a target percentile to an approximate z-score."""
    best_z = 0.0
    best_diff = 999.0
    for z_val, p_val in _Z_TO_PERCENTILE:
        diff = abs(p_val - pct)
        if diff < best_diff:
            best_diff = diff
            best_z = z_val
    return best_z


def _score_to_percentile(dimension: str, score: float) -> int:
    """Convert a raw score to a population percentile."""
    baseline = _POPULATION_BASELINES.get(dimension, {"mean": 0.5, "std": 0.15})
    if baseline["std"] == 0:
        return 50
    z = (score - baseline["mean"]) / baseline["std"]
    return _z_to_percentile(z)


# ---------------------------------------------------------------------------
# Data ingestion
# ---------------------------------------------------------------------------

def record_dimension_snapshot(
    user_id: str,
    title: str,
    scores: dict[str, float],
) -> DimensionScores:
    """Record a point-in-time dimension score snapshot for a user."""
    snapshot = {
        "read_speed": scores.get("read_speed", 0.5),
        "user_defense": scores.get("user_defense", 0.5),
        "clutch": scores.get("clutch", 0.5),
        "anti_meta": scores.get("anti_meta", 0.5),
        "execution": scores.get("execution", 0.5),
        "mental": scores.get("mental", 0.5),
        "timestamp": _now().isoformat(),
    }
    _score_history.setdefault(user_id, {}).setdefault(title, []).append(snapshot)

    return DimensionScores(
        user_id=user_id,
        title=title,
        **{k: v for k, v in snapshot.items() if k != "timestamp"},
        computed_at=_now(),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compare_to_percentile(
    user_id: str,
    title: str,
    percentile: int = 95,
) -> PercentileComparison:
    """Compare the player's current scores to a target percentile.

    Returns dimension-level gaps showing where the player falls short of
    the target and where they already exceed it.
    """
    current = get_dimension_scores(user_id, title)
    target_z = _percentile_to_z(percentile)

    dimensions: dict[str, float] = {}
    gaps: dict[str, float] = {}
    player_percentiles: list[int] = []

    for dim in ["read_speed", "user_defense", "clutch", "anti_meta", "execution", "mental"]:
        score = getattr(current, dim)
        dim_pct = _score_to_percentile(dim, score)
        player_percentiles.append(dim_pct)
        dimensions[dim] = score

        baseline = _POPULATION_BASELINES[dim]
        target_score = baseline["mean"] + target_z * baseline["std"]
        gap = round(target_score - score, 4)
        gaps[dim] = gap

    avg_percentile = (
        round(sum(player_percentiles) / len(player_percentiles))
        if player_percentiles
        else 50
    )

    # Summary
    above = [d for d, g in gaps.items() if g <= 0]
    below = [d for d, g in gaps.items() if g > 0]
    if not below:
        summary = f"Player already meets or exceeds the {percentile}th percentile across all dimensions."
    elif not above:
        summary = f"Player is below the {percentile}th percentile in all dimensions."
    else:
        summary = (
            f"Player exceeds {percentile}th percentile in {', '.join(above)} "
            f"but needs improvement in {', '.join(below)}."
        )

    return PercentileComparison(
        user_id=user_id,
        title=title,
        target_percentile=percentile,
        player_percentile=avg_percentile,
        dimensions=dimensions,
        gaps=gaps,
        summary=summary,
    )


def get_dimension_scores(user_id: str, title: str) -> DimensionScores:
    """Return the latest dimension scores for a player on a title.

    If no snapshots exist, returns neutral baselines.
    """
    snapshots = _score_history.get(user_id, {}).get(title, [])
    if not snapshots:
        return DimensionScores(user_id=user_id, title=title, computed_at=_now())

    latest = snapshots[-1]
    return DimensionScores(
        user_id=user_id,
        title=title,
        read_speed=latest.get("read_speed", 0.5),
        user_defense=latest.get("user_defense", 0.5),
        clutch=latest.get("clutch", 0.5),
        anti_meta=latest.get("anti_meta", 0.5),
        execution=latest.get("execution", 0.5),
        mental=latest.get("mental", 0.5),
        computed_at=_now(),
    )


def identify_standout_skills(user_id: str, title: str) -> StandoutSkillsReport:
    """Identify dimensions where the player is above average."""
    current = get_dimension_scores(user_id, title)
    standouts: list[StandoutSkill] = []

    for dim in ["read_speed", "user_defense", "clutch", "anti_meta", "execution", "mental"]:
        score = getattr(current, dim)
        if score >= _STANDOUT_THRESHOLD:
            pct = _score_to_percentile(dim, score)
            standouts.append(StandoutSkill(
                dimension=dim,
                score=score,
                percentile=pct,
                description=f"Top {100 - pct}% in {dim.replace('_', ' ')}",
            ))

    standouts.sort(key=lambda s: s.score, reverse=True)
    top_skill = standouts[0].dimension if standouts else ""

    return StandoutSkillsReport(
        user_id=user_id,
        title=title,
        standout_skills=standouts,
        top_skill=top_skill,
    )


def get_improvement_velocity(user_id: str, title: str) -> ImprovementVelocity:
    """Calculate rate of improvement over 7d, 30d, and 90d windows.

    Velocity is the slope of the trend line for each dimension's score
    over the given window. Positive = improving, negative = declining.
    """
    snapshots = _score_history.get(user_id, {}).get(title, [])

    if len(snapshots) < 2:
        return ImprovementVelocity(user_id=user_id, title=title)

    dims = ["read_speed", "user_defense", "clutch", "anti_meta", "execution", "mental"]

    def _avg_change(window: int) -> tuple[float, str, list[str]]:
        """Average score change over the last *window* snapshots."""
        sliced = snapshots[-window:] if len(snapshots) >= window else snapshots
        if len(sliced) < 2:
            return 0.0, "", []

        first = sliced[0]
        last = sliced[-1]
        changes: dict[str, float] = {}
        for d in dims:
            changes[d] = round(last.get(d, 0.5) - first.get(d, 0.5), 4)

        avg = round(sum(changes.values()) / len(changes), 4)
        fastest = max(changes, key=changes.get)  # type: ignore[arg-type]
        declining = [d for d, c in changes.items() if c < -0.01]
        return avg, fastest, declining

    v7, fast7, dec7 = _avg_change(7)
    v30, fast30, dec30 = _avg_change(30)
    v90, fast90, dec90 = _avg_change(90)

    # Use the longest available window for overall fastest / declining
    fastest = fast90 or fast30 or fast7
    declining = dec90 or dec30 or dec7

    return ImprovementVelocity(
        user_id=user_id,
        title=title,
        velocity_7d=v7,
        velocity_30d=v30,
        velocity_90d=v90,
        fastest_improving=fastest,
        declining=declining,
    )


# ---------------------------------------------------------------------------
# Reset (for testing)
# ---------------------------------------------------------------------------

def _reset() -> None:
    """Clear all in-memory stores. For testing only."""
    _score_history.clear()
