"""Confidence Tracker — evidence-based confidence, clutch stats, momentum, readiness.

All scores are derived from observable game data, not motivational heuristics.
The tracker maintains in-memory session history per user and computes metrics
on demand.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.schemas.mental import (
    ClutchPerformance,
    ConfidenceScore,
    MomentumDirection,
    MomentumState,
    PreGameReadiness,
    ReadinessLevel,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory stores (user_id -> data)
# ---------------------------------------------------------------------------
_game_history: dict[str, list[dict[str, Any]]] = {}
_session_history: dict[str, list[dict[str, Any]]] = {}
_practice_log: dict[str, list[dict[str, Any]]] = {}

# Weights for composite confidence
_CONF_WEIGHT_WINRATE = 0.30
_CONF_WEIGHT_CLUTCH = 0.25
_CONF_WEIGHT_CONSISTENCY = 0.20
_CONF_WEIGHT_FORM = 0.25

# Readiness weights
_READINESS_WEIGHT_CONFIDENCE = 0.30
_READINESS_WEIGHT_FATIGUE = 0.25
_READINESS_WEIGHT_PRACTICE = 0.20
_READINESS_WEIGHT_FORM = 0.25


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Data ingestion helpers
# ---------------------------------------------------------------------------

def record_game(user_id: str, game_data: dict[str, Any]) -> None:
    """Record a completed game for a user.

    ``game_data`` should include at minimum:
    - title: str
    - won: bool
    - clutch: bool (was this a high-pressure scenario)
    - close_game: bool
    - comeback: bool
    - timestamp: str (ISO format, optional)
    """
    _game_history.setdefault(user_id, []).append({
        **game_data,
        "recorded_at": _now().isoformat(),
    })


def record_session(user_id: str, session_data: dict[str, Any]) -> None:
    """Record a play session (may contain multiple games)."""
    _session_history.setdefault(user_id, []).append({
        **session_data,
        "recorded_at": _now().isoformat(),
    })


def record_practice(user_id: str, practice_data: dict[str, Any]) -> None:
    """Record a practice / lab session."""
    _practice_log.setdefault(user_id, []).append({
        **practice_data,
        "recorded_at": _now().isoformat(),
    })


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_confidence_score(user_id: str, title: str) -> ConfidenceScore:
    """Compute evidence-based confidence for *user_id* on *title*.

    The score is a weighted composite of:
    - 30-day win rate
    - Clutch conversion rate
    - Consistency (std-dev of recent performance)
    - Recent form (last 10 games weighted average)
    """
    games = [g for g in _game_history.get(user_id, []) if g.get("title") == title]
    sample = len(games)

    if sample == 0:
        return ConfidenceScore(
            user_id=user_id,
            title=title,
            overall=0.5,
            sample_size=0,
            computed_at=_now(),
        )

    # Win rate
    wins = sum(1 for g in games if g.get("won"))
    win_rate = wins / sample

    # Clutch rate
    clutch_games = [g for g in games if g.get("clutch")]
    clutch_rate = (
        sum(1 for g in clutch_games if g.get("won")) / len(clutch_games)
        if clutch_games
        else 0.5
    )

    # Consistency — measured as inverse of variance in recent win streaks
    recent = games[-20:] if len(games) >= 20 else games
    recent_outcomes = [1.0 if g.get("won") else 0.0 for g in recent]
    if len(recent_outcomes) >= 2:
        mean = sum(recent_outcomes) / len(recent_outcomes)
        variance = sum((x - mean) ** 2 for x in recent_outcomes) / len(recent_outcomes)
        consistency = max(0.0, 1.0 - variance)
    else:
        consistency = 0.5

    # Recent form — last 10 games, weighted toward most recent
    last_n = games[-10:] if len(games) >= 10 else games
    weights = list(range(1, len(last_n) + 1))
    total_weight = sum(weights)
    form = sum(
        w * (1.0 if g.get("won") else 0.0)
        for w, g in zip(weights, last_n)
    ) / total_weight if total_weight else 0.5

    overall = (
        _CONF_WEIGHT_WINRATE * win_rate
        + _CONF_WEIGHT_CLUTCH * clutch_rate
        + _CONF_WEIGHT_CONSISTENCY * consistency
        + _CONF_WEIGHT_FORM * form
    )
    overall = round(max(0.0, min(1.0, overall)), 4)

    return ConfidenceScore(
        user_id=user_id,
        title=title,
        overall=overall,
        win_rate_30d=round(win_rate, 4),
        clutch_rate=round(clutch_rate, 4),
        consistency=round(consistency, 4),
        recent_form=round(form, 4),
        sample_size=sample,
        computed_at=_now(),
    )


def track_clutch_performance(user_id: str) -> ClutchPerformance:
    """Aggregate clutch rates, pressure conversion, and comeback stats."""
    games = _game_history.get(user_id, [])
    clutch_games = [g for g in games if g.get("clutch")]
    close_games = [g for g in games if g.get("close_game")]

    clutch_wins = sum(1 for g in clutch_games if g.get("won"))
    clutch_rate = clutch_wins / len(clutch_games) if clutch_games else 0.0

    pressure_moments = len(clutch_games)
    pressure_conversion = clutch_rate  # same metric, different framing

    comeback_games = [g for g in games if g.get("comeback")]
    comeback_rate = (
        sum(1 for g in comeback_games if g.get("won")) / len(comeback_games)
        if comeback_games
        else 0.0
    )

    close_win_rate = (
        sum(1 for g in close_games if g.get("won")) / len(close_games)
        if close_games
        else 0.0
    )

    return ClutchPerformance(
        user_id=user_id,
        clutch_rate=round(clutch_rate, 4),
        clutch_games=len(clutch_games),
        total_pressure_moments=pressure_moments,
        pressure_conversion=round(pressure_conversion, 4),
        comeback_rate=round(comeback_rate, 4),
        close_game_win_rate=round(close_win_rate, 4),
    )


def get_momentum_state(user_id: str, session: str | None = None) -> MomentumState:
    """Determine current win/loss streak and recent form."""
    games = _game_history.get(user_id, [])
    if not games:
        return MomentumState(user_id=user_id, session_id=session)

    # Current streak
    streak_type = "win" if games[-1].get("won") else "loss"
    streak_val = games[-1].get("won")
    streak_length = 0
    for g in reversed(games):
        if g.get("won") == streak_val:
            streak_length += 1
        else:
            break

    # Recent results (last 10)
    recent = games[-10:]
    recent_results = [bool(g.get("won")) for g in recent]

    # Weighted form score
    weights = list(range(1, len(recent) + 1))
    total_weight = sum(weights)
    form_score = sum(
        w * (1.0 if g.get("won") else 0.0)
        for w, g in zip(weights, recent)
    ) / total_weight if total_weight else 0.5

    # Determine direction
    if streak_length >= 3 and streak_type == "win":
        direction = MomentumDirection.RISING
    elif streak_length >= 3 and streak_type == "loss":
        direction = MomentumDirection.FALLING
    elif len(recent) >= 4:
        wins_first_half = sum(1 for r in recent_results[: len(recent_results) // 2] if r)
        wins_second_half = sum(1 for r in recent_results[len(recent_results) // 2:] if r)
        half = len(recent_results) // 2
        if half > 0 and abs(wins_first_half - wins_second_half) <= 1:
            direction = MomentumDirection.STABLE
        elif wins_second_half > wins_first_half:
            direction = MomentumDirection.RISING
        else:
            direction = MomentumDirection.FALLING
    else:
        direction = MomentumDirection.STABLE

    return MomentumState(
        user_id=user_id,
        session_id=session,
        direction=direction,
        streak_length=streak_length,
        streak_type=streak_type,
        recent_results=recent_results,
        form_score=round(form_score, 4),
    )


def get_pre_game_readiness(user_id: str, title: str) -> PreGameReadiness:
    """Composite readiness: confidence + fatigue + practice + recent form."""
    confidence = get_confidence_score(user_id, title)
    momentum = get_momentum_state(user_id)

    # Fatigue — inverse of sessions in last 4 hours (more sessions = more tired)
    sessions = _session_history.get(user_id, [])
    recent_session_count = len(sessions[-4:]) if sessions else 0
    fatigue_factor = max(0.0, 1.0 - (recent_session_count * 0.2))

    # Practice factor — any practice in last 24h boosts readiness
    practice = _practice_log.get(user_id, [])
    practice_factor = min(1.0, len(practice) * 0.25) if practice else 0.0

    # Recent form from momentum
    form_factor = momentum.form_score

    composite = (
        _READINESS_WEIGHT_CONFIDENCE * confidence.overall
        + _READINESS_WEIGHT_FATIGUE * fatigue_factor
        + _READINESS_WEIGHT_PRACTICE * practice_factor
        + _READINESS_WEIGHT_FORM * form_factor
    )
    composite = round(max(0.0, min(1.0, composite)), 4)

    # Classify readiness level
    if composite >= 0.85:
        level = ReadinessLevel.PEAK
        recommendation = "You are in peak form. Great time for ranked play."
    elif composite >= 0.70:
        level = ReadinessLevel.READY
        recommendation = "Solid readiness. You should perform well."
    elif composite >= 0.50:
        level = ReadinessLevel.MODERATE
        recommendation = "Average readiness. Consider a warm-up session first."
    elif composite >= 0.30:
        level = ReadinessLevel.FATIGUED
        recommendation = "Signs of fatigue detected. A break or light practice may help."
    else:
        level = ReadinessLevel.LOW
        recommendation = "Low readiness. Rest and recovery recommended before competitive play."

    return PreGameReadiness(
        user_id=user_id,
        title=title,
        level=level,
        composite_score=composite,
        confidence_factor=round(confidence.overall, 4),
        fatigue_factor=round(fatigue_factor, 4),
        practice_factor=round(practice_factor, 4),
        recent_form_factor=round(form_factor, 4),
        recommendation=recommendation,
    )


# ---------------------------------------------------------------------------
# Reset (for testing)
# ---------------------------------------------------------------------------

def _reset() -> None:
    """Clear all in-memory stores. For testing only."""
    _game_history.clear()
    _session_history.clear()
    _practice_log.clear()
