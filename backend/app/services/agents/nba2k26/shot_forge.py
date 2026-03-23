"""ShotForge AI — personalized timing window trainer per jump shot base/release.

Tracks shot timing data, identifies green windows, recommends optimal jump shot
configurations, and generates personalized training plans for shooting improvement.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from app.schemas.nba2k26.gameplay import (
    ShotFeedback,
    ShotTiming,
    ShotTrainingPlan,
    ShotType,
    TimingGrade,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Jump shot base timing data (green window in ms from shot initiation)
# ---------------------------------------------------------------------------

SHOT_BASE_DATA: dict[str, dict[str, float]] = {
    "Base 98": {"optimal_release_ms": 520.0, "green_window_ms": 35.0, "speed_modifier": 1.0},
    "Base 38": {"optimal_release_ms": 490.0, "green_window_ms": 40.0, "speed_modifier": 1.05},
    "Base 3": {"optimal_release_ms": 540.0, "green_window_ms": 30.0, "speed_modifier": 0.95},
    "Kobe": {"optimal_release_ms": 510.0, "green_window_ms": 32.0, "speed_modifier": 1.0},
    "Curry": {"optimal_release_ms": 470.0, "green_window_ms": 38.0, "speed_modifier": 1.1},
    "Trae Young": {"optimal_release_ms": 460.0, "green_window_ms": 36.0, "speed_modifier": 1.12},
    "KD": {"optimal_release_ms": 530.0, "green_window_ms": 33.0, "speed_modifier": 0.98},
    "Carmelo": {"optimal_release_ms": 500.0, "green_window_ms": 37.0, "speed_modifier": 1.02},
    "Larry Bird": {"optimal_release_ms": 550.0, "green_window_ms": 28.0, "speed_modifier": 0.92},
    "Ray Allen": {"optimal_release_ms": 505.0, "green_window_ms": 42.0, "speed_modifier": 1.03},
}

# Release modifiers — how different releases affect the green window
RELEASE_MODIFIERS: dict[str, float] = {
    "Release 1": 1.0,
    "Release 2": 0.97,
    "Release 3": 1.03,
    "Curry Release": 1.08,
    "Kobe Release": 0.95,
    "KD Release": 0.98,
    "Trae Young Release": 1.05,
    "Ray Allen Release": 1.10,
    "Bird Release": 0.90,
    "Carmelo Release": 1.02,
}

# Timing grade boundaries (ms offset from optimal)
TIMING_GRADE_BOUNDS: list[tuple[float, TimingGrade]] = [
    (5.0, TimingGrade.EXCELLENT),
    (15.0, TimingGrade.SLIGHTLY_EARLY),    # or slightly_late
    (30.0, TimingGrade.EARLY),             # or late
    (999.0, TimingGrade.VERY_EARLY),       # or very_late
]


class ShotForge:
    """NBA 2K26 shot timing trainer and analyzer.

    Tracks per-user shot history, computes green percentages, recommends
    optimal jump shot configurations, and generates training plans.
    """

    def __init__(self) -> None:
        self._shot_history: dict[str, list[ShotFeedback]] = defaultdict(list)
        self._timing_profiles: dict[str, ShotTiming] = {}

    # ------------------------------------------------------------------
    # Shot timing analysis
    # ------------------------------------------------------------------

    def analyze_timing(
        self,
        user_id: str,
        jump_shot_base: str,
        release_1: str = "Release 1",
        release_2: str = "Release 1",
        release_blend: int = 50,
        release_speed: str = "normal",
    ) -> ShotTiming:
        """Analyze the timing window for a specific jump shot configuration.

        Computes the green window size, optimal release point, and expected
        make/green percentages based on the base + release combination.
        """
        base_data = SHOT_BASE_DATA.get(jump_shot_base, {
            "optimal_release_ms": 500.0, "green_window_ms": 30.0, "speed_modifier": 1.0,
        })

        # Apply release modifiers
        r1_mod = RELEASE_MODIFIERS.get(release_1, 1.0)
        r2_mod = RELEASE_MODIFIERS.get(release_2, 1.0)
        blend_mod = (r1_mod * (release_blend / 100.0)) + (r2_mod * (1.0 - release_blend / 100.0))

        # Speed multiplier
        speed_mult = {"slow": 1.15, "normal": 1.0, "fast": 0.88}.get(release_speed, 1.0)

        green_window = base_data["green_window_ms"] * blend_mod * speed_mult
        optimal_release = base_data["optimal_release_ms"] * base_data["speed_modifier"] * speed_mult

        # Compute user-specific make/green pct from history
        history = self._shot_history.get(user_id, [])
        relevant = [s for s in history if s.shot_type in (ShotType.JUMPER, ShotType.THREE_POINTER)]
        samples = len(relevant)
        make_pct = sum(1 for s in relevant if s.was_make) / max(samples, 1)
        green_pct = sum(1 for s in relevant if s.was_green) / max(samples, 1)

        timing = ShotTiming(
            user_id=user_id,
            jump_shot_base=jump_shot_base,
            jump_shot_release_1=release_1,
            jump_shot_release_2=release_2,
            release_blend=release_blend,
            release_speed=release_speed,
            green_window_ms=round(green_window, 1),
            optimal_release_ms=round(optimal_release, 1),
            make_percentage=round(make_pct, 3),
            green_percentage=round(green_pct, 3),
            samples=samples,
        )

        key = f"{user_id}:{jump_shot_base}"
        self._timing_profiles[key] = timing

        logger.info(
            "Shot timing analyzed: user=%s base=%s green_window=%.1fms optimal=%.1fms",
            user_id, jump_shot_base, green_window, optimal_release,
        )
        return timing

    # ------------------------------------------------------------------
    # Shot feedback recording
    # ------------------------------------------------------------------

    def record_shot(self, user_id: str, feedback: ShotFeedback) -> ShotTiming:
        """Record a shot attempt and update the user's timing profile.

        Returns updated timing statistics after incorporating the new shot.
        """
        self._shot_history[user_id].append(feedback)

        history = self._shot_history[user_id]
        relevant = [s for s in history if s.shot_type == feedback.shot_type]
        samples = len(relevant)
        make_pct = sum(1 for s in relevant if s.was_make) / max(samples, 1)
        green_pct = sum(1 for s in relevant if s.was_green) / max(samples, 1)

        # Compute timing grade from release_ms
        grade = self._grade_timing(feedback.release_ms, 500.0)  # default optimal

        timing = ShotTiming(
            user_id=user_id,
            jump_shot_base="current",
            timing_grade=grade,
            make_percentage=round(make_pct, 3),
            green_percentage=round(green_pct, 3),
            shot_type=feedback.shot_type,
            samples=samples,
        )

        logger.info(
            "Shot recorded: user=%s type=%s grade=%s make=%.1f%% green=%.1f%%",
            user_id, feedback.shot_type.value, grade.value,
            make_pct * 100, green_pct * 100,
        )
        return timing

    def _grade_timing(self, release_ms: float, optimal_ms: float) -> TimingGrade:
        """Determine timing grade based on offset from optimal release."""
        offset = abs(release_ms - optimal_ms)
        early = release_ms < optimal_ms

        for bound, grade in TIMING_GRADE_BOUNDS:
            if offset <= bound:
                if grade == TimingGrade.EXCELLENT:
                    return TimingGrade.EXCELLENT
                if early:
                    if grade == TimingGrade.SLIGHTLY_EARLY:
                        return TimingGrade.SLIGHTLY_EARLY
                    if grade == TimingGrade.EARLY:
                        return TimingGrade.EARLY
                    return TimingGrade.VERY_EARLY
                else:
                    if grade == TimingGrade.SLIGHTLY_EARLY:
                        return TimingGrade.SLIGHTLY_LATE
                    if grade == TimingGrade.EARLY:
                        return TimingGrade.LATE
                    return TimingGrade.VERY_LATE
        return TimingGrade.VERY_LATE

    # ------------------------------------------------------------------
    # Training plan generator
    # ------------------------------------------------------------------

    def generate_training_plan(
        self,
        user_id: str,
        target_green_pct: float = 0.6,
    ) -> ShotTrainingPlan:
        """Generate a personalized shot training plan.

        Analyzes the user's shot history, identifies timing patterns, and
        creates a structured drill plan to improve green percentage.
        """
        history = self._shot_history.get(user_id, [])
        samples = len(history)
        current_green_pct = sum(1 for s in history if s.was_green) / max(samples, 1)
        current_make_pct = sum(1 for s in history if s.was_make) / max(samples, 1)

        # Identify patterns
        focus_areas: list[str] = []
        drills: list[str] = []

        early_count = sum(1 for s in history if s.timing_grade in (
            TimingGrade.EARLY, TimingGrade.VERY_EARLY, TimingGrade.SLIGHTLY_EARLY,
        ))
        late_count = sum(1 for s in history if s.timing_grade in (
            TimingGrade.LATE, TimingGrade.VERY_LATE, TimingGrade.SLIGHTLY_LATE,
        ))

        if samples > 0:
            if early_count / max(samples, 1) > 0.4:
                focus_areas.append("Releasing too early — hold the button slightly longer")
                drills.append("Slow-motion release drill: practice at 0.5x speed")
            elif late_count / max(samples, 1) > 0.4:
                focus_areas.append("Releasing too late — release the button slightly earlier")
                drills.append("Quick-release drill: practice with fast release speed")

        # Contested shot analysis
        contested = [s for s in history if s.contest_level > 0.5]
        contested_make = sum(1 for s in contested if s.was_make) / max(len(contested), 1)
        if contested_make < 0.3:
            focus_areas.append("Poor contested shooting — work on shot selection")
            drills.append("Contested shot drill: practice with defender closeouts")

        # Default drills
        if not drills:
            drills = [
                "Free throw line warmup — 20 reps, focus on rhythm",
                "Catch-and-shoot drill — 30 reps from each corner and wing",
                "Pull-up jumper drill — 20 reps off the dribble",
                "Moving shot drill — 15 reps off screens",
            ]

        if not focus_areas:
            focus_areas = ["Maintain current timing rhythm", "Add variety to shot selection"]

        # Recommend best shot base
        best_base = self._recommend_shot_base(user_id)
        best_release = self._recommend_release(user_id)

        # Estimate sessions needed
        gap = max(target_green_pct - current_green_pct, 0.0)
        sessions = max(1, int(gap * 30))  # ~30 sessions per 100% improvement

        current_timing = ShotTiming(
            user_id=user_id,
            jump_shot_base=best_base,
            make_percentage=round(current_make_pct, 3),
            green_percentage=round(current_green_pct, 3),
            samples=samples,
        )

        return ShotTrainingPlan(
            user_id=user_id,
            current_timing=current_timing,
            target_green_pct=target_green_pct,
            drills=drills,
            focus_areas=focus_areas,
            estimated_sessions_to_target=sessions,
            recommended_shot_base=best_base,
            recommended_release=best_release,
        )

    def _recommend_shot_base(self, user_id: str) -> str:
        """Recommend the best shot base for a user based on their timing patterns."""
        history = self._shot_history.get(user_id, [])
        if not history:
            return "Ray Allen"  # Largest green window

        # If user tends to release early, recommend a faster base
        early_ratio = sum(
            1 for s in history
            if s.timing_grade in (TimingGrade.EARLY, TimingGrade.VERY_EARLY)
        ) / max(len(history), 1)

        if early_ratio > 0.4:
            return "Curry"  # Fast release matches early releasers
        return "Ray Allen"  # Wide green window for consistency

    def _recommend_release(self, user_id: str) -> str:
        """Recommend the best release animation based on timing patterns."""
        history = self._shot_history.get(user_id, [])
        if not history:
            return "Ray Allen Release"

        green_rate = sum(1 for s in history if s.was_green) / max(len(history), 1)
        if green_rate > 0.5:
            return "Curry Release"  # Reward consistent users with faster release
        return "Ray Allen Release"  # Wider window for inconsistent users

    # ------------------------------------------------------------------
    # Shot base comparison
    # ------------------------------------------------------------------

    def compare_shot_bases(self, base_a: str, base_b: str) -> dict:
        """Compare two jump shot bases side by side.

        Returns green window, speed, and optimal release differences.
        """
        data_a = SHOT_BASE_DATA.get(base_a, {
            "optimal_release_ms": 500.0, "green_window_ms": 30.0, "speed_modifier": 1.0,
        })
        data_b = SHOT_BASE_DATA.get(base_b, {
            "optimal_release_ms": 500.0, "green_window_ms": 30.0, "speed_modifier": 1.0,
        })

        return {
            "base_a": base_a,
            "base_b": base_b,
            "green_window_diff_ms": round(
                data_a["green_window_ms"] - data_b["green_window_ms"], 1,
            ),
            "speed_diff": round(
                data_a["speed_modifier"] - data_b["speed_modifier"], 3,
            ),
            "optimal_release_diff_ms": round(
                data_a["optimal_release_ms"] - data_b["optimal_release_ms"], 1,
            ),
            "recommendation": (
                base_a if data_a["green_window_ms"] > data_b["green_window_ms"] else base_b
            ),
            "reason": (
                "Larger green window for more consistent shooting"
                if data_a["green_window_ms"] != data_b["green_window_ms"]
                else "Identical green windows — choose based on animation preference"
            ),
        }

    # ------------------------------------------------------------------
    # Per-shot-type breakdown
    # ------------------------------------------------------------------

    def get_shot_type_breakdown(self, user_id: str) -> dict[str, dict]:
        """Get make/green percentages broken down by shot type."""
        history = self._shot_history.get(user_id, [])
        by_type: dict[str, list[ShotFeedback]] = defaultdict(list)
        for s in history:
            by_type[s.shot_type.value].append(s)

        breakdown: dict[str, dict] = {}
        for shot_type, shots in by_type.items():
            total = len(shots)
            breakdown[shot_type] = {
                "attempts": total,
                "makes": sum(1 for s in shots if s.was_make),
                "greens": sum(1 for s in shots if s.was_green),
                "make_pct": round(sum(1 for s in shots if s.was_make) / total, 3),
                "green_pct": round(sum(1 for s in shots if s.was_green) / total, 3),
                "avg_contest": round(sum(s.contest_level for s in shots) / total, 3),
            }

        return breakdown


# Module-level singleton
shot_forge = ShotForge()
