"""TiltGuard — real-time tilt detection, mental check-ins, and interventions.

Monitors player emotional and cognitive state during sessions, differentiates
between tilt (emotional) and fatigue (cognitive decline), and triggers
context-appropriate interventions.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.schemas.mental import (
    CheckinResult,
    Intervention,
    InterventionKind,
    PeakHours,
    TiltEvent,
    TiltOrFatigue,
    TiltStatus,
    TiltType,
)


# ---------------------------------------------------------------------------
# In-memory stores (replaced by DB in production)
# ---------------------------------------------------------------------------
_checkin_store: dict[str, list[CheckinResult]] = {}
_tilt_history: dict[str, list[TiltEvent]] = {}
_session_metrics_store: dict[str, list[dict]] = {}


# ---------------------------------------------------------------------------
# Constants / thresholds
# ---------------------------------------------------------------------------
_TILT_WIN_RATE_DROP = 0.15          # >=15 % drop signals possible tilt
_TILT_ERROR_SPIKE_FACTOR = 1.5      # errors 1.5x baseline
_FATIGUE_REACTION_INCREASE = 1.3    # reaction time 30 % slower than baseline
_FATIGUE_DECISION_DROP = 0.20       # decision accuracy drops 20 %

_RISK_THRESHOLDS = {"low": 6.0, "medium": 4.0}  # mood+energy avg


# ---------------------------------------------------------------------------
# TiltGuard service
# ---------------------------------------------------------------------------

class TiltGuard:
    """Player mental-state monitoring and intervention engine."""

    # -- Pre-session check-in -----------------------------------------------

    @staticmethod
    def pre_session_checkin(
        user_id: str,
        mood: float = 5.0,
        energy: float = 5.0,
    ) -> CheckinResult:
        """Ask mood/energy questions and return a risk assessment.

        Parameters
        ----------
        user_id:
            Player identifier.
        mood:
            Self-reported mood on a 0-10 scale.
        energy:
            Self-reported energy on a 0-10 scale.

        Returns
        -------
        CheckinResult with risk level and recommendation.
        """
        avg = (mood + energy) / 2.0

        if avg >= _RISK_THRESHOLDS["low"]:
            risk = "low"
            rec = "You're in good shape — jump into a ranked session!"
        elif avg >= _RISK_THRESHOLDS["medium"]:
            risk = "medium"
            rec = "Consider a warm-up game before ranked play."
        else:
            risk = "high"
            rec = "High risk of tilt. Try a training mode or take a break first."

        result = CheckinResult(
            user_id=user_id,
            mood_score=mood,
            energy_score=energy,
            risk_level=risk,
            recommendation=rec,
        )

        _checkin_store.setdefault(user_id, []).append(result)
        return result

    # -- Live performance monitoring ----------------------------------------

    @staticmethod
    def monitor_performance(
        user_id: str,
        session_metrics: dict[str, Any],
    ) -> TiltStatus:
        """Track win-rate drop, error spike, and decision degradation.

        *session_metrics* should contain keys such as:
        - ``win_rate`` (float 0-1)
        - ``baseline_win_rate`` (float 0-1)
        - ``error_count`` (int)
        - ``baseline_errors`` (int)
        - ``reaction_time_ms`` (float)
        - ``baseline_reaction_ms`` (float)
        - ``decision_accuracy`` (float 0-1)
        - ``baseline_decision_accuracy`` (float 0-1)
        """
        _session_metrics_store.setdefault(user_id, []).append(session_metrics)

        signals: list[str] = []

        # Win-rate drop
        wr = session_metrics.get("win_rate", 0)
        bwr = session_metrics.get("baseline_win_rate", wr)
        if bwr > 0 and (bwr - wr) / bwr >= _TILT_WIN_RATE_DROP:
            signals.append("win_rate_drop")

        # Error spike
        errors = session_metrics.get("error_count", 0)
        b_errors = session_metrics.get("baseline_errors", errors)
        if b_errors > 0 and errors / b_errors >= _TILT_ERROR_SPIKE_FACTOR:
            signals.append("error_spike")

        # Decision degradation
        da = session_metrics.get("decision_accuracy", 1.0)
        bda = session_metrics.get("baseline_decision_accuracy", da)
        if bda > 0 and (bda - da) / bda >= _FATIGUE_DECISION_DROP:
            signals.append("decision_degradation")

        is_tilted = len(signals) >= 2
        severity = min(len(signals) / 3.0, 1.0)

        tilt_type = None
        if is_tilted:
            # Heuristic: error spike → rage tilt; decision degradation → frustration
            if "error_spike" in signals:
                tilt_type = TiltType.RAGE
            else:
                tilt_type = TiltType.FRUSTRATION

        status = TiltStatus(
            user_id=user_id,
            is_tilted=is_tilted,
            tilt_type=tilt_type,
            severity=severity,
            confidence=0.6 + 0.13 * len(signals),
            detected_at=datetime.utcnow() if is_tilted else None,
        )

        if is_tilted:
            event = TiltEvent(
                event_id=uuid.uuid4().hex,
                user_id=user_id,
                tilt_type=tilt_type or TiltType.FRUSTRATION,
                severity=severity,
                trigger=", ".join(signals),
            )
            _tilt_history.setdefault(user_id, []).append(event)

        return status

    # -- Tilt vs. fatigue differential --------------------------------------

    @staticmethod
    def detect_tilt_vs_fatigue(metrics: dict[str, Any]) -> TiltOrFatigue:
        """Differentiate emotional tilt from cognitive fatigue.

        Tilt indicators (emotional):
        - Sudden error spikes
        - Aggressive/risky plays
        - Win-rate volatility

        Fatigue indicators (cognitive):
        - Gradual reaction-time increase
        - Steady decision-accuracy decline
        - Reduced APM / input frequency
        """
        tilt_signals: list[str] = []
        fatigue_signals: list[str] = []

        # Error spike → tilt
        errors = metrics.get("error_count", 0)
        b_errors = metrics.get("baseline_errors", errors)
        if b_errors > 0 and errors / b_errors >= _TILT_ERROR_SPIKE_FACTOR:
            tilt_signals.append("error_spike")

        # Win-rate volatility → tilt
        wr = metrics.get("win_rate", 0)
        bwr = metrics.get("baseline_win_rate", wr)
        if bwr > 0 and (bwr - wr) / bwr >= _TILT_WIN_RATE_DROP:
            tilt_signals.append("win_rate_drop")

        # Risky play increase → tilt
        if metrics.get("risky_play_ratio", 0) > 0.4:
            tilt_signals.append("risky_plays")

        # Reaction time increase → fatigue
        rt = metrics.get("reaction_time_ms", 0)
        brt = metrics.get("baseline_reaction_ms", rt)
        if brt > 0 and rt / brt >= _FATIGUE_REACTION_INCREASE:
            fatigue_signals.append("slow_reactions")

        # Decision accuracy decline → fatigue
        da = metrics.get("decision_accuracy", 1.0)
        bda = metrics.get("baseline_decision_accuracy", da)
        if bda > 0 and (bda - da) / bda >= _FATIGUE_DECISION_DROP:
            fatigue_signals.append("decision_decline")

        # APM drop → fatigue
        apm = metrics.get("apm", 0)
        b_apm = metrics.get("baseline_apm", apm)
        if b_apm > 0 and (b_apm - apm) / b_apm >= 0.25:
            fatigue_signals.append("apm_drop")

        tilt_prob = min(len(tilt_signals) / 3.0, 1.0)
        fatigue_prob = min(len(fatigue_signals) / 3.0, 1.0)

        if tilt_prob >= 0.5 and fatigue_prob >= 0.5:
            classification = "both"
        elif tilt_prob >= 0.5:
            classification = "tilt"
        elif fatigue_prob >= 0.5:
            classification = "fatigue"
        else:
            classification = "none"

        return TiltOrFatigue(
            classification=classification,
            tilt_probability=round(tilt_prob, 2),
            fatigue_probability=round(fatigue_prob, 2),
            indicators=tilt_signals + fatigue_signals,
            reasoning=f"Tilt signals: {tilt_signals}; Fatigue signals: {fatigue_signals}",
        )

    # -- Interventions ------------------------------------------------------

    @staticmethod
    def trigger_intervention(
        user_id: str,
        tilt_status: TiltStatus,
    ) -> list[Intervention]:
        """Suggest appropriate interventions based on tilt status.

        Higher severity → more aggressive interventions.
        """
        interventions: list[Intervention] = []

        if not tilt_status.is_tilted:
            return interventions

        # Always suggest breathing exercise for any tilt
        interventions.append(
            Intervention(
                kind=InterventionKind.BREATHING,
                message="Take 5 deep breaths — inhale 4s, hold 4s, exhale 6s.",
                duration_minutes=2,
                priority=1,
            )
        )

        if tilt_status.severity >= 0.3:
            interventions.append(
                Intervention(
                    kind=InterventionKind.HYDRATION,
                    message="Grab some water and stretch for a moment.",
                    duration_minutes=3,
                    priority=2,
                )
            )

        if tilt_status.severity >= 0.5:
            interventions.append(
                Intervention(
                    kind=InterventionKind.MODE_SWITCH,
                    message="Switch to a casual or training mode to reset your mental state.",
                    priority=3,
                )
            )

        if tilt_status.severity >= 0.7:
            interventions.append(
                Intervention(
                    kind=InterventionKind.BREAK,
                    message="Take a 10-15 minute break away from the screen.",
                    duration_minutes=15,
                    priority=4,
                )
            )

        if tilt_status.severity >= 0.9:
            interventions.append(
                Intervention(
                    kind=InterventionKind.SESSION_END,
                    message="Consider ending this session. You'll perform better after rest.",
                    priority=5,
                )
            )

        return interventions

    # -- Peak hours analysis ------------------------------------------------

    @staticmethod
    def get_mental_peak_hours(user_id: str) -> PeakHours:
        """Analyse session history to find best performance time windows.

        Uses stored session metrics keyed by hour-of-day to compute average
        performance per hour.
        """
        metrics_list = _session_metrics_store.get(user_id, [])

        hour_perf: dict[int, list[float]] = {}
        for m in metrics_list:
            hour = m.get("hour_of_day")
            perf = m.get("win_rate", m.get("performance_score", 0.5))
            if hour is not None:
                hour_perf.setdefault(hour, []).append(perf)

        avg_by_hour: dict[int, float] = {}
        for h, vals in hour_perf.items():
            avg_by_hour[h] = round(sum(vals) / len(vals), 3)

        if avg_by_hour:
            sorted_hours = sorted(avg_by_hour, key=avg_by_hour.get, reverse=True)  # type: ignore[arg-type]
            best = sorted_hours[:3]
            worst = sorted_hours[-3:]
        else:
            best = []
            worst = []

        return PeakHours(
            user_id=user_id,
            best_hours=best,
            worst_hours=worst,
            avg_performance_by_hour=avg_by_hour,
        )

    # -- Tilt history -------------------------------------------------------

    @staticmethod
    def get_tilt_history(user_id: str) -> list[TiltEvent]:
        """Return all recorded tilt events for a player."""
        return _tilt_history.get(user_id, [])
