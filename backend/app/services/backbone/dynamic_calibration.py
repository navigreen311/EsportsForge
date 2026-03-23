"""Dynamic Calibration Engine — auto-calibrates training difficulty.

Keeps every drill and training tool sitting just above the player's current
ceiling.  Not too easy (coasting), not impossible (frustration).  Targets
approximately 70% success rate — the optimal challenge point for skill
acquisition.
"""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone

from app.schemas.simulation import (
    CalibrationConfig,
    CalibrationDirection,
    CalibrationLevel,
    DifficultyAdjustment,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TARGET_SUCCESS_RATE = 0.70
_COASTING_THRESHOLD = 0.90       # Success rate above this → too easy
_FRUSTRATION_THRESHOLD = 0.40    # Success rate below this → too hard
_MIN_REPS_FOR_DETECTION = 5      # Need at least this many reps to judge
_STREAK_BUMP_THRESHOLD = 5       # Consecutive successes → bump up
_STREAK_DIAL_THRESHOLD = 3       # Consecutive failures → dial back
_DIFFICULTY_STEP = 0.05          # Standard adjustment increment
_MAX_HISTORY = 50                # Rolling window for success-rate calc

# Ordered levels for promotion / demotion
_LEVEL_ORDER: list[CalibrationLevel] = [
    CalibrationLevel.BEGINNER,
    CalibrationLevel.DEVELOPING,
    CalibrationLevel.INTERMEDIATE,
    CalibrationLevel.ADVANCED,
    CalibrationLevel.ELITE,
    CalibrationLevel.MASTER,
]

_LEVEL_DIFFICULTY_RANGES: dict[CalibrationLevel, tuple[float, float]] = {
    CalibrationLevel.BEGINNER:      (0.00, 0.15),
    CalibrationLevel.DEVELOPING:    (0.15, 0.30),
    CalibrationLevel.INTERMEDIATE:  (0.30, 0.55),
    CalibrationLevel.ADVANCED:      (0.55, 0.75),
    CalibrationLevel.ELITE:         (0.75, 0.90),
    CalibrationLevel.MASTER:        (0.90, 1.00),
}

# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

# (user_id, skill) -> CalibrationConfig
_calibrations: dict[tuple[str, str], CalibrationConfig] = {}

# (user_id, skill) -> rolling history of bool (True=success, False=fail)
_history: dict[tuple[str, str], deque[bool]] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _level_index(level: CalibrationLevel) -> int:
    return _LEVEL_ORDER.index(level)


def _level_for_difficulty(difficulty: float) -> CalibrationLevel:
    """Map a continuous difficulty value to a discrete level."""
    for lvl in reversed(_LEVEL_ORDER):
        lo, _ = _LEVEL_DIFFICULTY_RANGES[lvl]
        if difficulty >= lo:
            return lvl
    return CalibrationLevel.BEGINNER


def _get_or_create(user_id: str, skill: str) -> CalibrationConfig:
    key = (user_id, skill)
    if key not in _calibrations:
        _calibrations[key] = CalibrationConfig(
            user_id=user_id,
            skill=skill,
            level=CalibrationLevel.INTERMEDIATE,
            difficulty_value=0.40,
            target_success_rate=_TARGET_SUCCESS_RATE,
            current_success_rate=0.0,
            updated_at=_now(),
        )
        _history[key] = deque(maxlen=_MAX_HISTORY)
    return _calibrations[key]


def _success_rate(key: tuple[str, str]) -> float:
    """Compute rolling success rate from history."""
    hist = _history.get(key, deque())
    if not hist:
        return 0.0
    return sum(1 for r in hist if r) / len(hist)


def _clamp(val: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, val))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def calibrate(user_id: str, skill: str, current_ceiling: float) -> CalibrationConfig:
    """Set difficulty just above the player's current ceiling.

    Parameters
    ----------
    user_id:
        Player identifier.
    skill:
        Skill dimension, e.g. 'zone_read', 'user_blitz'.
    current_ceiling:
        Player's measured execution ceiling for this skill (0-1).

    Returns
    -------
    CalibrationConfig
        Updated calibration state.
    """
    cfg = _get_or_create(user_id, skill)
    # Target: just above ceiling, scaled toward 70% success expectation
    new_diff = _clamp(current_ceiling + _DIFFICULTY_STEP)
    cfg.difficulty_value = round(new_diff, 4)
    cfg.level = _level_for_difficulty(new_diff)
    cfg.target_success_rate = _TARGET_SUCCESS_RATE
    cfg.updated_at = _now()

    logger.info(
        "Calibrated %s/%s: ceiling=%.2f → difficulty=%.2f (%s)",
        user_id, skill, current_ceiling, new_diff, cfg.level.value,
    )
    return cfg


def get_calibration_level(user_id: str, skill: str) -> CalibrationConfig:
    """Return current calibration config for a user + skill."""
    return _get_or_create(user_id, skill)


