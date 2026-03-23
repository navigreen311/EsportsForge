"""Cross-Session Narrative Engine — growth stories, milestones, trajectories, session summaries.

Turns raw performance data into coherent human-readable narratives that help
players understand their growth arc, not just their stats.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.schemas.mental import (
    GrowthTrajectory,
    Milestone,
    MilestoneCategory,
    MomentumDirection,
    SessionSummary,
    WeeklyNarrative,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

# user_id -> title -> list[dict] weekly snapshots
_weekly_data: dict[str, dict[str, list[dict[str, Any]]]] = {}

# user_id -> list[Milestone]
_milestones: dict[str, list[Milestone]] = {}

# user_id -> session_id -> session data
_session_data: dict[str, dict[str, dict[str, Any]]] = {}

# user_id -> title -> list[dict] metric snapshots per week
_metric_history: dict[str, dict[str, list[dict[str, Any]]]] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Data ingestion
# ---------------------------------------------------------------------------

def record_weekly_snapshot(
    user_id: str,
    title: str,
    data: dict[str, Any],
) -> None:
    """Record a weekly performance snapshot."""
    _weekly_data.setdefault(user_id, {}).setdefault(title, []).append({
        **data,
        "recorded_at": _now().isoformat(),
    })


def record_session_data(
    user_id: str,
    session_id: str,
    data: dict[str, Any],
) -> None:
    """Record post-session data for narrative generation."""
    _session_data.setdefault(user_id, {})[session_id] = {
        **data,
        "recorded_at": _now().isoformat(),
    }


def record_metric_snapshot(
    user_id: str,
    title: str,
    metrics: dict[str, float],
) -> None:
    """Record a weekly metric snapshot for trajectory tracking."""
    _metric_history.setdefault(user_id, {}).setdefault(title, []).append({
        **metrics,
        "week": len(_metric_history.get(user_id, {}).get(title, [])) + 1,
        "recorded_at": _now().isoformat(),
    })


def add_milestone(user_id: str, milestone: Milestone) -> None:
    """Manually add a milestone (also used internally by detect_milestones)."""
    _milestones.setdefault(user_id, []).append(milestone)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_weekly_narrative(user_id: str, title: str) -> WeeklyNarrative:
    """Generate a coherent growth story from the most recent week's data.

    Produces a human-readable narrative with highlights, lowlights, and
    key stats rather than a raw data dump.
    """
    snapshots = _weekly_data.get(user_id, {}).get(title, [])

    if not snapshots:
        return WeeklyNarrative(
            user_id=user_id,
            title=title,
            narrative="No data available yet. Play some games to start building your story.",
            period_end=_now(),
        )

    latest = snapshots[-1]
    wins = latest.get("wins", 0)
    losses = latest.get("losses", 0)
    total = wins + losses
    win_rate = wins / total if total > 0 else 0
    best_moment = latest.get("best_moment", "")
    worst_moment = latest.get("worst_moment", "")
    improvement_areas = latest.get("improvements", [])
    decline_areas = latest.get("declines", [])

    # Build narrative
    parts: list[str] = []
    if total > 0:
        parts.append(
            f"This week you played {total} games with a {win_rate:.0%} win rate "
            f"({wins}W-{losses}L)."
        )
    else:
        parts.append("No competitive games recorded this week.")

    if improvement_areas:
        joined = ", ".join(improvement_areas)
        parts.append(f"Improvement was visible in {joined}.")
    if decline_areas:
        joined = ", ".join(decline_areas)
        parts.append(f"Areas that slipped: {joined}.")

    if win_rate >= 0.7:
        parts.append("Strong week overall — keep the momentum going.")
    elif win_rate >= 0.5:
        parts.append("Solid week with room to push higher.")
    elif total > 0:
        parts.append("Tough stretch, but every session is a learning opportunity.")

    highlights: list[str] = []
    if best_moment:
        highlights.append(best_moment)
    if win_rate >= 0.6 and total >= 5:
        highlights.append(f"Maintained {win_rate:.0%} win rate over {total} games")
    for area in improvement_areas:
        highlights.append(f"Improved in {area}")

    lowlights: list[str] = []
    if worst_moment:
        lowlights.append(worst_moment)
    for area in decline_areas:
        lowlights.append(f"Declined in {area}")

    return WeeklyNarrative(
        user_id=user_id,
        title=title,
        narrative=" ".join(parts),
        highlights=highlights,
        lowlights=lowlights,
        key_stats={
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 4),
            "games_played": total,
        },
        period_end=_now(),
    )


def detect_milestones(user_id: str) -> list[Milestone]:
    """Scan data and detect new milestones for a user.

    Examples: "First 10-game win streak", "Reached top 5% read speed",
    "100 games played", etc.

    Returns only *newly* detected milestones (not previously recorded).
    """
    from app.services.backbone import confidence_tracker, benchmark_ai

    existing_titles = {m.title for m in _milestones.get(user_id, [])}
    new_milestones: list[Milestone] = []

    # Check streak milestones
    momentum = confidence_tracker.get_momentum_state(user_id)
    for threshold in [3, 5, 10, 20]:
        milestone_title = f"{threshold}-game win streak"
        if (
            momentum.streak_type == "win"
            and momentum.streak_length >= threshold
            and milestone_title not in existing_titles
        ):
            ms = Milestone(
                user_id=user_id,
                category=MilestoneCategory.STREAK,
                title=milestone_title,
                description=f"Achieved a {threshold}-game win streak!",
                achieved_at=_now(),
                value=float(threshold),
            )
            new_milestones.append(ms)

    # Check game-count milestones
    games = confidence_tracker._game_history.get(user_id, [])
    for count in [10, 50, 100, 500, 1000]:
        milestone_title = f"{count} games played"
        if len(games) >= count and milestone_title not in existing_titles:
            ms = Milestone(
                user_id=user_id,
                category=MilestoneCategory.CONSISTENCY,
                title=milestone_title,
                description=f"Played {count} total games. Dedication pays off!",
                achieved_at=_now(),
                value=float(count),
            )
            new_milestones.append(ms)

    # Check percentile milestones per title
    titles_seen: set[str] = set()
    for g in games:
        t = g.get("title")
        if t:
            titles_seen.add(t)

    for title in titles_seen:
        scores = benchmark_ai.get_dimension_scores(user_id, title)
        for dim in ["read_speed", "user_defense", "clutch", "anti_meta", "execution", "mental"]:
            score = getattr(scores, dim)
            pct = benchmark_ai._score_to_percentile(dim, score)
            for target_pct in [90, 95, 99]:
                milestone_title = f"Top {100 - target_pct}% {dim.replace('_', ' ')}"
                if pct >= target_pct and milestone_title not in existing_titles:
                    ms = Milestone(
                        user_id=user_id,
                        category=MilestoneCategory.PERCENTILE,
                        title=milestone_title,
                        description=f"Reached top {100 - target_pct}% in {dim.replace('_', ' ')} on {title}.",
                        achieved_at=_now(),
                        value=float(pct),
                    )
                    new_milestones.append(ms)

    # Persist newly detected milestones
    for ms in new_milestones:
        add_milestone(user_id, ms)

    return new_milestones


def get_growth_trajectory(
    user_id: str,
    title: str,
    weeks: int = 4,
) -> GrowthTrajectory:
    """Return trend lines for key metrics over the specified number of weeks."""
    snapshots = _metric_history.get(user_id, {}).get(title, [])
    sliced = snapshots[-weeks:] if len(snapshots) >= weeks else snapshots

    if not sliced:
        return GrowthTrajectory(user_id=user_id, title=title, weeks=weeks)

    # Build trend dict: metric_name -> list of weekly values
    metric_keys = [
        k for k in sliced[0].keys()
        if k not in ("week", "recorded_at")
    ]
    trends: dict[str, list[float]] = {k: [] for k in metric_keys}
    for snap in sliced:
        for k in metric_keys:
            val = snap.get(k)
            if isinstance(val, (int, float)):
                trends[k].append(float(val))

    # Determine overall direction from average trend
    directions: list[float] = []
    for k, vals in trends.items():
        if len(vals) >= 2:
            directions.append(vals[-1] - vals[0])

    if directions:
        avg_dir = sum(directions) / len(directions)
        if avg_dir > 0.02:
            overall = MomentumDirection.RISING
        elif avg_dir < -0.02:
            overall = MomentumDirection.FALLING
        else:
            overall = MomentumDirection.STABLE
    else:
        overall = MomentumDirection.STABLE

    return GrowthTrajectory(
        user_id=user_id,
        title=title,
        weeks=len(sliced),
        trends=trends,
        overall_direction=overall,
    )


def generate_session_summary(user_id: str, session: str) -> SessionSummary:
    """Generate a post-game narrative from session data.

    Unlike raw stats, this produces a story: what happened, what stood out,
    and what to focus on next.
    """
    data = _session_data.get(user_id, {}).get(session, {})

    if not data:
        return SessionSummary(
            user_id=user_id,
            session_id=session,
            narrative="No session data found.",
        )

    wins = data.get("wins", 0)
    losses = data.get("losses", 0)
    total = wins + losses
    win_rate = wins / total if total > 0 else 0
    key_moments = data.get("key_moments", [])
    improvements = data.get("improvements", [])
    areas_to_work_on = data.get("areas_to_work_on", [])
    best_play = data.get("best_play", "")

    # Build narrative
    parts: list[str] = []
    if total > 0:
        if win_rate >= 0.7:
            parts.append(f"Dominant session — {wins}W-{losses}L.")
        elif win_rate >= 0.5:
            parts.append(f"Productive session with a {wins}W-{losses}L record.")
        else:
            parts.append(f"Challenging session at {wins}W-{losses}L.")

    if best_play:
        parts.append(f"Standout moment: {best_play}.")

    if improvements:
        parts.append(f"Growth areas this session: {', '.join(improvements)}.")

    if areas_to_work_on:
        parts.append(f"Focus next time on: {', '.join(areas_to_work_on)}.")

    if not parts:
        parts.append("Session completed. Keep building momentum.")

    performance = round(win_rate, 4) if total > 0 else 0.5

    return SessionSummary(
        user_id=user_id,
        session_id=session,
        narrative=" ".join(parts),
        performance_rating=performance,
        key_moments=key_moments,
        improvements=improvements,
        areas_to_work_on=areas_to_work_on,
    )


# ---------------------------------------------------------------------------
# Reset (for testing)
# ---------------------------------------------------------------------------

def _reset() -> None:
    """Clear all in-memory stores. For testing only."""
    _weekly_data.clear()
    _milestones.clear()
    _session_data.clear()
    _metric_history.clear()
