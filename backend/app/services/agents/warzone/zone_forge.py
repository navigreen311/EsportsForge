"""ZoneForge AI — circle collapse prediction, rotation timing, third-party risk scanner.

Provides zone intelligence for Warzone by predicting circle movement,
planning safe rotations, and assessing third-party ambush probability.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from app.schemas.warzone.combat import (
    CirclePhase,
    CirclePrediction,
    RotationPlan,
    RotationRequest,
    ThirdPartyRisk,
    ZoneRequest,
    ZoneResponse,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Phase timing: seconds until collapse per phase
PHASE_TIMING: dict[CirclePhase, int] = {
    CirclePhase.PHASE_1: 180,
    CirclePhase.PHASE_2: 150,
    CirclePhase.PHASE_3: 120,
    CirclePhase.PHASE_4: 90,
    CirclePhase.PHASE_5: 60,
    CirclePhase.FINAL: 30,
}

# Safe zone radius per phase (meters)
PHASE_RADIUS: dict[CirclePhase, float] = {
    CirclePhase.PHASE_1: 800.0,
    CirclePhase.PHASE_2: 500.0,
    CirclePhase.PHASE_3: 300.0,
    CirclePhase.PHASE_4: 150.0,
    CirclePhase.PHASE_5: 75.0,
    CirclePhase.FINAL: 25.0,
}

# Map center coordinates for pull bias
MAP_CENTERS: dict[str, tuple[float, float]] = {
    "urzikstan": (500.0, 500.0),
    "al_mazrah": (480.0, 520.0),
    "vondel": (250.0, 250.0),
    "ashika_island": (200.0, 200.0),
    "rebirth_island": (150.0, 150.0),
}

# High-traffic POI zones for third-party risk (name, center, radius)
HIGH_TRAFFIC_POIS: dict[str, list[tuple[str, tuple[float, float], float]]] = {
    "urzikstan": [
        ("City Center", (500.0, 500.0), 80.0),
        ("Military Base", (300.0, 700.0), 60.0),
        ("Port", (700.0, 300.0), 50.0),
        ("Summit", (200.0, 200.0), 40.0),
        ("Power Plant", (600.0, 650.0), 45.0),
    ],
}

# Sprint speed: meters per second
SPRINT_SPEED = 6.5
VEHICLE_SPEED = 25.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Euclidean distance between two grid points."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _midpoint(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def _cardinal_direction(from_pos: tuple[float, float], to_pos: tuple[float, float]) -> str:
    """Return cardinal direction from one point to another."""
    dx = to_pos[0] - from_pos[0]
    dy = to_pos[1] - from_pos[1]
    angle = math.degrees(math.atan2(dy, dx))
    directions = ["E", "NE", "N", "NW", "W", "SW", "S", "SE"]
    idx = round(angle / 45) % 8
    return directions[idx]


def _next_phase(phase: CirclePhase) -> CirclePhase:
    """Return the next circle phase."""
    order = list(CirclePhase)
    idx = order.index(phase)
    return order[min(idx + 1, len(order) - 1)]


# ---------------------------------------------------------------------------
# ZoneForge
# ---------------------------------------------------------------------------

class ZoneForge:
    """Circle collapse prediction and rotation intelligence engine."""

    # ------------------------------------------------------------------
    # predict_circle
    # ------------------------------------------------------------------

    def predict_circle(self, request: ZoneRequest) -> CirclePrediction:
        """Predict the next circle center and radius.

        Uses map center gravity, current player positions, and phase
        progression to estimate the next safe zone.
        """
        phase = request.current_phase
        next_ph = _next_phase(phase)
        map_center = MAP_CENTERS.get(request.map_name, (500.0, 500.0))

        # Bias toward map center with some pull from player cluster
        all_positions = [request.player_position] + request.teammate_positions
        if all_positions:
            avg_x = sum(p[0] for p in all_positions) / len(all_positions)
            avg_y = sum(p[1] for p in all_positions) / len(all_positions)
            player_center = (avg_x, avg_y)
        else:
            player_center = map_center

        # Weighted blend: 60% map center, 40% player cluster (simulates pull)
        predicted = (
            map_center[0] * 0.6 + player_center[0] * 0.4,
            map_center[1] * 0.6 + player_center[1] * 0.4,
        )

        radius = PHASE_RADIUS.get(next_ph, 25.0)
        eta = PHASE_TIMING.get(phase, 60)

        # Confidence decreases in later phases (more randomness)
        phase_idx = list(CirclePhase).index(phase)
        confidence = max(0.3, 0.85 - phase_idx * 0.1)

        return CirclePrediction(
            predicted_center=predicted,
            confidence=round(confidence, 2),
            safe_zone_radius=radius,
            collapse_eta_seconds=eta,
            phase=next_ph,
        )

    # ------------------------------------------------------------------
    # assess_third_party_risk
    # ------------------------------------------------------------------

    def assess_third_party_risk(
        self,
        position: tuple[float, float],
        known_enemies: list[tuple[float, float]],
        map_name: str = "urzikstan",
    ) -> ThirdPartyRisk:
        """Evaluate probability of third-party engagement at a position."""
        pois = HIGH_TRAFFIC_POIS.get(map_name, [])

        # POI proximity risk
        poi_risk = 0.0
        nearest_poi = ""
        for name, center, radius in pois:
            dist = _distance(position, center)
            if dist < radius * 2:
                local_risk = max(0.0, 1.0 - dist / (radius * 2))
                if local_risk > poi_risk:
                    poi_risk = local_risk
                    nearest_poi = name

        # Enemy proximity risk
        enemy_risk = 0.0
        closest_enemy_dir = "N"
        for ep in known_enemies:
            dist = _distance(position, ep)
            if dist < 150.0:
                local = max(0.0, 1.0 - dist / 150.0)
                if local > enemy_risk:
                    enemy_risk = local
                    closest_enemy_dir = _cardinal_direction(position, ep)

        combined = min(1.0, poi_risk * 0.4 + enemy_risk * 0.6)
        enemy_est = sum(1 for ep in known_enemies if _distance(position, ep) < 200.0)

        threat_dir = closest_enemy_dir if enemy_risk > poi_risk else (
            _cardinal_direction(position, next(
                (c for n, c, _ in pois if n == nearest_poi), position
            )) if nearest_poi else "N"
        )

        if combined > 0.7:
            mitigation = "Avoid area — rotate wide or use smoke for concealment."
        elif combined > 0.4:
            mitigation = "Move cautiously — pre-aim common angles and use cover."
        else:
            mitigation = "Low risk — maintain pace but keep awareness up."

        return ThirdPartyRisk(
            risk_score=round(combined, 2),
            threat_direction=threat_dir,
            enemy_count_estimate=enemy_est,
            mitigation=mitigation,
        )

    # ------------------------------------------------------------------
    # plan_rotation
    # ------------------------------------------------------------------

    def plan_rotation(self, request: RotationRequest) -> RotationPlan:
        """Generate an optimal rotation plan between two points.

        Accounts for circle phase urgency, vehicle availability, and
        third-party risk along the route.
        """
        start = request.current_position
        end = request.destination
        total_dist = _distance(start, end)

        # Generate intermediate waypoints (every ~100m)
        num_waypoints = max(2, int(total_dist / 100))
        waypoints: list[tuple[float, float]] = []
        for i in range(num_waypoints + 1):
            t = i / num_waypoints
            wp = (
                round(start[0] + t * (end[0] - start[0]), 1),
                round(start[1] + t * (end[1] - start[1]), 1),
            )
            waypoints.append(wp)

        speed = VEHICLE_SPEED if request.has_vehicle else SPRINT_SPEED
        travel_time = int(total_dist / speed)

        # Cover quality inversely correlates with open-field distance
        phase_idx = list(CirclePhase).index(request.phase)
        cover_quality = max(0.2, 0.8 - phase_idx * 0.1 - (total_dist / 2000))

        # Third-party risk at midpoint
        mid = _midpoint(start, end)
        tp_risk = self.assess_third_party_risk(mid, [], "urzikstan")

        urgency = PHASE_TIMING.get(request.phase, 60)
        if travel_time > urgency * 0.7:
            notes = "URGENT — rotation is cutting it close. Sprint or find a vehicle."
        elif tp_risk.risk_score > 0.6:
            notes = "High third-party risk on this route. Consider flanking wide."
        else:
            notes = "Standard rotation — maintain squad spacing and cover angles."

        return RotationPlan(
            waypoints=waypoints,
            estimated_travel_seconds=travel_time,
            cover_quality=round(max(0.0, min(1.0, cover_quality)), 2),
            third_party_risk=tp_risk,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # analyze_zone (full pipeline)
    # ------------------------------------------------------------------

    def analyze_zone(self, request: ZoneRequest) -> ZoneResponse:
        """Full zone intelligence pipeline — predict, plan, and assess."""
        prediction = self.predict_circle(request)

        rotation_req = RotationRequest(
            current_position=request.player_position,
            destination=prediction.predicted_center,
            phase=request.current_phase,
        )
        rotation = self.plan_rotation(rotation_req)

        # Assess third-party risk at current position and predicted destination
        risks = [
            self.assess_third_party_risk(
                request.player_position,
                request.known_enemy_positions,
                request.map_name,
            ),
            self.assess_third_party_risk(
                prediction.predicted_center,
                request.known_enemy_positions,
                request.map_name,
            ),
        ]

        max_risk = max(r.risk_score for r in risks)
        dist = _distance(request.player_position, prediction.predicted_center)

        summary = (
            f"Circle pulling to ({prediction.predicted_center[0]:.0f}, "
            f"{prediction.predicted_center[1]:.0f}) — {prediction.safe_zone_radius:.0f}m radius. "
            f"Distance: {dist:.0f}m. Travel: ~{rotation.estimated_travel_seconds}s. "
            f"Third-party risk: {'HIGH' if max_risk > 0.6 else 'MEDIUM' if max_risk > 0.3 else 'LOW'}."
        )

        return ZoneResponse(
            prediction=prediction,
            rotation_plan=rotation,
            third_party_risks=risks,
            summary=summary,
        )
