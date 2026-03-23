"""Predictive Fatigue Model — cognitive load prediction and decline detection.

Uses session history and time-of-day patterns to predict when a player will
experience cognitive decline and recommends optimal session lengths and
tournament-day scheduling.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from app.schemas.mental import (
    DeclineReport,
    FatigueLevel,
    SessionRecommendation,
    TournamentDayPlan,
)


# ---------------------------------------------------------------------------
# In-memory stores (replaced by DB in production)
# ---------------------------------------------------------------------------
_session_history: dict[str, list[dict]] = {}


# ---------------------------------------------------------------------------
# Constants / thresholds
# ---------------------------------------------------------------------------
_DEFAULT_OPTIMAL_MINUTES = 90
_DEFAULT_MAX_MINUTES = 150
_DEFAULT_BREAK_INTERVAL = 30
_DECLINE_REACTION_THRESHOLD = 1.2   # 20% slower than baseline
_DECLINE_ERROR_THRESHOLD = 1.3      # 30% more errors than baseline

# Circadian rhythm modifier — performance multiplier by hour bracket
_CIRCADIAN: dict[str, float] = {
    "early_morning": 0.7,   # 05-08
    "morning": 0.9,         # 08-11
    "midday": 1.0,          # 11-14
    "afternoon": 0.95,      # 14-17
    "evening": 0.85,        # 17-20
    "night": 0.7,           # 20-23
    "late_night": 0.5,      # 23-05
}


def _hour_to_bracket(hour: int) -> str:
    """Map a 0-23 hour to a circadian bracket name."""
    if 5 <= hour < 8:
        return "early_morning"
    if 8 <= hour < 11:
        return "morning"
    if 11 <= hour < 14:
        return "midday"
    if 14 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 20:
        return "evening"
    if 20 <= hour < 23:
        return "night"
    return "late_night"


# ---------------------------------------------------------------------------
# Fatigue Model service
# ---------------------------------------------------------------------------

class FatigueModel:
    """Predictive fatigue modelling for esports players."""

    # -- Fatigue prediction -------------------------------------------------

    @staticmethod
    def predict_fatigue(
        user_id: str,
        session_length_minutes: int,
        time_of_day: int = 12,
    ) -> FatigueLevel:
        """Predict cognitive fatigue level given session length and time.

        Combines session duration with circadian rhythm data to estimate
        current fatigue level.

        Parameters
        ----------
        user_id:
            Player identifier.
        session_length_minutes:
            How long the session has been running (minutes).
        time_of_day:
            Hour of day (0-23).

        Returns
        -------
        FatigueLevel enum value.
        """
        bracket = _hour_to_bracket(time_of_day)
        circadian_mod = _CIRCADIAN.get(bracket, 0.8)

        # Base fatigue grows with session length (diminishing returns curve)
        base_fatigue = 1 - math.exp(-session_length_minutes / 120.0)

        # Adjust for circadian rhythm (lower modifier = faster fatigue)
        adjusted = base_fatigue / circadian_mod

        # Check user history for personal fatigue curve
        history = _session_history.get(user_id, [])
        if history:
            avg_decline_point = sum(
                h.get("decline_at_minutes", 90) for h in history
            ) / len(history)
            personal_factor = session_length_minutes / max(avg_decline_point, 1)
            adjusted = max(adjusted, personal_factor * 0.5)

        adjusted = min(adjusted, 1.0)

        if adjusted < 0.2:
            return FatigueLevel.FRESH
        if adjusted < 0.4:
            return FatigueLevel.MILD
        if adjusted < 0.6:
            return FatigueLevel.MODERATE
        if adjusted < 0.8:
            return FatigueLevel.SEVERE
        return FatigueLevel.CRITICAL

    # -- Optimal session length ---------------------------------------------

    @staticmethod
    def get_optimal_session_length(user_id: str) -> SessionRecommendation:
        """Recommend session duration based on historical decline patterns.

        Analyses past sessions to find the average point where performance
        begins to drop, then recommends stopping *before* that point.
        """
        history = _session_history.get(user_id, [])

        if not history:
            return SessionRecommendation(
                user_id=user_id,
                optimal_minutes=_DEFAULT_OPTIMAL_MINUTES,
                max_before_decline=_DEFAULT_MAX_MINUTES,
                suggested_break_interval=_DEFAULT_BREAK_INTERVAL,
                reasoning="No session history — using population defaults.",
            )

        decline_points = [h.get("decline_at_minutes", 90) for h in history]
        avg_decline = sum(decline_points) / len(decline_points)

        # Recommend 80 % of the decline point as optimal
        optimal = int(avg_decline * 0.8)
        max_before = int(avg_decline)
        break_interval = max(15, optimal // 3)

        return SessionRecommendation(
            user_id=user_id,
            optimal_minutes=optimal,
            max_before_decline=max_before,
            suggested_break_interval=break_interval,
            reasoning=(
                f"Based on {len(history)} sessions, performance typically "
                f"declines around {max_before} min. Optimal stop at {optimal} min."
            ),
        )

    # -- Tournament-day planning --------------------------------------------

    @staticmethod
    def model_tournament_day(
        user_id: str,
        schedule: list[dict[str, Any]],
    ) -> TournamentDayPlan:
        """Build a peak-performance plan for a tournament day.

        *schedule* is a list of dicts with keys:
        - ``start_hour`` (int 0-23)
        - ``duration_minutes`` (int)
        - ``label`` (str, e.g. "Match 1")

        Returns a plan with peak/rest windows and warm-up advice.
        """
        peak_windows: list[dict] = []
        rest_windows: list[dict] = []
        total_play = 0

        for entry in schedule:
            start = entry.get("start_hour", 12)
            dur = entry.get("duration_minutes", 60)
            label = entry.get("label", "Match")
            bracket = _hour_to_bracket(start)
            modifier = _CIRCADIAN.get(bracket, 0.8)

            window = {
                "label": label,
                "start_hour": start,
                "duration_minutes": dur,
                "circadian_quality": modifier,
                "fatigue_risk": FatigueModel.predict_fatigue(
                    user_id, dur, start
                ).value,
            }
            peak_windows.append(window)
            total_play += dur

        # Insert rest windows between matches
        for i in range(len(schedule) - 1):
            end_of_current = schedule[i].get("start_hour", 12)
            start_of_next = schedule[i + 1].get("start_hour", 12)
            gap_hours = start_of_next - end_of_current
            if gap_hours > 0:
                rest_windows.append({
                    "after": schedule[i].get("label", f"Match {i+1}"),
                    "duration_minutes": gap_hours * 60,
                    "suggestion": "Light stretching, hydration, mental reset.",
                })

        warmup = (
            "15-minute aim trainer or practice mode, followed by "
            "2 minutes of breathing exercises."
        )

        return TournamentDayPlan(
            user_id=user_id,
            peak_windows=peak_windows,
            rest_windows=rest_windows,
            warmup_plan=warmup,
            total_play_minutes=total_play,
            notes="Stay hydrated. Avoid heavy meals 1h before matches.",
        )

    # -- Real-time decline detection ----------------------------------------

    @staticmethod
    def detect_cognitive_decline(
        session_metrics: dict[str, Any],
    ) -> DeclineReport:
        """Detect real-time cognitive decline from session metrics.

        Looks at trending reaction time and error rate relative to
        session-start baselines.

        *session_metrics* should contain:
        - ``reaction_time_ms`` (float)
        - ``baseline_reaction_ms`` (float)
        - ``error_rate`` (float 0-1)
        - ``baseline_error_rate`` (float 0-1)
        - ``session_elapsed_minutes`` (int)
        """
        affected: list[str] = []

        rt = session_metrics.get("reaction_time_ms", 0)
        brt = session_metrics.get("baseline_reaction_ms", rt)
        if brt > 0 and rt / brt >= _DECLINE_REACTION_THRESHOLD:
            affected.append("reaction_time")

        err = session_metrics.get("error_rate", 0)
        berr = session_metrics.get("baseline_error_rate", err)
        if berr > 0 and err / berr >= _DECLINE_ERROR_THRESHOLD:
            affected.append("error_rate")

        is_declining = len(affected) > 0
        elapsed = session_metrics.get("session_elapsed_minutes", 0)

        # Estimate decline rate (how fast metrics are degrading per minute)
        decline_rate = 0.0
        if is_declining and elapsed > 0:
            rt_ratio = (rt / brt - 1.0) if brt > 0 else 0
            decline_rate = round(rt_ratio / max(elapsed, 1), 4)

        # Estimate minutes until critical
        minutes_until_critical = None
        if decline_rate > 0:
            # Critical = 50 % degradation from baseline
            remaining_degradation = 0.5 - (rt / brt - 1.0) if brt > 0 else 0
            if remaining_degradation > 0:
                minutes_until_critical = round(remaining_degradation / decline_rate, 1)

        if is_declining:
            rec = "Cognitive decline detected. Consider a break soon."
        else:
            rec = "Performance metrics are stable."

        return DeclineReport(
            is_declining=is_declining,
            decline_rate=decline_rate,
            minutes_until_critical=minutes_until_critical,
            affected_metrics=affected,
            recommendation=rec,
        )

    # -- History recording (utility) ----------------------------------------

    @staticmethod
    def record_session(user_id: str, session_data: dict[str, Any]) -> None:
        """Store a completed session for future fatigue predictions."""
        _session_history.setdefault(user_id, []).append(session_data)
