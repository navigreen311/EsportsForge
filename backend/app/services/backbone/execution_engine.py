"""Execution Engine — reliability scoring across skills, pressure, and game modes.

Measures what a player can *actually* do, not what they theoretically know.
Tracks the gap between practice-mode performance and ranked/tournament execution.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.schemas.player_twin import (
    ExecutionScore,
    GameMode,
    PressureDifferential,
    PressureLevel,
    SessionData,
    TransferRate,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal storage type (will be replaced by DB in production)
# ---------------------------------------------------------------------------
# user_id -> title -> skill -> list of (score, is_pressure, mode, ts)
_Observation = tuple[float, bool, GameMode, datetime]
_SkillLog = dict[str, dict[str, dict[str, list[_Observation]]]]

_store: _SkillLog = {}

# Minimum observations before we produce a score
_MIN_SAMPLE = 3


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_path(user_id: str, title: str, skill: str) -> list[_Observation]:
    """Return (and lazily create) the observation list for a skill."""
    _store.setdefault(user_id, {})
    _store[user_id].setdefault(title, {})
    _store[user_id][title].setdefault(skill, [])
    return _store[user_id][title][skill]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ingest_session(user_id: str, session: SessionData) -> None:
    """Extract skill observations from a completed session and store them."""
    title = session.title
    mode = session.mode
    ts = session.recorded_at or _now()

    # Skill events carry per-skill success/failure signals
    for evt in session.skill_events:
        skill = evt.get("skill", "unknown")
        success = float(evt.get("success", 0))
        is_pressure = evt.get("pressure", False)
        obs_list = _ensure_path(user_id, title, skill)
        obs_list.append((success, bool(is_pressure), mode, ts))

    # Pressure moments are macro-level clutch observations
    for pm in session.pressure_moments:
        skill = pm.get("skill", "clutch_general")
        outcome = float(pm.get("outcome", 0))
        obs_list = _ensure_path(user_id, title, skill)
        obs_list.append((outcome, True, mode, ts))

    logger.info(
        "ExecutionEngine ingested session %s for user=%s title=%s (%d skill_events, %d pressure_moments)",
        session.session_id,
        user_id,
        title,
        len(session.skill_events),
        len(session.pressure_moments),
    )


def score_execution(user_id: str, title: str, skill_dimension: str) -> ExecutionScore:
    """Compute a reliability score for a single skill dimension.

    Returns a score between 0 and 1 representing how reliably the player
    executes this skill, along with the pressure-specific sub-score and trend.
    """
    obs = _ensure_path(user_id, title, skill_dimension)

    if not obs:
        return ExecutionScore(
            skill=skill_dimension,
            title=title,
            score=0.0,
            sample_size=0,
            pressure_score=0.0,
            trend=0.0,
            last_updated=_now(),
        )

    scores = [o[0] for o in obs]
    pressure_scores = [o[0] for o in obs if o[1]]
    avg = sum(scores) / len(scores)
    pressure_avg = (sum(pressure_scores) / len(pressure_scores)) if pressure_scores else avg

    # Trend: compare most recent half to first half
    trend = 0.0
    if len(scores) >= 4:
        mid = len(scores) // 2
        first_half = sum(scores[:mid]) / mid
        second_half = sum(scores[mid:]) / (len(scores) - mid)
        trend = round(second_half - first_half, 4)

    return ExecutionScore(
        skill=skill_dimension,
        title=title,
        score=round(avg, 4),
        sample_size=len(scores),
        pressure_score=round(pressure_avg, 4),
        trend=trend,
        last_updated=_now(),
    )


def get_all_scores(user_id: str, title: str) -> list[ExecutionScore]:
    """Return execution scores for every tracked skill in a title."""
    skills = _store.get(user_id, {}).get(title, {})
    return [score_execution(user_id, title, skill) for skill in skills]


def get_pressure_differential(user_id: str, title: str) -> PressureDifferential:
    """Compute the gap between normal and pressure execution across all skills.

    A negative differential means the player performs worse under pressure.
    The clutch_rating is a 0-1 composite: 1.0 means no drop-off (or improvement).
    """
    skills = _store.get(user_id, {}).get(title, {})
    if not skills:
        return PressureDifferential(title=title)

    normal_scores: list[float] = []
    pressure_scores: list[float] = []

    for obs_list in skills.values():
        for score_val, is_pressure, _mode, _ts in obs_list:
            if is_pressure:
                pressure_scores.append(score_val)
            else:
                normal_scores.append(score_val)

    normal_avg = (sum(normal_scores) / len(normal_scores)) if normal_scores else 0.0
    pressure_avg = (sum(pressure_scores) / len(pressure_scores)) if pressure_scores else 0.0
    diff = pressure_avg - normal_avg

    # Clutch rating: 1.0 if no drop-off, scales down with larger negative diffs
    clutch = max(0.0, min(1.0, 1.0 + diff))

    return PressureDifferential(
        title=title,
        normal_avg=round(normal_avg, 4),
        pressure_avg=round(pressure_avg, 4),
        differential=round(diff, 4),
        clutch_rating=round(clutch, 4),
    )


def get_transfer_rate(
    user_id: str,
    skill: str,
    from_mode: GameMode,
    to_mode: GameMode,
) -> TransferRate:
    """Measure how well a skill transfers from one game mode to another.

    E.g. lab -> ranked tells you if practice translates to real games.
    A rate of 1.0 means perfect transfer; < 1.0 means degradation.
    """
    all_titles = _store.get(user_id, {})
    from_scores: list[float] = []
    to_scores: list[float] = []

    for title_skills in all_titles.values():
        obs = title_skills.get(skill, [])
        for score_val, _pressure, mode, _ts in obs:
            if mode == from_mode:
                from_scores.append(score_val)
            elif mode == to_mode:
                to_scores.append(score_val)

    if not from_scores or not to_scores:
        return TransferRate(
            skill=skill,
            from_mode=from_mode,
            to_mode=to_mode,
            rate=0.0,
            sample_size=0,
        )

    from_avg = sum(from_scores) / len(from_scores)
    to_avg = sum(to_scores) / len(to_scores)

    rate = (to_avg / from_avg) if from_avg > 0 else 0.0
    rate = min(rate, 1.0)  # cap at 1.0

    return TransferRate(
        skill=skill,
        from_mode=from_mode,
        to_mode=to_mode,
        rate=round(rate, 4),
        sample_size=min(len(from_scores), len(to_scores)),
    )


# ---------------------------------------------------------------------------
# Helpers (testing / reset)
# ---------------------------------------------------------------------------

def reset_store() -> None:
    """Clear all in-memory observations. For testing only."""
    _store.clear()
