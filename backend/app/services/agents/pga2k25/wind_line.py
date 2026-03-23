"""WindLine AI — wind-adjusted club selection, trajectory control, carry vs total distance.

Converts raw wind conditions into actionable club selection and aim
adjustments, accounting for trajectory, elevation, and carry/total splits.
"""

from __future__ import annotations

import logging
import math
import uuid
from typing import Optional

from app.schemas.pga2k25.wind import (
    CarryTotalSplit,
    ShotConfidence,
    TrajectoryControl,
    TrajectoryType,
    WindAdjustedSelection,
    WindCondition,
    WindDirection,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Club distance tables (yards)
# ---------------------------------------------------------------------------

_CLUB_DISTANCES: list[tuple[str, float, float]] = [
    # (club_name, carry, total)
    ("LW", 70, 75),
    ("SW", 90, 95),
    ("GW", 105, 112),
    ("PW", 125, 133),
    ("9-iron", 138, 146),
    ("8-iron", 150, 158),
    ("7-iron", 162, 171),
    ("6-iron", 174, 184),
    ("5-iron", 186, 197),
    ("4-iron", 197, 210),
    ("3-iron", 208, 222),
    ("hybrid", 215, 230),
    ("5-wood", 225, 242),
    ("3-wood", 245, 262),
    ("driver", 275, 295),
]

# Wind direction effect vectors (headwind/tailwind component, crosswind component)
_WIND_VECTORS: dict[WindDirection, tuple[float, float]] = {
    WindDirection.HEADWIND: (-1.0, 0.0),
    WindDirection.TAILWIND: (1.0, 0.0),
    WindDirection.CROSSWIND_LEFT: (0.0, -1.0),
    WindDirection.CROSSWIND_RIGHT: (0.0, 1.0),
    WindDirection.N: (-0.7, 0.0),
    WindDirection.NE: (-0.5, 0.5),
    WindDirection.E: (0.0, 1.0),
    WindDirection.SE: (0.5, 0.5),
    WindDirection.S: (0.7, 0.0),
    WindDirection.SW: (0.5, -0.5),
    WindDirection.W: (0.0, -1.0),
    WindDirection.NW: (-0.5, -0.5),
}


class WindLineAI:
    """
    WindLine AI for PGA TOUR 2K25.

    Provides wind-adjusted club selection with trajectory recommendations.
    Core focus: ensuring the ball finishes on target despite wind by adjusting
    club, aim, and trajectory to minimize dispersion.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_wind_adjusted_selection(
        self,
        user_id: uuid.UUID,
        target_distance: float,
        wind: WindCondition,
        lie: str = "fairway",
        elevation_change: float = 0.0,
        club_preference: Optional[str] = None,
    ) -> WindAdjustedSelection:
        """Calculate wind-adjusted club selection and aim."""
        # Find base club for the target distance
        original_club = club_preference or self._select_club_for_distance(target_distance)

        # Calculate wind effect
        head_tail, cross = self._resolve_wind_vector(wind)
        carry_adj = self._calculate_carry_adjustment(wind.speed_mph, head_tail)
        total_adj = carry_adj * 1.1  # Wind affects total slightly more

        # Gust adjustment
        if wind.gusting and wind.gust_speed_mph:
            gust_extra = self._calculate_carry_adjustment(
                wind.gust_speed_mph - wind.speed_mph, head_tail,
            ) * 0.5
            carry_adj += gust_extra

        # Elevation adjustment (1 yard per 3 feet elevation)
        elev_adj = -elevation_change / 3.0

        # Effective distance accounting for wind and elevation
        wind_adjusted_distance = target_distance - carry_adj - elev_adj

        # Select adjusted club
        adjusted_club = self._select_club_for_distance(wind_adjusted_distance)

        # Get carry/total for the adjusted club
        carry, total = self._get_club_distances(adjusted_club)
        carry_total = CarryTotalSplit(
            carry_yards=carry,
            total_yards=total,
            roll_yards=round(total - carry, 1),
            wind_carry_adjustment=round(carry_adj, 1),
            wind_total_adjustment=round(total_adj, 1),
        )

        # Trajectory recommendation
        trajectory = self._recommend_trajectory(wind, lie)

        # Aim adjustment for crosswind
        aim = self._calculate_aim_adjustment(wind.speed_mph, cross)

        # Confidence assessment
        confidence = self._assess_confidence(wind, lie, trajectory)

        # Lie adjustment notes
        lie_note = self._lie_adjustment_note(lie)

        return WindAdjustedSelection(
            original_club=original_club,
            adjusted_club=adjusted_club,
            original_distance=target_distance,
            wind_adjusted_distance=round(wind_adjusted_distance, 1),
            carry_total=carry_total,
            trajectory=trajectory,
            aim_adjustment=aim,
            confidence=confidence,
            notes=lie_note,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _select_club_for_distance(distance: float) -> str:
        """Select the best club for a given distance."""
        best_club = _CLUB_DISTANCES[0][0]
        best_diff = abs(distance - _CLUB_DISTANCES[0][2])

        for club, carry, total in _CLUB_DISTANCES:
            diff = abs(distance - total)
            if diff < best_diff:
                best_diff = diff
                best_club = club
        return best_club

    @staticmethod
    def _get_club_distances(club_name: str) -> tuple[float, float]:
        """Get carry and total distances for a club."""
        for club, carry, total in _CLUB_DISTANCES:
            if club == club_name:
                return carry, total
        return 150.0, 160.0  # Default

    @staticmethod
    def _resolve_wind_vector(wind: WindCondition) -> tuple[float, float]:
        """Resolve wind into headwind/tailwind and crosswind components."""
        vector = _WIND_VECTORS.get(wind.direction, (0.0, 0.0))
        return vector[0], vector[1]

    @staticmethod
    def _calculate_carry_adjustment(speed_mph: float, head_tail_component: float) -> float:
        """Calculate carry distance adjustment from wind.

        Headwind effect is roughly 1.5x stronger than tailwind benefit
        due to increased backspin in headwinds.
        """
        if head_tail_component < 0:
            # Headwind: ~1.5 yards per mph into the wind
            return head_tail_component * speed_mph * 1.5
        else:
            # Tailwind: ~1.0 yards per mph with the wind
            return head_tail_component * speed_mph * 1.0

    @staticmethod
    def _recommend_trajectory(
        wind: WindCondition, lie: str,
    ) -> TrajectoryControl:
        """Recommend ball trajectory based on wind and lie."""
        if wind.speed_mph > 20:
            traj = TrajectoryType.STINGER
            reason = "Strong wind — keep the ball low to minimize wind exposure"
            apex = "low"
            exposure = 0.35
        elif wind.speed_mph > 12:
            traj = TrajectoryType.LOW
            reason = "Moderate wind — flight the ball down to reduce drift"
            apex = "low-mid"
            exposure = 0.55
        elif wind.speed_mph > 5:
            traj = TrajectoryType.MID
            reason = "Light wind — standard trajectory with slight adjustment"
            apex = "standard"
            exposure = 0.75
        else:
            traj = TrajectoryType.HIGH
            reason = "Calm conditions — maximize carry with normal trajectory"
            apex = "high"
            exposure = 0.90

        # Lie adjustments
        if lie in ("rough", "deep_rough"):
            traj = TrajectoryType.HIGH  # Rough forces higher trajectory
            reason += " (rough lie forces higher ball flight)"
            exposure = min(1.0, exposure + 0.15)

        spin_adj = None
        if wind.speed_mph > 15:
            spin_adj = "Reduce backspin — club down and swing easy"

        return TrajectoryControl(
            trajectory=traj,
            reason=reason,
            apex_height=apex,
            wind_exposure=round(exposure, 2),
            spin_adjustment=spin_adj,
        )

    @staticmethod
    def _calculate_aim_adjustment(speed_mph: float, cross_component: float) -> str:
        """Calculate lateral aim adjustment for crosswind."""
        if abs(cross_component) < 0.1:
            return "No crosswind — aim directly at target"

        # ~1 yard lateral drift per mph of crosswind
        drift_yards = abs(cross_component) * speed_mph * 1.0
        direction = "left" if cross_component > 0 else "right"

        if drift_yards < 2:
            return f"Minimal crosswind — aim ~{drift_yards:.0f} yard {direction} of target"
        if drift_yards < 8:
            return f"Aim {drift_yards:.0f} yards {direction} of target to compensate for crosswind"
        return f"Strong crosswind — aim {drift_yards:.0f} yards {direction} of target; consider shaping the shot into the wind"

    @staticmethod
    def _assess_confidence(
        wind: WindCondition, lie: str, trajectory: TrajectoryControl,
    ) -> ShotConfidence:
        """Assess confidence in executing the wind-adjusted shot."""
        risk_score = 0.0

        # Wind strength
        if wind.speed_mph > 20:
            risk_score += 0.4
        elif wind.speed_mph > 12:
            risk_score += 0.2
        elif wind.speed_mph > 5:
            risk_score += 0.1

        # Gusting
        if wind.gusting:
            risk_score += 0.2

        # Bad lie
        if lie in ("rough", "deep_rough", "bunker"):
            risk_score += 0.15

        if risk_score < 0.15:
            return ShotConfidence.HIGH
        if risk_score < 0.35:
            return ShotConfidence.MEDIUM
        if risk_score < 0.55:
            return ShotConfidence.LOW
        return ShotConfidence.RISKY

    @staticmethod
    def _lie_adjustment_note(lie: str) -> str:
        """Generate notes for lie-specific adjustments."""
        notes = {
            "fairway": "Clean lie — full shot control available",
            "rough": "Rough lie — expect reduced spin and less distance control; take one extra club",
            "deep_rough": "Deep rough — significantly reduced distance; club up 2 and swing hard",
            "bunker": "Bunker lie — open the face, aim for center of green",
            "tee": "Tee shot — full control; tee height affects trajectory",
            "fringe": "Fringe — consider putting or chipping depending on grain",
        }
        return notes.get(lie, "Non-standard lie — adjust expectations")
