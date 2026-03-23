"""Behavioral Signal Agent — Read non-gameplay signals from opponents.

Detects timeout patterns, pace changes, formation/substitution patterns,
and other behavioral cues that reveal an opponent's mental state and
strategic adjustments.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.opponent import (
    BehavioralSignal,
    PaceChange,
    SignalType,
    SubPattern,
    TimeoutPattern,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read_signals(game_state: dict[str, Any]) -> list[BehavioralSignal]:
    """Read all detectable behavioral signals from the current game state.

    Parameters
    ----------
    game_state:
        Dict with keys like ``timeouts_called``, ``play_clock_usage``,
        ``formation_changes``, ``substitutions``, ``pace_history``,
        ``score_differential``, ``game_phase``.
    """
    signals: list[BehavioralSignal] = []

    # --- Timeout signal ---
    timeouts = game_state.get("timeouts_called", [])
    if timeouts:
        pattern = detect_timeout_pattern({"timeouts": timeouts})
        if pattern.panic_timeout_ratio > 0.5:
            signals.append(
                BehavioralSignal(
                    signal_type=SignalType.TIMEOUT,
                    intensity=pattern.panic_timeout_ratio,
                    description=f"High panic-timeout ratio ({pattern.panic_timeout_ratio:.0%})",
                    actionable=True,
                    suggested_response="Opponent is flustered — increase pressure.",
                )
            )
        elif pattern.total_timeouts > 0:
            signals.append(
                BehavioralSignal(
                    signal_type=SignalType.TIMEOUT,
                    intensity=0.3,
                    description=f"Strategic timeout usage ({pattern.total_timeouts} called)",
                    actionable=False,
                    suggested_response="No immediate exploit — monitor for panic.",
                )
            )

    # --- Pace change signal ---
    pace_history = game_state.get("pace_history", [])
    if pace_history:
        flow = {"pace_history": pace_history, "game_phase": game_state.get("game_phase", "")}
        pace = detect_pace_change(flow)
        if pace.detected:
            signals.append(
                BehavioralSignal(
                    signal_type=SignalType.PACE_CHANGE,
                    intensity=pace.magnitude,
                    description=f"Pace {pace.direction} — {pace.likely_reason}",
                    actionable=pace.magnitude > 0.4,
                    suggested_response=_pace_response(pace),
                )
            )

    # --- Formation / substitution signal ---
    formation_changes = game_state.get("formation_changes", [])
    substitutions = game_state.get("substitutions", [])
    if formation_changes or substitutions:
        history = {
            "formation_changes": formation_changes,
            "substitutions": substitutions,
        }
        sub_pat = detect_formation_sub_pattern(history)
        if sub_pat.detected:
            signals.append(
                BehavioralSignal(
                    signal_type=SignalType.FORMATION_SHIFT
                    if sub_pat.pattern_type == "formation"
                    else SignalType.SUBSTITUTION,
                    intensity=sub_pat.frequency,
                    description=sub_pat.description,
                    actionable=sub_pat.frequency > 0.3,
                    suggested_response=f"Watch for {sub_pat.trigger_situation}.",
                )
            )

    # --- Tilt / aggression signal ---
    score_diff = game_state.get("score_differential", 0)
    turnovers = game_state.get("recent_turnovers", 0)
    if score_diff < -14 or turnovers >= 2:
        tilt_intensity = min(1.0, (abs(score_diff) / 28 + turnovers / 4))
        signals.append(
            BehavioralSignal(
                signal_type=SignalType.TILT,
                intensity=round(tilt_intensity, 3),
                description="Opponent may be tilting after turnovers/deficit.",
                actionable=True,
                suggested_response="Exploit tilt — they may force risky plays.",
            )
        )

    return signals


def detect_timeout_pattern(opponent_history: dict[str, Any]) -> TimeoutPattern:
    """Analyse timeout usage patterns from opponent history.

    Parameters
    ----------
    opponent_history:
        ``{"timeouts": [{"game_time_pct": float, "under_pressure": bool}, ...]}``
    """
    timeouts: list[dict[str, Any]] = opponent_history.get("timeouts", [])
    if not timeouts:
        return TimeoutPattern()

    total = len(timeouts)
    avg_time = sum(t.get("game_time_pct", 0.5) for t in timeouts) / total
    panic_count = sum(1 for t in timeouts if t.get("under_pressure", False))
    panic_ratio = panic_count / total

    if panic_ratio > 0.6:
        desc = "Predominantly panic-driven — called under pressure"
    elif panic_ratio < 0.3:
        desc = "Strategic timeouts — called proactively"
    else:
        desc = "Mixed timeout usage"

    return TimeoutPattern(
        total_timeouts=total,
        avg_game_time_when_called=round(avg_time, 3),
        panic_timeout_ratio=round(panic_ratio, 3),
        pattern_description=desc,
    )


def detect_pace_change(game_flow: dict[str, Any]) -> PaceChange:
    """Detect whether the opponent is changing pace.

    Parameters
    ----------
    game_flow:
        ``{"pace_history": [float, ...], "game_phase": str}``
        where each float in pace_history represents seconds between plays.
    """
    paces: list[float] = game_flow.get("pace_history", [])
    phase: str = game_flow.get("game_phase", "")

    if len(paces) < 3:
        return PaceChange()

    recent_avg = sum(paces[-3:]) / 3
    earlier_avg = sum(paces[:-3]) / max(len(paces) - 3, 1)

    if earlier_avg == 0:
        return PaceChange()

    change_ratio = (recent_avg - earlier_avg) / earlier_avg

    if abs(change_ratio) < 0.15:
        return PaceChange()

    direction = "slower" if change_ratio > 0 else "faster"
    magnitude = min(1.0, abs(change_ratio))

    if direction == "faster":
        reason = "Opponent speeding up — possible hurry-up / desperation"
    else:
        reason = "Opponent slowing down — possible clock management / regrouping"

    return PaceChange(
        detected=True,
        direction=direction,
        magnitude=round(magnitude, 3),
        likely_reason=reason,
        game_phase=phase,
    )


def detect_formation_sub_pattern(history: dict[str, Any]) -> SubPattern:
    """Detect formation or substitution patterns.

    Parameters
    ----------
    history:
        ``{"formation_changes": [{"from": str, "to": str, "situation": str}, ...],
          "substitutions": [{"player_in": str, "player_out": str, "situation": str}, ...]}``
    """
    formations: list[dict[str, Any]] = history.get("formation_changes", [])
    subs: list[dict[str, Any]] = history.get("substitutions", [])

    # Check formation pattern
    if len(formations) >= 2:
        situations = [f.get("situation", "") for f in formations]
        # Check if same situation triggers formation changes
        from collections import Counter
        sit_counts = Counter(situations)
        most_common_sit, count = sit_counts.most_common(1)[0]
        if count >= 2 and most_common_sit:
            freq = count / len(formations)
            return SubPattern(
                detected=True,
                pattern_type="formation",
                description=(
                    f"Formation change triggered by '{most_common_sit}' "
                    f"({count}/{len(formations)} times)"
                ),
                frequency=round(freq, 3),
                trigger_situation=most_common_sit,
            )

    # Check substitution pattern
    if len(subs) >= 2:
        situations = [s.get("situation", "") for s in subs]
        from collections import Counter
        sit_counts = Counter(situations)
        most_common_sit, count = sit_counts.most_common(1)[0]
        if count >= 2 and most_common_sit:
            freq = count / len(subs)
            return SubPattern(
                detected=True,
                pattern_type="substitution",
                description=(
                    f"Substitution triggered by '{most_common_sit}' "
                    f"({count}/{len(subs)} times)"
                ),
                frequency=round(freq, 3),
                trigger_situation=most_common_sit,
            )

    return SubPattern()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pace_response(pace: PaceChange) -> str:
    """Suggest a response to a pace change."""
    if pace.direction == "faster":
        return "Match tempo or slow down to disrupt their rhythm."
    if pace.direction == "slower":
        return "Speed up to prevent them from regrouping."
    return "No pace adjustment needed."
