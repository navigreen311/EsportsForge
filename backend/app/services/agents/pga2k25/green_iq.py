"""GreenIQ — read quality, pace control, three-putt risk, pressure putting mode.

Putting intelligence focused on eliminating three-putts and optimizing
pace control for consistent two-putt management under all conditions.
"""

from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.schemas.pga2k25.green import (
    GreenRead,
    GreenSpeed,
    PaceControl,
    PressurePuttingMode,
    PuttAnalysis,
    PuttDifficulty,
    SlopeDirection,
    ThreePuttRisk,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Green speed factors (stimpmeter-based adjustments)
# ---------------------------------------------------------------------------

_SPEED_FACTORS: dict[GreenSpeed, dict[str, float]] = {
    GreenSpeed.SLOW: {"power_mult": 1.15, "break_mult": 0.75, "three_putt_adj": -0.05},
    GreenSpeed.MEDIUM: {"power_mult": 1.0, "break_mult": 1.0, "three_putt_adj": 0.0},
    GreenSpeed.FAST: {"power_mult": 0.85, "break_mult": 1.25, "three_putt_adj": 0.08},
    GreenSpeed.TOURNAMENT: {"power_mult": 0.75, "break_mult": 1.45, "three_putt_adj": 0.15},
}


class GreenIQ:
    """
    GreenIQ for PGA TOUR 2K25.

    Provides green reading intelligence, pace control recommendations,
    and three-putt risk management.  Under pressure, automatically shifts
    to conservative putting modes that protect against three-putts.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze_putt(
        self,
        user_id: uuid.UUID,
        course_name: str,
        hole_number: int,
        distance_feet: float,
        pin_position: str = "center",
        green_speed: GreenSpeed = GreenSpeed.MEDIUM,
        include_pressure: bool = True,
    ) -> PuttAnalysis:
        """Generate a complete putting analysis."""
        read = self._calculate_read(distance_feet, pin_position, green_speed)
        pace = self._calculate_pace(distance_feet, read, green_speed)
        three_putt = self._assess_three_putt_risk(distance_feet, green_speed, read)
        difficulty = self._classify_difficulty(distance_feet)
        make_prob = self._calculate_make_probability(distance_feet, green_speed)

        # Pressure mode selection
        pressure_mode = PressurePuttingMode.SAFE_TWO_PUTT
        pressure_adj: Optional[str] = None
        if include_pressure:
            pressure_mode, pressure_adj = self._select_pressure_mode(
                distance_feet, three_putt, difficulty,
            )

        # Read quality based on distance and slope complexity
        read_quality = self._calculate_read_quality(distance_feet, read)

        return PuttAnalysis(
            hole_number=hole_number,
            course_name=course_name,
            green_speed=green_speed,
            read=read,
            pace=pace,
            three_putt_risk=three_putt,
            difficulty=difficulty,
            make_probability=round(make_prob, 3),
            pressure_mode=pressure_mode,
            pressure_adjustment=pressure_adj,
            read_quality_score=round(read_quality, 2),
            confidence=0.77,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    async def get_three_putt_risk(
        self,
        distance_feet: float,
        green_speed: GreenSpeed = GreenSpeed.MEDIUM,
    ) -> ThreePuttRisk:
        """Quick three-putt risk assessment."""
        read = self._calculate_read(distance_feet, "center", green_speed)
        return self._assess_three_putt_risk(distance_feet, green_speed, read)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _calculate_read(
        self,
        distance_feet: float,
        pin_position: str,
        speed: GreenSpeed,
    ) -> GreenRead:
        """Calculate the green read."""
        speed_factor = _SPEED_FACTORS[speed]

        # Determine slope based on pin position
        slope = self._infer_slope(pin_position)

        # Break amount scales with distance and speed
        base_break = distance_feet * 0.08  # Base break in inches
        break_amount = base_break * speed_factor["break_mult"]

        # Elevation change estimate
        elevation = self._estimate_elevation(pin_position, distance_feet)

        # Aim point
        aim = self._calculate_aim_point(slope, break_amount)

        return GreenRead(
            distance_feet=distance_feet,
            slope_direction=slope,
            break_amount=round(break_amount, 1),
            elevation_change=round(elevation, 1),
            aim_point=aim,
            grain_effect=self._grain_effect(slope),
        )

    @staticmethod
    def _calculate_pace(
        distance_feet: float,
        read: GreenRead,
        speed: GreenSpeed,
    ) -> PaceControl:
        """Calculate pace control recommendations."""
        speed_factor = _SPEED_FACTORS[speed]

        # Base power scales with distance
        base_power = min(100.0, (distance_feet / 60.0) * 100.0)
        recommended_power = base_power * speed_factor["power_mult"]

        # Uphill needs more power, downhill less
        if read.elevation_change > 0:
            recommended_power *= 1 + (read.elevation_change * 0.03)
        elif read.elevation_change < 0:
            recommended_power *= 1 + (read.elevation_change * 0.05)  # More reduction downhill

        recommended_power = max(5.0, min(100.0, recommended_power))

        # Leave distance (how far past the hole if missed)
        leave_dist = max(0.5, distance_feet * 0.05 * speed_factor["power_mult"])

        # Comeback putt difficulty
        if leave_dist < 2:
            comeback = PuttDifficulty.TAP_IN
        elif leave_dist < 4:
            comeback = PuttDifficulty.MAKEABLE
        else:
            comeback = PuttDifficulty.CHALLENGING

        # Tolerance window
        tolerance = max(2.0, 8.0 - (distance_feet * 0.1))

        return PaceControl(
            recommended_power=round(recommended_power, 1),
            leave_distance=round(leave_dist, 1),
            comeback_difficulty=comeback,
            speed_tolerance=round(tolerance, 1),
        )

    @staticmethod
    def _assess_three_putt_risk(
        distance_feet: float,
        speed: GreenSpeed,
        read: GreenRead,
    ) -> ThreePuttRisk:
        """Assess three-putt probability."""
        speed_factor = _SPEED_FACTORS[speed]

        # Base three-putt risk scales exponentially with distance
        if distance_feet < 10:
            base_risk = 0.02
        elif distance_feet < 20:
            base_risk = 0.05
        elif distance_feet < 30:
            base_risk = 0.12
        elif distance_feet < 40:
            base_risk = 0.22
        elif distance_feet < 50:
            base_risk = 0.30
        else:
            base_risk = min(0.60, 0.30 + (distance_feet - 50) * 0.006)

        # Adjust for green speed
        risk = base_risk + speed_factor["three_putt_adj"]

        # Adjust for slope complexity
        if read.slope_direction == SlopeDirection.DOUBLE_BREAK:
            risk += 0.08
        if read.slope_direction == SlopeDirection.DOWNHILL:
            risk += 0.05

        risk = max(0.0, min(1.0, risk))

        # Risk level
        if risk < 0.10:
            level = "low"
        elif risk < 0.20:
            level = "medium"
        elif risk < 0.35:
            level = "high"
        else:
            level = "extreme"

        # Primary cause
        if distance_feet > 40:
            cause = "Distance — lag putt accuracy decreases beyond 40 feet"
        elif speed in (GreenSpeed.FAST, GreenSpeed.TOURNAMENT):
            cause = "Green speed — fast greens amplify pace errors"
        elif read.slope_direction in (SlopeDirection.DOUBLE_BREAK, SlopeDirection.DOWNHILL):
            cause = "Slope complexity — difficult to judge pace on this terrain"
        else:
            cause = "Read misjudgment — break estimation is the primary risk factor"

        # Mitigation
        if risk > 0.25:
            mitigation = "Lag to 3-foot circle; accept two-putt and move on"
        elif risk > 0.15:
            mitigation = "Focus on pace over line; leave it within tap-in range"
        else:
            mitigation = "Normal putting routine; trust your read"

        return ThreePuttRisk(
            probability=round(risk, 3),
            risk_level=level,
            primary_cause=cause,
            mitigation=mitigation,
        )

    @staticmethod
    def _classify_difficulty(distance_feet: float) -> PuttDifficulty:
        """Classify putt difficulty by distance."""
        if distance_feet < 3:
            return PuttDifficulty.TAP_IN
        if distance_feet < 10:
            return PuttDifficulty.MAKEABLE
        if distance_feet < 25:
            return PuttDifficulty.CHALLENGING
        if distance_feet < 50:
            return PuttDifficulty.LAG
        return PuttDifficulty.HEROIC

    @staticmethod
    def _calculate_make_probability(distance_feet: float, speed: GreenSpeed) -> float:
        """Calculate probability of making the putt."""
        # PGA Tour make percentages approximation
        if distance_feet <= 3:
            base = 0.96
        elif distance_feet <= 5:
            base = 0.77
        elif distance_feet <= 8:
            base = 0.55
        elif distance_feet <= 10:
            base = 0.40
        elif distance_feet <= 15:
            base = 0.25
        elif distance_feet <= 20:
            base = 0.15
        elif distance_feet <= 30:
            base = 0.08
        else:
            base = max(0.01, 0.08 * math.exp(-0.03 * (distance_feet - 30)))

        # Fast greens reduce make probability slightly
        if speed in (GreenSpeed.FAST, GreenSpeed.TOURNAMENT):
            base *= 0.90

        return max(0.01, min(0.99, base))

    @staticmethod
    def _select_pressure_mode(
        distance_feet: float,
        three_putt: ThreePuttRisk,
        difficulty: PuttDifficulty,
    ) -> tuple[PressurePuttingMode, str]:
        """Select the optimal putting mode under pressure."""
        if difficulty == PuttDifficulty.TAP_IN:
            return PressurePuttingMode.AGGRESSIVE, "Tap-in range — be decisive"

        if three_putt.probability > 0.25:
            return (
                PressurePuttingMode.LAG_AND_TAP,
                "High three-putt risk — lag to safe distance and tap in",
            )

        if difficulty == PuttDifficulty.LAG or difficulty == PuttDifficulty.HEROIC:
            return (
                PressurePuttingMode.SAFE_TWO_PUTT,
                "Long putt under pressure — prioritize two-putt",
            )

        if distance_feet < 8:
            return (
                PressurePuttingMode.DIE_IN_HOLE,
                "Makeable range — aim to die the ball in the hole for maximum capture zone",
            )

        return (
            PressurePuttingMode.SAFE_TWO_PUTT,
            "Medium distance under pressure — safe two-putt is the smart play",
        )

    @staticmethod
    def _infer_slope(pin_position: str) -> SlopeDirection:
        """Infer slope direction from pin position description."""
        pos = pin_position.lower()
        if "back" in pos and "left" in pos:
            return SlopeDirection.UPHILL
        if "back" in pos:
            return SlopeDirection.UPHILL
        if "front" in pos:
            return SlopeDirection.DOWNHILL
        if "left" in pos:
            return SlopeDirection.LEFT_TO_RIGHT
        if "right" in pos:
            return SlopeDirection.RIGHT_TO_LEFT
        return SlopeDirection.FLAT

    @staticmethod
    def _estimate_elevation(pin_position: str, distance: float) -> float:
        """Estimate elevation change based on position and distance."""
        pos = pin_position.lower()
        per_foot = 0.02  # feet of elevation per foot of distance
        if "back" in pos:
            return distance * per_foot
        if "front" in pos:
            return -distance * per_foot
        return 0.0

    @staticmethod
    def _calculate_aim_point(slope: SlopeDirection, break_inches: float) -> str:
        """Convert slope and break into an aim point description."""
        cups = break_inches / 4.25  # hole diameter in inches

        direction_map = {
            SlopeDirection.LEFT_TO_RIGHT: "left",
            SlopeDirection.RIGHT_TO_LEFT: "right",
            SlopeDirection.UPHILL: "firm center",
            SlopeDirection.DOWNHILL: "soft center",
            SlopeDirection.DOUBLE_BREAK: "outside the first break",
            SlopeDirection.FLAT: "center",
        }

        direction = direction_map.get(slope, "center")

        if cups < 0.5:
            return f"Inside {direction} edge"
        if cups < 1.5:
            return f"1 cup {direction}"
        if cups < 3:
            return f"{cups:.0f} cups {direction}"
        return f"{cups:.0f} cups {direction} — large break"

    @staticmethod
    def _grain_effect(slope: SlopeDirection) -> Optional[str]:
        """Estimate grain effect based on typical bermuda conditions."""
        if slope in (SlopeDirection.DOWNHILL,):
            return "With grain downhill — reduce power by 5%"
        if slope in (SlopeDirection.UPHILL,):
            return "Against grain uphill — add 5% power"
        return None

    @staticmethod
    def _calculate_read_quality(distance_feet: float, read: GreenRead) -> float:
        """Score the confidence in the read (0-1)."""
        # Shorter putts are easier to read
        dist_factor = max(0.3, 1.0 - (distance_feet / 80))

        # Flat reads are more confident
        slope_penalty = {
            SlopeDirection.FLAT: 0.0,
            SlopeDirection.UPHILL: 0.05,
            SlopeDirection.DOWNHILL: 0.08,
            SlopeDirection.LEFT_TO_RIGHT: 0.05,
            SlopeDirection.RIGHT_TO_LEFT: 0.05,
            SlopeDirection.DOUBLE_BREAK: 0.15,
        }
        penalty = slope_penalty.get(read.slope_direction, 0.05)

        return max(0.3, min(1.0, dist_factor - penalty))