def adjust_after_rep(user_id: str, skill: str, success: bool) -> DifficultyAdjustment:
    """Adjust difficulty after a single training rep.

    Increases difficulty on success streaks, decreases on failure streaks,
    and makes micro-adjustments otherwise.

    Parameters
    ----------
    user_id:
        Player identifier.
    skill:
        Skill dimension.
    success:
        Whether the rep was completed successfully.

    Returns
    -------
    DifficultyAdjustment
        Details of the change.
    """
    cfg = _get_or_create(user_id, skill)
    key = (user_id, skill)
    _history.setdefault(key, deque(maxlen=_MAX_HISTORY)).append(success)

    prev_diff = cfg.difficulty_value
    prev_level = cfg.level

    # Update streaks
    if success:
        cfg.streak_successes += 1
        cfg.streak_failures = 0
    else:
        cfg.streak_failures += 1
        cfg.streak_successes = 0

    cfg.total_reps += 1
    cfg.reps_at_level += 1
    cfg.current_success_rate = round(_success_rate(key), 4)

    # Determine adjustment
    direction = CalibrationDirection.HOLD
    reason = "No adjustment needed."
    step = 0.0

    if cfg.streak_successes >= _STREAK_BUMP_THRESHOLD:
        step = _DIFFICULTY_STEP * 1.5
        direction = CalibrationDirection.UP
        reason = f"Success streak of {cfg.streak_successes} — bumping up."
        cfg.streak_successes = 0
        cfg.reps_at_level = 0
    elif cfg.streak_failures >= _STREAK_DIAL_THRESHOLD:
        step = -_DIFFICULTY_STEP * 1.5
        direction = CalibrationDirection.DOWN
        reason = f"Failure streak of {cfg.streak_failures} — dialing back."
        cfg.streak_failures = 0
        cfg.reps_at_level = 0
    elif success:
        step = _DIFFICULTY_STEP * 0.3
        direction = CalibrationDirection.UP
        reason = "Single success — micro-increase."
    else:
        step = -_DIFFICULTY_STEP * 0.3
        direction = CalibrationDirection.DOWN
        reason = "Single failure — micro-decrease."

    cfg.difficulty_value = round(_clamp(cfg.difficulty_value + step), 4)
    cfg.level = _level_for_difficulty(cfg.difficulty_value)
    cfg.updated_at = _now()

    adjustment = DifficultyAdjustment(
        user_id=user_id,
        skill=skill,
        previous_difficulty=prev_diff,
        new_difficulty=cfg.difficulty_value,
        previous_level=prev_level,
        new_level=cfg.level,
        direction=direction,
        reason=reason,
    )
    logger.info(
        "Adjusted %s/%s: %.4f → %.4f (%s) — %s",
        user_id, skill, prev_diff, cfg.difficulty_value, direction.value, reason,
    )
    return adjustment


def detect_coasting(user_id: str, skill: str) -> bool:
    """Detect whether the player is coasting (success rate too high).

    Returns True if the player's rolling success rate exceeds the coasting
    threshold with enough reps to be meaningful.
    """
    key = (user_id, skill)
    hist = _history.get(key, deque())
    if len(hist) < _MIN_REPS_FOR_DETECTION:
        return False
    rate = _success_rate(key)
    is_coasting = rate >= _COASTING_THRESHOLD
    if is_coasting:
        logger.info("Coasting detected for %s/%s: success rate %.0f%%", user_id, skill, rate * 100)
    return is_coasting


def detect_frustration(user_id: str, skill: str) -> bool:
    """Detect whether the player is frustrated (success rate too low).

    Returns True if the rolling success rate falls below the frustration
    threshold with enough reps to be meaningful.
    """
    key = (user_id, skill)
    hist = _history.get(key, deque())
    if len(hist) < _MIN_REPS_FOR_DETECTION:
        return False
    rate = _success_rate(key)
    is_frustrated = rate <= _FRUSTRATION_THRESHOLD
    if is_frustrated:
        logger.info("Frustration detected for %s/%s: success rate %.0f%%", user_id, skill, rate * 100)
    return is_frustrated


def get_optimal_challenge_point(success_rate_history: list[float]) -> float:
    """Compute the optimal difficulty to target ~70% success rate.

    Analyzes a history of success rates at various difficulty levels and
    returns the difficulty value most likely to produce the target rate.

    Parameters
    ----------
    success_rate_history:
        List of recent success rates (0-1), ordered oldest → newest.

    Returns
    -------
    float
        Recommended difficulty value (0-1).
    """
    if not success_rate_history:
        return 0.40  # Safe default

    recent = success_rate_history[-10:]  # Focus on recent data
    avg_rate = sum(recent) / len(recent)

    # If average is above target, player can handle more
    # If below, pull back
    delta = avg_rate - _TARGET_SUCCESS_RATE
    # The further from target, the larger the correction
    correction = delta * 0.5

    # Start from a mid-range difficulty and adjust
    optimal = _clamp(0.50 + correction)
    logger.info(
        "Optimal challenge point: avg_rate=%.2f, delta=%.2f, optimal=%.4f",
        avg_rate, delta, optimal,
    )
    return round(optimal, 4)
