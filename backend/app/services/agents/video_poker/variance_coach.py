"""VarianceCoach — explains variance, integrates TiltGuard, detects strategy deviations.

Helps players understand the mathematical reality of video poker variance,
monitors for tilt-induced strategy deviations, and provides evidence-based
coaching to maintain discipline during losing and winning streaks.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from app.schemas.video_poker.variance import (
    DeviationAlert,
    DeviationSeverity,
    SessionMood,
    StreakAnalysis,
    TiltRisk,
    TiltStatus,
    VarianceExplanation,
    VarianceLesson,
)
from app.schemas.video_poker.strategy import VariantType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Educational content
# ---------------------------------------------------------------------------

VARIANCE_LESSONS: list[dict[str, str]] = [
    {
        "id": "what_is_variance",
        "title": "What Is Variance?",
        "content": (
            "Variance measures how far your actual results spread from the "
            "expected average. In video poker, high variance means bigger swings — "
            "longer losing streaks AND bigger wins. It does NOT mean the machine "
            "is 'due' or 'hot'."
        ),
        "key_insight": "Variance is math, not luck. Each hand is independent.",
    },
    {
        "id": "standard_deviation",
        "title": "Standard Deviation in Practice",
        "content": (
            "Standard deviation (SD) tells you the typical swing per hand. "
            "Jacks or Better has ~4.4 SD, while Double Double Bonus has ~7.0 SD. "
            "Higher SD = wilder ride, even with the same RTP."
        ),
        "key_insight": "Choose your variant based on your comfort with swings.",
    },
    {
        "id": "losing_streaks",
        "title": "Losing Streaks Are Normal",
        "content": (
            "In 9/6 Jacks or Better, you will lose on ~55% of hands. Streaks of "
            "10-15 consecutive losses happen regularly. A streak of 20+ losses "
            "occurs roughly once every 200 sessions. This is expected math."
        ),
        "key_insight": "A losing streak is not a broken machine — it is normal variance.",
    },
    {
        "id": "royal_flush_wait",
        "title": "The Royal Flush Wait",
        "content": (
            "A royal flush appears roughly once every 40,000 hands with perfect "
            "play. At 400 hands/hour, that is 100 hours of play. You might hit "
            "one in 10 hours or go 300+ hours without one. Both are normal."
        ),
        "key_insight": "Never change strategy to 'chase' a royal flush.",
    },
    {
        "id": "short_vs_long_run",
        "title": "Short Run vs. Long Run",
        "content": (
            "In the short run (one session), variance dominates. You might be up "
            "50% or down 40% — both are normal. In the long run (100,000+ hands), "
            "results converge toward the mathematical RTP."
        ),
        "key_insight": "Judge your play by decisions, not by session results.",
    },
]

# Tilt triggers and their weights
TILT_TRIGGERS: dict[str, float] = {
    "consecutive_losses": 0.3,
    "large_single_loss": 0.2,
    "missed_big_hand": 0.25,
    "session_loss_pct": 0.15,
    "play_duration": 0.1,
}


# ---------------------------------------------------------------------------
# VarianceCoach
# ---------------------------------------------------------------------------

class VarianceCoach:
    """Coaching engine for understanding and managing video poker variance."""

    def explain_variance(
        self,
        variant: VariantType = VariantType.JACKS_OR_BETTER,
        hands_played: int = 0,
        current_result: float = 0.0,
        bet_size: float = 1.25,
    ) -> VarianceExplanation:
        """Provide a contextual explanation of variance for the player's situation."""
        sd_map = {
            VariantType.JACKS_OR_BETTER: 4.42,
            VariantType.DEUCES_WILD: 5.08,
            VariantType.DOUBLE_BONUS: 6.35,
            VariantType.DOUBLE_DOUBLE_BONUS: 7.04,
            VariantType.JOKER_POKER: 5.65,
        }
        rtp_map = {
            VariantType.JACKS_OR_BETTER: 99.54,
            VariantType.DEUCES_WILD: 100.76,
            VariantType.DOUBLE_BONUS: 100.17,
            VariantType.DOUBLE_DOUBLE_BONUS: 98.98,
            VariantType.JOKER_POKER: 100.64,
        }

        sd = sd_map.get(variant, 4.42)
        rtp = rtp_map.get(variant, 99.54)
        edge = (100.0 - rtp) / 100.0

        if hands_played > 0:
            expected_result = round(-edge * hands_played * bet_size, 2)
            session_sd = round(sd * math.sqrt(hands_played) * bet_size, 2)
            z_score = (
                (current_result - expected_result) / session_sd
                if session_sd > 0
                else 0.0
            )
        else:
            expected_result = 0.0
            session_sd = 0.0
            z_score = 0.0

        # Determine if result is within normal range
        if abs(z_score) <= 1:
            result_assessment = "completely_normal"
            assessment_text = "Your result is within 1 standard deviation — completely typical."
        elif abs(z_score) <= 2:
            result_assessment = "normal"
            assessment_text = "Your result is within 2 standard deviations — well within normal range."
        elif abs(z_score) <= 3:
            result_assessment = "unusual_but_expected"
            assessment_text = "Somewhat unusual, but happens ~5% of the time. Nothing to worry about."
        else:
            result_assessment = "rare_but_possible"
            assessment_text = "A rare outcome, but possible. This is variance at work."

        # Pick relevant lesson
        if current_result < expected_result - session_sd:
            relevant_lesson = "losing_streaks"
        elif hands_played < 100:
            relevant_lesson = "short_vs_long_run"
        else:
            relevant_lesson = "what_is_variance"

        lessons = [
            VarianceLesson(**l) for l in VARIANCE_LESSONS
            if l["id"] == relevant_lesson
        ]

        return VarianceExplanation(
            variant=variant,
            hands_played=hands_played,
            current_result=current_result,
            expected_result=expected_result,
            session_sd=session_sd,
            z_score=round(z_score, 2),
            result_assessment=result_assessment,
            assessment_text=assessment_text,
            relevant_lessons=lessons,
            encouragement=self._get_encouragement(z_score, hands_played),
        )

    def assess_tilt_risk(
        self,
        consecutive_losses: int = 0,
        session_loss_pct: float = 0.0,
        hands_played: int = 0,
        missed_big_hands: int = 0,
        time_playing_minutes: int = 0,
    ) -> TiltStatus:
        """Assess current tilt risk based on session factors.

        Integrates with TiltGuard philosophy — proactive intervention before
        tilt affects play quality.
        """
        risk_score = 0.0
        triggers: list[str] = []

        # Consecutive losses
        if consecutive_losses >= 15:
            risk_score += TILT_TRIGGERS["consecutive_losses"]
            triggers.append(f"{consecutive_losses} consecutive losses")
        elif consecutive_losses >= 8:
            risk_score += TILT_TRIGGERS["consecutive_losses"] * 0.5
            triggers.append(f"{consecutive_losses} consecutive losses (moderate)")

        # Session loss
        if session_loss_pct >= 40:
            risk_score += TILT_TRIGGERS["session_loss_pct"]
            triggers.append(f"Session loss of {session_loss_pct:.1f}%")
        elif session_loss_pct >= 25:
            risk_score += TILT_TRIGGERS["session_loss_pct"] * 0.5
            triggers.append(f"Session loss of {session_loss_pct:.1f}% (building)")

        # Missed big hands (held 4 to royal, missed, etc.)
        if missed_big_hands >= 3:
            risk_score += TILT_TRIGGERS["missed_big_hand"]
            triggers.append(f"Missed {missed_big_hands} big hand draws")
        elif missed_big_hands >= 1:
            risk_score += TILT_TRIGGERS["missed_big_hand"] * 0.4
            triggers.append("Missed a big hand draw")

        # Play duration
        if time_playing_minutes >= 180:
            risk_score += TILT_TRIGGERS["play_duration"]
            triggers.append(f"Playing for {time_playing_minutes} minutes")
        elif time_playing_minutes >= 120:
            risk_score += TILT_TRIGGERS["play_duration"] * 0.5
            triggers.append(f"Extended play ({time_playing_minutes} min)")

        # Determine tilt level
        risk_score = round(min(risk_score, 1.0), 2)

        if risk_score >= 0.7:
            risk = TiltRisk.CRITICAL
            recommendation = (
                "STOP PLAYING. Take a mandatory break of at least 30 minutes. "
                "Your decision-making is likely compromised."
            )
        elif risk_score >= 0.5:
            risk = TiltRisk.HIGH
            recommendation = (
                "Take a 15-minute break NOW. Stretch, get water, review strategy. "
                "Return only if you feel clear-headed."
            )
        elif risk_score >= 0.3:
            risk = TiltRisk.MODERATE
            recommendation = (
                "Be aware of increasing tilt factors. Slow your pace, "
                "double-check each hold decision against strategy."
            )
        elif risk_score >= 0.1:
            risk = TiltRisk.LOW
            recommendation = "Minor tilt factors present — maintain discipline."
        else:
            risk = TiltRisk.NONE
            recommendation = "Clear-headed play. No tilt indicators."

        return TiltStatus(
            risk_level=risk,
            risk_score=risk_score,
            triggers=triggers,
            recommendation=recommendation,
            should_take_break=risk_score >= 0.5,
            mandatory_stop=risk_score >= 0.7,
        )

    def detect_strategy_deviation(
        self,
        recent_decisions: list[dict[str, Any]],
        baseline_accuracy: float = 98.0,
    ) -> DeviationAlert:
        """Detect if the player is deviating from optimal strategy.

        Compares recent play accuracy against their established baseline.
        A significant drop signals tilt-induced errors.
        """
        if not recent_decisions:
            return DeviationAlert(
                is_deviating=False,
                severity=DeviationSeverity.NONE,
                recent_accuracy=baseline_accuracy,
                baseline_accuracy=baseline_accuracy,
                accuracy_drop=0.0,
                pattern=None,
                recommendation="No recent decisions to analyze.",
            )

        # Calculate recent accuracy
        total = len(recent_decisions)
        correct = sum(1 for d in recent_decisions if d.get("is_correct", True))
        recent_accuracy = round(correct / total * 100, 1) if total > 0 else 100.0

        accuracy_drop = round(baseline_accuracy - recent_accuracy, 1)

        # Identify mistake patterns
        mistakes = [d for d in recent_decisions if not d.get("is_correct", True)]
        pattern = None
        if mistakes:
            categories = [m.get("mistake_type", "unknown") for m in mistakes]
            counts: dict[str, int] = {}
            for cat in categories:
                counts[cat] = counts.get(cat, 0) + 1
            if counts:
                pattern = max(counts, key=lambda k: counts[k])

        # Classify severity
        if accuracy_drop >= 15:
            severity = DeviationSeverity.CRITICAL
        elif accuracy_drop >= 8:
            severity = DeviationSeverity.HIGH
        elif accuracy_drop >= 3:
            severity = DeviationSeverity.MODERATE
        elif accuracy_drop >= 1:
            severity = DeviationSeverity.MINOR
        else:
            severity = DeviationSeverity.NONE

        is_deviating = severity != DeviationSeverity.NONE

        if is_deviating:
            recommendation = (
                f"Strategy accuracy dropped {accuracy_drop:.1f}% from baseline. "
                f"{'Most errors: ' + pattern + '. ' if pattern else ''}"
                f"{'STOP PLAYING — significant deviation detected.' if severity in (DeviationSeverity.CRITICAL, DeviationSeverity.HIGH) else 'Slow down and review strategy chart.'}"
            )
        else:
            recommendation = "Play quality is consistent with your baseline. Keep it up."

        return DeviationAlert(
            is_deviating=is_deviating,
            severity=severity,
            recent_accuracy=recent_accuracy,
            baseline_accuracy=baseline_accuracy,
            accuracy_drop=accuracy_drop,
            pattern=pattern,
            recommendation=recommendation,
        )

    def analyze_streak(
        self,
        results: list[float],
        bet_size: float = 1.25,
    ) -> StreakAnalysis:
        """Analyze a sequence of hand results for streak patterns.

        Helps players understand that streaks are mathematically normal.
        """
        if not results:
            return StreakAnalysis(
                total_hands=0,
                winning_hands=0,
                losing_hands=0,
                longest_win_streak=0,
                longest_loss_streak=0,
                current_streak=0,
                current_streak_type="none",
                streak_is_normal=True,
                explanation="No hands to analyze.",
                mood=SessionMood.NEUTRAL,
            )

        wins = sum(1 for r in results if r > 0)
        losses = sum(1 for r in results if r <= 0)

        # Calculate streaks
        max_win_streak = 0
        max_loss_streak = 0
        current_streak = 0
        current_type = "none"

        win_streak = 0
        loss_streak = 0

        for r in results:
            if r > 0:
                win_streak += 1
                loss_streak = 0
                max_win_streak = max(max_win_streak, win_streak)
            else:
                loss_streak += 1
                win_streak = 0
                max_loss_streak = max(max_loss_streak, loss_streak)

        # Current streak from end
        if results[-1] > 0:
            current_type = "winning"
            current_streak = win_streak
        else:
            current_type = "losing"
            current_streak = loss_streak

        # Is this streak normal?
        n = len(results)
        # Expected max streak length ~ log2(n) for 50/50
        expected_max = max(1, int(math.log2(n + 1)) + 2)
        relevant_streak = max_loss_streak if current_type == "losing" else max_win_streak
        streak_is_normal = relevant_streak <= expected_max * 2

        # Mood assessment
        total_result = sum(results)
        if total_result > bet_size * 20:
            mood = SessionMood.EUPHORIC
        elif total_result > 0:
            mood = SessionMood.POSITIVE
        elif total_result > -bet_size * 10:
            mood = SessionMood.NEUTRAL
        elif total_result > -bet_size * 30:
            mood = SessionMood.FRUSTRATED
        else:
            mood = SessionMood.TILTED

        explanation = (
            f"Over {n} hands: {wins} wins, {losses} losses. "
            f"Longest losing streak: {max_loss_streak} hands "
            f"({'normal' if max_loss_streak <= expected_max * 2 else 'above average but possible'}). "
            f"Current: {current_streak}-hand {current_type} streak."
        )

        return StreakAnalysis(
            total_hands=n,
            winning_hands=wins,
            losing_hands=losses,
            longest_win_streak=max_win_streak,
            longest_loss_streak=max_loss_streak,
            current_streak=current_streak,
            current_streak_type=current_type,
            streak_is_normal=streak_is_normal,
            explanation=explanation,
            mood=mood,
        )

    def get_lesson(self, lesson_id: str) -> VarianceLesson | None:
        """Retrieve a specific variance education lesson."""
        for lesson in VARIANCE_LESSONS:
            if lesson["id"] == lesson_id:
                return VarianceLesson(**lesson)
        return None

    def get_all_lessons(self) -> list[VarianceLesson]:
        """Return all available variance education content."""
        return [VarianceLesson(**l) for l in VARIANCE_LESSONS]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_encouragement(z_score: float, hands_played: int) -> str:
        if hands_played == 0:
            return "Ready to play! Remember: judge your play by decisions, not outcomes."
        if z_score < -2:
            return (
                "Tough stretch, but this is normal variance. Your strategy is still "
                "correct — the math will balance over time. Consider a break if frustrated."
            )
        if z_score < -1:
            return (
                "Running a bit below expectation. Stay patient and trust the math. "
                "Every correct decision has positive long-term value."
            )
        if z_score < 1:
            return "Results are right around where math predicts. Solid, disciplined play."
        if z_score < 2:
            return (
                "Running above expectation — nice! Remember this feeling when "
                "variance goes the other way. Lock profits with your win goal."
            )
        return (
            "Exceptional run! This is the upside of variance. "
            "Don't let it convince you to deviate from strategy."
        )
