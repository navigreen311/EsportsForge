"""HitForge — timing window trainer, zone hitting optimizer, and count leverage analysis.

Trains hitters on pitch-specific timing windows, optimizes zone hitting PCI placement,
and calculates count leverage to guide approach at the plate.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from app.schemas.mlb26.hitting import (
    CountLeverage,
    HitApproach,
    HitTrainingPlan,
    PCIPlacement,
    SwingFeedback,
    SwingResult,
    TimingWindow,
    ZoneHittingProfile,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Timing window data by pitch type (ms from pitch release)
# ---------------------------------------------------------------------------

_TIMING_WINDOWS: dict[str, dict[str, float]] = {
    "four_seam": {"optimal_ms": 420, "window_ms": 30, "velo_range": "93-98 mph"},
    "two_seam": {"optimal_ms": 430, "window_ms": 32, "velo_range": "91-95 mph"},
    "cutter": {"optimal_ms": 445, "window_ms": 28, "velo_range": "87-92 mph"},
    "slider": {"optimal_ms": 465, "window_ms": 25, "velo_range": "83-88 mph"},
    "curveball": {"optimal_ms": 500, "window_ms": 35, "velo_range": "75-82 mph"},
    "changeup": {"optimal_ms": 470, "window_ms": 30, "velo_range": "83-88 mph"},
    "sinker": {"optimal_ms": 425, "window_ms": 30, "velo_range": "92-96 mph"},
    "splitter": {"optimal_ms": 455, "window_ms": 26, "velo_range": "85-90 mph"},
}

# Count leverage values (higher = more hitter-friendly)
_COUNT_LEVERAGE: dict[str, dict[str, Any]] = {
    "0-0": {"leverage": 0.50, "approach": "neutral", "swing_pct": 0.30},
    "1-0": {"leverage": 0.60, "approach": "hitter_ahead", "swing_pct": 0.35},
    "2-0": {"leverage": 0.75, "approach": "hitter_ahead", "swing_pct": 0.25},
    "3-0": {"leverage": 0.85, "approach": "green_light_or_take", "swing_pct": 0.10},
    "3-1": {"leverage": 0.80, "approach": "hitter_ahead", "swing_pct": 0.40},
    "2-1": {"leverage": 0.65, "approach": "hitter_ahead", "swing_pct": 0.38},
    "0-1": {"leverage": 0.40, "approach": "pitcher_ahead", "swing_pct": 0.35},
    "0-2": {"leverage": 0.20, "approach": "protect", "swing_pct": 0.50},
    "1-2": {"leverage": 0.25, "approach": "protect", "swing_pct": 0.48},
    "2-2": {"leverage": 0.35, "approach": "battle", "swing_pct": 0.45},
    "3-2": {"leverage": 0.55, "approach": "full_count", "swing_pct": 0.55},
    "1-1": {"leverage": 0.50, "approach": "neutral", "swing_pct": 0.35},
}

# PCI placement zones (zone number -> {x, y} normalized 0-1 PCI position)
_PCI_DEFAULTS: dict[int, dict[str, float]] = {
    1: {"x": 0.3, "y": 0.7}, 2: {"x": 0.5, "y": 0.7}, 3: {"x": 0.7, "y": 0.7},
    4: {"x": 0.3, "y": 0.5}, 5: {"x": 0.5, "y": 0.5}, 6: {"x": 0.7, "y": 0.5},
    7: {"x": 0.3, "y": 0.3}, 8: {"x": 0.5, "y": 0.3}, 9: {"x": 0.7, "y": 0.3},
}


class HitForge:
    """MLB The Show 26 hitting engine.

    Trains timing windows, optimizes PCI placement, analyzes count leverage,
    and generates personalized training plans.
    """

    def __init__(self) -> None:
        self._swing_history: dict[str, list[SwingFeedback]] = defaultdict(list)
        self._zone_profiles: dict[str, ZoneHittingProfile] = {}

    # ------------------------------------------------------------------
    # Timing window analysis
    # ------------------------------------------------------------------

    def analyze_timing(
        self,
        user_id: str,
        pitch_type: str,
        swing_ms: float,
    ) -> TimingWindow:
        """Evaluate swing timing against the optimal window for a pitch type.

        Returns timing grade, offset, and corrective advice.
        """
        tw_data = _TIMING_WINDOWS.get(pitch_type, {"optimal_ms": 450, "window_ms": 30})
        optimal = tw_data["optimal_ms"]
        window = tw_data["window_ms"]
        offset = swing_ms - optimal

        if abs(offset) <= window * 0.3:
            grade = "perfect"
        elif abs(offset) <= window * 0.7:
            grade = "good"
        elif abs(offset) <= window:
            grade = "okay"
        else:
            grade = "miss"

        tips: list[str] = []
        if offset < -window * 0.5:
            tips.append(f"Swing was {abs(offset):.0f}ms early — wait on the pitch longer.")
            tips.append(f"Against {pitch_type}, delay your trigger by ~{abs(offset):.0f}ms.")
        elif offset > window * 0.5:
            tips.append(f"Swing was {offset:.0f}ms late — start your swing earlier.")
            tips.append(f"Look for the release point and commit sooner against {pitch_type}.")
        else:
            tips.append("Timing is in the window — focus on PCI placement now.")

        return TimingWindow(
            user_id=user_id,
            pitch_type=pitch_type,
            swing_ms=swing_ms,
            optimal_ms=optimal,
            window_ms=window,
            offset_ms=round(offset, 1),
            grade=grade,
            velo_range=tw_data.get("velo_range", "unknown"),
            tips=tips,
        )

    # ------------------------------------------------------------------
    # Zone hitting optimizer
    # ------------------------------------------------------------------

    def optimize_pci(
        self,
        user_id: str,
        target_zone: int,
        pitch_type: str = "four_seam",
        count: str = "0-0",
    ) -> PCIPlacement:
        """Recommend optimal PCI placement for a target zone.

        Adjusts default placement based on pitch type movement and count leverage.
        """
        default_pos = _PCI_DEFAULTS.get(target_zone, {"x": 0.5, "y": 0.5})
        x, y = default_pos["x"], default_pos["y"]

        # Adjust for pitch movement
        tw_data = _TIMING_WINDOWS.get(pitch_type, {})
        if pitch_type in ("slider", "cutter"):
            x -= 0.05  # slides away from RHH
        elif pitch_type in ("changeup", "splitter"):
            y -= 0.08  # drops low
        elif pitch_type == "curveball":
            y -= 0.12  # big vertical drop
        elif pitch_type in ("sinker", "two_seam"):
            x += 0.03
            y -= 0.04

        # Count leverage adjustment
        leverage = _COUNT_LEVERAGE.get(count, {}).get("leverage", 0.5)
        if leverage >= 0.7:
            # Hitter ahead — can sit on a zone
            pass  # Keep tight PCI
        elif leverage <= 0.3:
            # Pitcher ahead — widen mental approach
            pass  # Keep default

        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))

        return PCIPlacement(
            user_id=user_id,
            target_zone=target_zone,
            pitch_type=pitch_type,
            pci_x=round(x, 3),
            pci_y=round(y, 3),
            count=count,
            note=(
                f"Zone {target_zone} vs {pitch_type}: PCI at ({x:.2f}, {y:.2f}). "
                f"{'Sit on this pitch — you have the count.' if leverage >= 0.7 else 'Protect the zone — two strikes.'}"
            ),
        )

    # ------------------------------------------------------------------
    # Count leverage
    # ------------------------------------------------------------------

    def get_count_leverage(self, count: str) -> CountLeverage:
        """Return the leverage value and recommended approach for a count."""
        data = _COUNT_LEVERAGE.get(count, {"leverage": 0.50, "approach": "neutral", "swing_pct": 0.35})

        advice: list[str] = []
        approach = data["approach"]
        if approach == "hitter_ahead":
            advice.append("Hitter's count — look for your pitch in your hot zone.")
            advice.append("Be selective — force the pitcher to come to you.")
        elif approach == "protect":
            advice.append("Two-strike approach — expand zone slightly, foul off tough pitches.")
            advice.append("Shorten your swing — contact over power.")
        elif approach == "full_count":
            advice.append("Full count — runner goes on pitch. Protect against anything close.")
        elif approach == "green_light_or_take":
            advice.append("3-0: Only swing at a cookie in your wheelhouse, otherwise take.")
        else:
            advice.append("Neutral count — stick to your gameplan pitch/zone.")

        return CountLeverage(
            count=count,
            leverage=data["leverage"],
            approach=approach,
            recommended_swing_pct=data["swing_pct"],
            advice=advice,
        )

    # ------------------------------------------------------------------
    # Swing recording and training plan
    # ------------------------------------------------------------------

    def record_swing(self, user_id: str, feedback: SwingFeedback) -> SwingResult:
        """Record a swing attempt and return updated stats."""
        self._swing_history[user_id].append(feedback)
        history = self._swing_history[user_id]

        total = len(history)
        hits = sum(1 for s in history if s.result in ("single", "double", "triple", "homer"))
        whiffs = sum(1 for s in history if s.result == "whiff")
        perfect_timings = sum(1 for s in history if s.timing_grade == "perfect")

        return SwingResult(
            user_id=user_id,
            total_swings=total,
            batting_avg=round(hits / max(total, 1), 3),
            whiff_rate=round(whiffs / max(total, 1), 3),
            perfect_timing_rate=round(perfect_timings / max(total, 1), 3),
            latest_result=feedback.result,
            latest_grade=feedback.timing_grade,
        )

    def generate_training_plan(
        self,
        user_id: str,
        target_avg: float = 0.300,
    ) -> HitTrainingPlan:
        """Generate a personalized hitting training plan."""
        history = self._swing_history.get(user_id, [])
        total = len(history)
        hits = sum(1 for s in history if s.result in ("single", "double", "triple", "homer"))
        current_avg = hits / max(total, 1)

        # Identify pitch-type weaknesses
        pitch_results: dict[str, dict[str, int]] = defaultdict(lambda: {"swings": 0, "hits": 0, "whiffs": 0})
        for s in history:
            pr = pitch_results[s.pitch_type]
            pr["swings"] += 1
            if s.result in ("single", "double", "triple", "homer"):
                pr["hits"] += 1
            if s.result == "whiff":
                pr["whiffs"] += 1

        weak_pitches = [
            pt for pt, r in pitch_results.items()
            if r["swings"] >= 5 and r["whiffs"] / r["swings"] >= 0.4
        ]
        strong_pitches = [
            pt for pt, r in pitch_results.items()
            if r["swings"] >= 5 and r["hits"] / r["swings"] >= 0.25
        ]

        drills: list[str] = []
        if weak_pitches:
            for wp in weak_pitches[:2]:
                tw = _TIMING_WINDOWS.get(wp, {})
                drills.append(
                    f"Batting practice vs {wp}: 30 reps. Optimal timing: {tw.get('optimal_ms', 450)}ms. "
                    f"Focus on recognizing the spin early."
                )
        drills.append("Live at-bats: 10 ABs with two-strike discipline. Foul off borderline pitches.")
        if current_avg < 0.200:
            drills.append("Timing drill: use practice mode at reduced speed to calibrate rhythm.")

        gap = max(target_avg - current_avg, 0.0)
        sessions = max(3, int(gap * 50))

        return HitTrainingPlan(
            user_id=user_id,
            current_avg=round(current_avg, 3),
            target_avg=target_avg,
            weak_pitches=weak_pitches,
            strong_pitches=strong_pitches,
            drills=drills,
            estimated_sessions=sessions,
            focus=(
                f"Focus on {weak_pitches[0]} recognition — your whiff rate is too high."
                if weak_pitches
                else "Solid contact skills. Work on situational hitting and count management."
            ),
        )


# Module-level singleton
hit_forge = HitForge()
