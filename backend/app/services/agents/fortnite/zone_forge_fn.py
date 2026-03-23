"""ZoneForge FN — storm rotation optimizer, zone tax calculator, third-party positioning.

Analyzes optimal rotation paths, calculates the 'zone tax' of being out of position,
and identifies third-party fight risk zones during rotations.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from app.schemas.fortnite.gameplay import (
    MaterialType,
    PlayerPosition,
    RotationPlan,
    RotationStyle,
    StormState,
    ZonePhase,
    ZoneTax,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Zone phase parameters
# ---------------------------------------------------------------------------

ZONE_DAMAGE_TABLE: dict[ZonePhase, float] = {
    ZonePhase.EARLY_GAME: 1.0,
    ZonePhase.FIRST_ZONE: 1.0,
    ZonePhase.SECOND_ZONE: 2.0,
    ZonePhase.THIRD_ZONE: 5.0,
    ZonePhase.FOURTH_ZONE: 8.0,
    ZonePhase.MOVING_ZONE: 10.0,
    ZonePhase.HALF_HALF: 10.0,
    ZonePhase.ENDGAME: 10.0,
}

# Material cost per 100 units of distance
MATERIAL_COST_PER_100: dict[RotationStyle, int] = {
    RotationStyle.EARLY_ROTATE: 50,
    RotationStyle.EDGE_ROTATE: 150,
    RotationStyle.TARPING: 300,
    RotationStyle.TUNNELING: 400,
    RotationStyle.LAUNCH_PAD: 20,
    RotationStyle.VEHICLE_ROTATE: 0,
    RotationStyle.STORM_SURGE_PLAY: 100,
}

# Alive player thresholds for third-party risk
THIRD_PARTY_HIGH_RISK_THRESHOLD = 50
THIRD_PARTY_EXTREME_THRESHOLD = 30


class ZoneForgeFN:
    """Storm rotation optimizer with zone tax calculation.

    Recommends rotation style, calculates material / health / fight costs
    of different paths, and identifies high-risk third-party zones.
    """

    # ------------------------------------------------------------------
    # Distance utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
        """Euclidean distance between two 2D points."""
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    @staticmethod
    def _lerp(
        p1: tuple[float, float],
        p2: tuple[float, float],
        t: float,
    ) -> tuple[float, float]:
        """Linear interpolation between two points."""
        return (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)

    # ------------------------------------------------------------------
    # Zone tax calculation
    # ------------------------------------------------------------------

    def calculate_zone_tax(
        self,
        storm: StormState,
        player: PlayerPosition,
    ) -> ZoneTax:
        """Calculate the zone tax — cost of the player's current position.

        Considers distance to zone, materials needed, storm damage risk,
        and third-party fight probability.
        """
        player_pos = (player.x, player.y)
        dist_to_center = self._distance(player_pos, storm.safe_zone_center)
        in_zone = dist_to_center <= storm.safe_zone_radius

        # Health risk: based on whether player is in zone and storm damage
        if in_zone:
            health_risk = 0.0
        else:
            overflow = dist_to_center - storm.safe_zone_radius
            time_to_reach = overflow / 50.0  # assume ~50 units/sec movement
            ticks_in_storm = max(0, time_to_reach - storm.seconds_until_close)
            potential_damage = max(0.0, ticks_in_storm * storm.storm_damage_per_tick)
            health_risk = min(1.0, potential_damage / (player.health + player.shield))

        # Material cost estimate
        dist_to_safe = max(0.0, dist_to_center - storm.safe_zone_radius)
        base_mat_cost = int(dist_to_safe * 1.5)  # ~1.5 mats per unit of distance
        total_mats = sum(player.materials.values())
        material_cost = min(base_mat_cost, total_mats)

        # Third-party fight probability
        fight_prob = self._third_party_probability(
            player.alive_players, storm.zone_phase, dist_to_safe
        )

        # Time pressure
        if storm.seconds_until_close <= 0:
            time_pressure = 1.0
        elif storm.seconds_until_close < 15:
            time_pressure = 0.9
        elif storm.seconds_until_close < 30:
            time_pressure = 0.6
        elif storm.seconds_until_close < 60:
            time_pressure = 0.3
        else:
            time_pressure = max(0.0, 0.1 * (dist_to_safe / max(storm.safe_zone_radius, 1)))

        total_tax = round(
            health_risk * 0.35 + fight_prob * 0.30 + time_pressure * 0.25
            + (material_cost / max(total_mats, 1)) * 0.10,
            3,
        )

        return ZoneTax(
            material_cost=material_cost,
            health_risk=round(health_risk, 3),
            fight_probability=round(fight_prob, 3),
            time_pressure=round(time_pressure, 3),
            total_tax_score=min(1.0, total_tax),
        )

    def _third_party_probability(
        self,
        alive_players: int,
        phase: ZonePhase,
        dist_outside_zone: float,
    ) -> float:
        """Estimate third-party fight probability during rotation."""
        base = 0.1

        # More players alive = higher risk
        if alive_players > THIRD_PARTY_HIGH_RISK_THRESHOLD:
            base += 0.2
        elif alive_players > THIRD_PARTY_EXTREME_THRESHOLD:
            base += 0.35
        else:
            base += 0.15

        # Late zones = congestion = more third-partying
        if phase in (ZonePhase.MOVING_ZONE, ZonePhase.HALF_HALF, ZonePhase.ENDGAME):
            base += 0.25
        elif phase in (ZonePhase.THIRD_ZONE, ZonePhase.FOURTH_ZONE):
            base += 0.15

        # Being outside zone during rotation increases exposure
        if dist_outside_zone > 200:
            base += 0.15
        elif dist_outside_zone > 100:
            base += 0.08

        return min(1.0, base)

    # ------------------------------------------------------------------
    # Rotation recommendation
    # ------------------------------------------------------------------

    def recommend_rotation(
        self,
        storm: StormState,
        player: PlayerPosition,
    ) -> RotationStyle:
        """Recommend the best rotation style given game state."""
        player_pos = (player.x, player.y)
        dist = self._distance(player_pos, storm.safe_zone_center)
        in_zone = dist <= storm.safe_zone_radius
        total_mats = sum(player.materials.values())

        # Early game / already in zone -> no rotation needed or early rotate
        if in_zone and storm.zone_phase in (ZonePhase.EARLY_GAME, ZonePhase.FIRST_ZONE):
            return RotationStyle.EARLY_ROTATE

        # Has mobility item -> use it
        if player.has_mobility_item and not in_zone:
            return RotationStyle.LAUNCH_PAD

        # Late game with lots of mats -> tarping or tunneling
        if storm.zone_phase in (ZonePhase.MOVING_ZONE, ZonePhase.HALF_HALF, ZonePhase.ENDGAME):
            if total_mats >= 500:
                return RotationStyle.TARPING
            elif total_mats >= 200:
                return RotationStyle.TUNNELING
            else:
                return RotationStyle.STORM_SURGE_PLAY

        # Mid-game: edge rotate if mats available, otherwise early rotate
        if total_mats >= 300:
            return RotationStyle.EDGE_ROTATE
        else:
            return RotationStyle.EARLY_ROTATE

    # ------------------------------------------------------------------
    # Generate rotation plan
    # ------------------------------------------------------------------

    def generate_rotation_plan(
        self,
        user_id: str,
        storm: StormState,
        player: PlayerPosition,
    ) -> RotationPlan:
        """Generate a full rotation plan with waypoints and risk zones."""
        zone_tax = self.calculate_zone_tax(storm, player)
        style = self.recommend_rotation(storm, player)

        player_pos = (player.x, player.y)
        target = storm.safe_zone_center

        # Generate waypoints (intermediate positions)
        waypoints = self._generate_waypoints(player_pos, target, storm)

        # Identify third-party risk zones
        risk_zones = self._identify_risk_zones(player_pos, target, player.alive_players)

        # Priority actions
        actions = self._build_priority_actions(storm, player, zone_tax, style)

        # Confidence based on zone tax
        confidence = max(0.1, 1.0 - zone_tax.total_tax_score)

        return RotationPlan(
            user_id=user_id,
            storm_state=storm,
            player_position=player,
            recommended_style=style,
            zone_tax=zone_tax,
            path_waypoints=waypoints,
            third_party_risk_zones=risk_zones,
            priority_actions=actions,
            confidence=round(confidence, 3),
        )

    def _generate_waypoints(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        storm: StormState,
    ) -> list[tuple[float, float]]:
        """Generate intermediate waypoints avoiding storm center."""
        dist = self._distance(start, end)
        if dist < 50:
            return [end]

        num_points = max(2, min(5, int(dist / 100)))
        waypoints: list[tuple[float, float]] = []
        for i in range(1, num_points + 1):
            t = i / num_points
            point = self._lerp(start, end, t)
            # Slight offset to avoid straight-line predictability
            offset = 20.0 * (1 if i % 2 == 0 else -1)
            dx = end[1] - start[1]
            dy = -(end[0] - start[0])
            length = math.sqrt(dx * dx + dy * dy) or 1.0
            waypoints.append((
                round(point[0] + offset * dx / length, 1),
                round(point[1] + offset * dy / length, 1),
            ))

        return waypoints

    def _identify_risk_zones(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        alive_players: int,
    ) -> list[tuple[float, float]]:
        """Identify positions along the path with high third-party risk.

        Risk zones are typically at midpoints, named POIs, and zone edges.
        """
        midpoint = self._lerp(start, end, 0.5)
        risk_zones = [midpoint]

        # Quarter points for longer rotations
        dist = self._distance(start, end)
        if dist > 200:
            risk_zones.append(self._lerp(start, end, 0.25))
            risk_zones.append(self._lerp(start, end, 0.75))

        return [(round(z[0], 1), round(z[1], 1)) for z in risk_zones]

    def _build_priority_actions(
        self,
        storm: StormState,
        player: PlayerPosition,
        tax: ZoneTax,
        style: RotationStyle,
    ) -> list[str]:
        """Build ordered list of priority actions for the rotation."""
        actions: list[str] = []

        # Immediate health concern
        if player.health + player.shield < 75:
            actions.append("Heal before rotating — you cannot afford storm ticks.")

        # Time pressure
        if tax.time_pressure > 0.7:
            actions.append("ROTATE NOW — zone is closing and you are out of position.")
        elif tax.time_pressure > 0.4:
            actions.append("Start rotation soon — zone will close within 30s.")

        # Material concern
        total_mats = sum(player.materials.values())
        if total_mats < 100 and style in (RotationStyle.TARPING, RotationStyle.TUNNELING):
            actions.append(
                "Low materials — farm before rotating or switch to an open rotation."
            )

        # Style-specific advice
        if style == RotationStyle.TARPING:
            actions.append("Tarp: build floors overhead while moving to block AR spam.")
        elif style == RotationStyle.TUNNELING:
            actions.append("Tunnel: box up and move through walls to avoid damage.")
        elif style == RotationStyle.EDGE_ROTATE:
            actions.append("Edge rotate: follow the storm wall to reduce fight angles.")
        elif style == RotationStyle.LAUNCH_PAD:
            actions.append("Use mobility item for instant rotation — save it for max distance.")

        # Third-party warning
        if tax.fight_probability > 0.5:
            actions.append("High third-party risk — avoid engagements during rotation.")

        return actions
