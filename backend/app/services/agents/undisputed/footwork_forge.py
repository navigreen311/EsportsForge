"""FootworkForge — ring position optimizer, rope trap detection, and cut-off angle calculator.

Provides ring control AI including optimal positioning, rope/corner trap
recognition, cutting off the ring, and lateral movement recommendations.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from app.schemas.undisputed.boxing import (
    CutOffAngle,
    RingPosition,
    RingPositionAnalysis,
    RopeTracker,
    RingZone,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ring geometry (normalized 0-1 coordinate space, center = 0.5, 0.5)
# ---------------------------------------------------------------------------

_RING_CENTER = (0.5, 0.5)
_RING_RADIUS = 0.45  # Usable ring area
_ROPE_ZONE_THRESHOLD = 0.38  # Distance from center where ropes begin
_CORNER_POSITIONS = [(0.1, 0.1), (0.1, 0.9), (0.9, 0.1), (0.9, 0.9)]

# Zone classification thresholds
_ZONE_THRESHOLDS: dict[RingZone, tuple[float, float]] = {
    RingZone.CENTER: (0.0, 0.20),
    RingZone.MID_RING: (0.20, 0.35),
    RingZone.ROPES: (0.35, 0.43),
    RingZone.CORNER: (0.43, 1.0),
}


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _classify_zone(x: float, y: float) -> RingZone:
    dist_from_center = _distance((x, y), _RING_CENTER)
    for zone, (lo, hi) in _ZONE_THRESHOLDS.items():
        if lo <= dist_from_center < hi:
            return zone
    return RingZone.CORNER


class FootworkForge:
    """Undisputed ring positioning and footwork engine.

    Analyzes ring position quality, detects rope/corner traps,
    calculates cut-off angles, and recommends lateral movement.
    """

    # ------------------------------------------------------------------
    # Ring position analysis
    # ------------------------------------------------------------------

    def analyze_position(
        self,
        player_x: float,
        player_y: float,
        opponent_x: float,
        opponent_y: float,
    ) -> RingPositionAnalysis:
        """Analyze current ring positions and rate control quality.

        Returns zone classification, control score, and movement recommendations.
        """
        player_zone = _classify_zone(player_x, player_y)
        opponent_zone = _classify_zone(opponent_x, opponent_y)
        distance = _distance((player_x, player_y), (opponent_x, opponent_y))

        # Control score: higher = better position
        player_dist = _distance((player_x, player_y), _RING_CENTER)
        opponent_dist = _distance((opponent_x, opponent_y), _RING_CENTER)

        # Being closer to center is better
        position_score = max(0, 1.0 - player_dist / _RING_RADIUS) * 0.5
        # Opponent being farther from center is better
        position_score += min(1.0, opponent_dist / _RING_RADIUS) * 0.3
        # Distance management
        if 0.15 <= distance <= 0.35:
            position_score += 0.2  # Optimal fighting distance
        elif distance < 0.10:
            position_score += 0.05  # Too close — clinch range
        else:
            position_score += 0.1

        position_score = min(1.0, position_score)

        # Recommendations
        recommendations: list[str] = []
        if player_zone == RingZone.CORNER:
            recommendations.append("URGENT: You are in the corner. Pivot out immediately.")
            recommendations.append("Use a jab and lateral step to escape to the center.")
        elif player_zone == RingZone.ROPES:
            recommendations.append("On the ropes — create angles to move back to center ring.")
            recommendations.append("Clinch or pivot to reset your position.")
        elif player_zone == RingZone.CENTER:
            recommendations.append("Excellent position — you control the center. Dictate range.")

        if opponent_zone in (RingZone.ROPES, RingZone.CORNER):
            recommendations.append(f"Opponent is on the {opponent_zone.value} — press forward and cut off escape.")
        if distance > 0.40:
            recommendations.append("Too far away — close distance with the jab to establish range.")
        elif distance < 0.10:
            recommendations.append("Clinch range — either clinch or create separation with a push-off.")

        return RingPositionAnalysis(
            player_position=RingPosition(x=player_x, y=player_y, zone=player_zone),
            opponent_position=RingPosition(x=opponent_x, y=opponent_y, zone=opponent_zone),
            distance=round(distance, 3),
            control_score=round(position_score, 3),
            recommendations=recommendations,
        )

    # ------------------------------------------------------------------
    # Rope trap detection
    # ------------------------------------------------------------------

    def detect_rope_trap(
        self,
        player_x: float,
        player_y: float,
        opponent_x: float,
        opponent_y: float,
        opponent_pressure: float = 0.5,
    ) -> RopeTracker:
        """Detect if the player is being trapped on the ropes or in a corner.

        Evaluates proximity to ropes, opponent pressure angle, and escape routes.
        """
        player_zone = _classify_zone(player_x, player_y)
        dist_to_center = _distance((player_x, player_y), _RING_CENTER)

        is_trapped = False
        trap_severity = 0.0
        escape_routes: list[str] = []

        if player_zone in (RingZone.ROPES, RingZone.CORNER):
            # Check if opponent is blocking the center
            opp_to_center = _distance((opponent_x, opponent_y), _RING_CENTER)
            if opp_to_center < dist_to_center:
                is_trapped = True
                trap_severity = min(1.0, 0.5 + opponent_pressure * 0.3 + (dist_to_center - opp_to_center) * 0.5)

        # Nearest corners (worst traps)
        nearest_corner_dist = min(_distance((player_x, player_y), c) for c in _CORNER_POSITIONS)
        if nearest_corner_dist < 0.15:
            trap_severity = min(1.0, trap_severity + 0.3)
            is_trapped = True

        # Escape route suggestions
        if is_trapped:
            # Calculate escape vectors
            dx = _RING_CENTER[0] - player_x
            dy = _RING_CENTER[1] - player_y

            if abs(dx) > abs(dy):
                escape_routes.append("Pivot LEFT" if dx > 0 else "Pivot RIGHT")
            else:
                escape_routes.append("Step FORWARD" if dy > 0 else "Step BACK")

            escape_routes.append("Clinch to reset position")
            escape_routes.append("Jab and circle away from the ropes")
            if trap_severity > 0.7:
                escape_routes.append("EMERGENCY: Smother and grab — you need to survive this exchange")
        else:
            escape_routes.append("Not trapped — maintain position or advance.")

        return RopeTracker(
            is_trapped=is_trapped,
            trap_severity=round(trap_severity, 3),
            player_zone=player_zone,
            nearest_corner_distance=round(nearest_corner_dist, 3),
            escape_routes=escape_routes,
        )

    # ------------------------------------------------------------------
    # Cut-off angle calculator
    # ------------------------------------------------------------------

    def calculate_cutoff_angle(
        self,
        player_x: float,
        player_y: float,
        opponent_x: float,
        opponent_y: float,
        opponent_likely_direction: str = "left",
    ) -> CutOffAngle:
        """Calculate the optimal angle to cut off an opponent's escape.

        Returns the movement vector and step recommendation to cut off the ring.
        """
        # Opponent's likely escape vector
        escape_vectors: dict[str, tuple[float, float]] = {
            "left": (-0.1, 0.0),
            "right": (0.1, 0.0),
            "backward": (0.0, -0.1 if opponent_y > 0.5 else 0.1),
            "pivot_left": (-0.07, 0.07),
            "pivot_right": (0.07, 0.07),
        }

        escape = escape_vectors.get(opponent_likely_direction, (-0.1, 0.0))
        predicted_x = opponent_x + escape[0]
        predicted_y = opponent_y + escape[1]

        # Intercept point: move toward where they will be
        intercept_dx = predicted_x - player_x
        intercept_dy = predicted_y - player_y
        dist = max(0.01, math.sqrt(intercept_dx ** 2 + intercept_dy ** 2))
        step_size = 0.08

        move_x = round(intercept_dx / dist * step_size, 3)
        move_y = round(intercept_dy / dist * step_size, 3)

        # Angle in degrees
        angle = round(math.degrees(math.atan2(intercept_dy, intercept_dx)), 1)

        recommendation = "Step"
        if abs(move_x) > abs(move_y):
            recommendation = f"Lateral step {'right' if move_x > 0 else 'left'} to cut off the ring"
        else:
            recommendation = f"Step {'forward' if move_y > 0 else 'back'} to close the angle"

        return CutOffAngle(
            angle_degrees=angle,
            move_x=move_x,
            move_y=move_y,
            opponent_likely_direction=opponent_likely_direction,
            recommendation=recommendation,
            intercept_position=RingPosition(
                x=round(player_x + move_x, 3),
                y=round(player_y + move_y, 3),
                zone=_classify_zone(player_x + move_x, player_y + move_y),
            ),
        )

    # ------------------------------------------------------------------
    # Lateral movement recommendation
    # ------------------------------------------------------------------

    def recommend_movement(
        self,
        player_stance: str = "orthodox",
        opponent_pressure: float = 0.5,
        current_zone: RingZone = RingZone.CENTER,
    ) -> dict[str, Any]:
        """Recommend lateral movement based on stance, pressure, and position."""
        recommendations: dict[str, Any] = {
            "stance": player_stance,
            "pressure_level": opponent_pressure,
            "zone": current_zone.value,
            "moves": [],
        }

        if current_zone == RingZone.CENTER:
            if opponent_pressure > 0.7:
                recommendations["moves"].append("Pivot away from pressure — maintain center control.")
                recommendations["moves"].append("Use the jab to re-establish distance.")
            else:
                recommendations["moves"].append("Hold your ground — you own the center.")
                recommendations["moves"].append("Small lateral steps to create punching angles.")
        elif current_zone == RingZone.ROPES:
            recommendations["moves"].append("Circle toward center ring immediately.")
            if player_stance == "orthodox":
                recommendations["moves"].append("Pivot to your LEFT to escape — step with lead foot first.")
            else:
                recommendations["moves"].append("Pivot to your RIGHT to escape — step with lead foot first.")
        elif current_zone == RingZone.CORNER:
            recommendations["moves"].append("EMERGENCY: Pivot out of the corner NOW.")
            recommendations["moves"].append("Lower your level, fire a body shot, and pivot out.")

        return recommendations


# Module-level singleton
footwork_forge = FootworkForge()
