"""RankedTours AI + SocietyScout — ranked environment tracking, Society-specific prep.

Tracks ranked progression, analyses performance across tour types, and
provides targeted preparation plans for Society events with course- and
condition-specific strategy.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.schemas.pga2k25.ranked import (
    CourseCondition,
    RankedEnvironment,
    RankedTier,
    SocietyPrep,
    TourReport,
    TourType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tier point thresholds
# ---------------------------------------------------------------------------

_TIER_THRESHOLDS: dict[RankedTier, int] = {
    RankedTier.BRONZE: 0,
    RankedTier.SILVER: 500,
    RankedTier.GOLD: 1200,
    RankedTier.PLATINUM: 2200,
    RankedTier.DIAMOND: 3500,
    RankedTier.LEGEND: 5000,
}


class RankedToursAI:
    """
    RankedTours AI + SocietyScout for PGA TOUR 2K25.

    Tracks ranked environment state, provides performance reports across
    tour types, and generates Society-specific preparation plans.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_ranked_status(
        self,
        user_id: uuid.UUID,
        tier_points: int = 0,
        recent_results: Optional[list[str]] = None,
        avg_score: float = 0.0,
    ) -> RankedEnvironment:
        """Get current ranked environment status."""
        tier = self._determine_tier(tier_points)
        next_tier = self._next_tier(tier)
        pts_to_next = self._points_to_next(tier_points, next_tier)

        results = recent_results or []
        win_rate = results.count("W") / max(len(results), 1)
        streak = self._calculate_streak(results)

        return RankedEnvironment(
            current_tier=tier,
            tier_points=tier_points,
            points_to_next_tier=pts_to_next,
            win_rate=round(win_rate, 2),
            avg_score_vs_par=avg_score,
            recent_form=results[-5:],
            streak=streak,
        )

    async def generate_tour_report(
        self,
        user_id: uuid.UUID,
        tour_type: TourType = TourType.RANKED_STROKE,
        events_played: int = 0,
        finishes: Optional[list[int]] = None,
        scores: Optional[list[float]] = None,
    ) -> TourReport:
        """Generate a performance report for a tour type."""
        _finishes = finishes or []
        _scores = scores or []

        avg_finish = sum(_finishes) / max(len(_finishes), 1) if _finishes else 0.0
        top_3 = sum(1 for f in _finishes if f <= 3) / max(len(_finishes), 1) if _finishes else 0.0
        scoring_avg = sum(_scores) / max(len(_scores), 1) if _scores else 0.0
        best = min(_finishes) if _finishes else 1
        worst = max(_finishes) if _finishes else 1

        # Clutch rating: how well they finish (improvement in final rounds)
        clutch = self._calculate_clutch_rating(_finishes, _scores)

        # Course type strength
        strength = self._determine_course_strength(scoring_avg)

        return TourReport(
            tour_type=tour_type,
            events_played=events_played or len(_finishes),
            avg_finish=round(avg_finish, 1),
            top_3_rate=round(top_3, 2),
            scoring_avg=round(scoring_avg, 1),
            best_finish=best,
            worst_finish=worst,
            clutch_rating=round(clutch, 2),
            course_type_strength=strength,
        )

    async def prepare_for_society(
        self,
        user_id: uuid.UUID,
        society_name: str,
        event_name: str,
        course_name: str,
        course_condition: CourseCondition = CourseCondition.STANDARD,
        field_size: int = 20,
    ) -> SocietyPrep:
        """Generate a Society event preparation plan."""
        field_strength = self._estimate_field_strength(field_size)
        strategy = self._build_event_strategy(course_condition, field_strength)
        notes = self._course_condition_notes(course_condition)
        target = self._calculate_scoring_target(field_strength, course_condition)
        key_holes = self._identify_key_holes(course_name)
        risk_level = self._determine_risk_level(field_strength, course_condition)
        checklist = self._build_prep_checklist(course_condition, course_name)

        return SocietyPrep(
            society_name=society_name,
            event_name=event_name,
            course_name=course_name,
            course_condition=course_condition,
            field_size=field_size,
            field_strength=round(field_strength, 2),
            recommended_strategy=strategy,
            course_notes=notes,
            scoring_target=round(target, 1),
            key_holes=key_holes,
            risk_level=risk_level,
            preparation_checklist=checklist,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _determine_tier(points: int) -> RankedTier:
        """Determine tier from points."""
        tier = RankedTier.BRONZE
        for t, threshold in _TIER_THRESHOLDS.items():
            if points >= threshold:
                tier = t
        return tier

    @staticmethod
    def _next_tier(current: RankedTier) -> Optional[RankedTier]:
        """Get the next tier."""
        tiers = list(RankedTier)
        idx = tiers.index(current)
        return tiers[idx + 1] if idx + 1 < len(tiers) else None

    @staticmethod
    def _points_to_next(current_points: int, next_tier: Optional[RankedTier]) -> int:
        """Calculate points needed for next tier."""
        if next_tier is None:
            return 0
        return max(0, _TIER_THRESHOLDS[next_tier] - current_points)

    @staticmethod
    def _calculate_streak(results: list[str]) -> int:
        """Calculate current win/loss streak."""
        if not results:
            return 0
        streak = 0
        last = results[-1]
        for r in reversed(results):
            if r == last:
                streak += 1
            else:
                break
        return streak if last == "W" else -streak

    @staticmethod
    def _calculate_clutch_rating(finishes: list[int], scores: list[float]) -> float:
        """Calculate clutch rating from performance data."""
        if not finishes:
            return 0.50

        # Weight recent results more heavily
        n = len(finishes)
        if n < 3:
            return 0.50

        # Compare second half to first half of results (improvement = clutch)
        mid = n // 2
        first_half_avg = sum(finishes[:mid]) / mid
        second_half_avg = sum(finishes[mid:]) / (n - mid)

        # Lower finish position = better, so improvement means second_half < first_half
        if first_half_avg > 0:
            improvement = (first_half_avg - second_half_avg) / first_half_avg
        else:
            improvement = 0.0

        return max(0.0, min(1.0, 0.50 + improvement))

    @staticmethod
    def _determine_course_strength(scoring_avg: float) -> str:
        """Determine what type of course the player performs best on."""
        if scoring_avg < -3:
            return "All course types — elite scoring"
        if scoring_avg < -1:
            return "Birdie-friendly courses with reachable par 5s"
        if scoring_avg < 1:
            return "Target golf courses requiring accuracy"
        return "Easier courses — need to improve on championship layouts"

    @staticmethod
    def _estimate_field_strength(field_size: int) -> float:
        """Estimate field strength from size (larger = potentially stronger)."""
        return min(1.0, 0.3 + (field_size / 100))

    @staticmethod
    def _build_event_strategy(condition: CourseCondition, field_strength: float) -> str:
        """Build strategic approach for the event."""
        parts: list[str] = []

        if condition == CourseCondition.FIRM_AND_FAST:
            parts.append("Play for roll-out; land short of targets and let the ball release.")
            parts.append("Avoid spinning the ball — bump-and-run approach shots.")
        elif condition == CourseCondition.SOFT:
            parts.append("Attack pins aggressively — balls will check up on approach.")
            parts.append("Take extra club as soft conditions reduce roll.")
        elif condition == CourseCondition.WINDY:
            parts.append("Control trajectory; keep the ball low in the wind.")
            parts.append("Play for position not distance; fairways matter more than ever.")
        elif condition == CourseCondition.TOURNAMENT:
            parts.append("Championship conditions — course management is paramount.")
            parts.append("Protect pars on difficult holes; attack easy ones.")
        else:
            parts.append("Standard conditions — balanced approach.")

        if field_strength > 0.7:
            parts.append("Strong field — need to be aggressive on birdie holes to keep pace.")
        else:
            parts.append("Moderate field — consistent bogey-free golf should contend.")

        return " ".join(parts)

    @staticmethod
    def _course_condition_notes(condition: CourseCondition) -> list[str]:
        """Generate condition-specific notes."""
        notes_map: dict[CourseCondition, list[str]] = {
            CourseCondition.STANDARD: [
                "Normal green speeds and fairway firmness",
                "Standard carry/roll ratios apply",
            ],
            CourseCondition.FIRM_AND_FAST: [
                "Greens are firm — land approach shots 10-15 yards short",
                "Fairways are running — expect 20+ yards of roll off the tee",
                "Uphill putts only — avoid leaving putts above the hole",
                "Bump-and-run is your friend around the greens",
            ],
            CourseCondition.SOFT: [
                "Greens are soft — attack pins directly",
                "Reduced roll — take one extra club on approaches",
                "Spin will grip — can be aggressive with wedges",
                "Fairway roll is minimal — driver distance reduced",
            ],
            CourseCondition.WINDY: [
                "Wind is the primary challenge — check conditions every shot",
                "Club selection must account for wind on every shot",
                "Lower trajectory shots reduce wind effect significantly",
                "Putting: wind affects long putts more than you think",
            ],
            CourseCondition.TOURNAMENT: [
                "Greens are fast and firm — precision is everything",
                "Pin positions will be difficult — aim for safe zones",
                "Course management wins tournaments — avoid big numbers",
                "Three-putt avoidance is the #1 priority on these greens",
            ],
        }
        return notes_map.get(condition, ["Standard conditions apply"])

    @staticmethod
    def _calculate_scoring_target(field_strength: float, condition: CourseCondition) -> float:
        """Calculate the scoring target needed to contend."""
        base = -2.0  # 2 under par baseline

        # Stronger field requires lower score
        base -= field_strength * 4

        # Conditions affect scoring
        condition_adj = {
            CourseCondition.STANDARD: 0.0,
            CourseCondition.FIRM_AND_FAST: 1.5,
            CourseCondition.SOFT: -1.0,
            CourseCondition.WINDY: 2.0,
            CourseCondition.TOURNAMENT: 1.0,
        }
        base += condition_adj.get(condition, 0.0)

        return base

    @staticmethod
    def _identify_key_holes(course_name: str) -> list[int]:
        """Identify key holes for a course (where the round is won or lost)."""
        # Course-specific key holes; default to standard swing holes
        course_keys: dict[str, list[int]] = {
            "east_lake": [2, 5, 9, 13, 15, 18],
            "tpc_sawgrass": [5, 8, 11, 14, 17, 18],
            "st_andrews": [1, 4, 11, 14, 17, 18],
            "pebble_beach": [6, 7, 8, 14, 17, 18],
        }
        key = course_name.lower().replace(" ", "_")
        return course_keys.get(key, [1, 5, 9, 13, 15, 18])

    @staticmethod
    def _determine_risk_level(field_strength: float, condition: CourseCondition) -> str:
        """Determine recommended risk level."""
        if condition in (CourseCondition.WINDY, CourseCondition.TOURNAMENT):
            return "conservative"
        if field_strength > 0.7:
            return "aggressive"
        if condition == CourseCondition.SOFT:
            return "aggressive"
        return "moderate"

    @staticmethod
    def _build_prep_checklist(condition: CourseCondition, course_name: str) -> list[str]:
        """Build a preparation checklist for the event."""
        checklist = [
            f"Play a practice round on {course_name} under {condition.value} conditions",
            "Review dispersion maps for all clubs — know your real distances",
            "Identify the 4-5 birdie holes and commit to attacking them",
            "Identify the 3-4 bogey danger holes and plan conservative lines",
            "Practice lag putting on the expected green speed",
        ]

        if condition == CourseCondition.WINDY:
            checklist.append("Practice low-trajectory stinger shots with irons")
            checklist.append("Rehearse wind-adjusted club selection with WindLine AI")

        if condition == CourseCondition.FIRM_AND_FAST:
            checklist.append("Practice bump-and-run chips around the green")
            checklist.append("Hit approach shots landing short and rolling to the pin")

        checklist.append("Set a pre-round routine: warm up, check wind, review strategy")
        return checklist
