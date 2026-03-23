"""Dispersion Maps — real miss pattern per club, personalized from session history.

Builds statistical dispersion models from session shot data to reveal
each club's true scatter pattern.  Used by CourseIQ and WindLine to
make dispersion-aware decisions.
"""

from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.schemas.pga2k25.dispersion import (
    ClubDispersion,
    DispersionMap,
    MissPattern,
    SessionShot,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Grade thresholds
# ---------------------------------------------------------------------------

_GRADE_THRESHOLDS: list[tuple[float, str]] = [
    (3.0, "A+"),
    (5.0, "A"),
    (7.0, "A-"),
    (9.0, "B+"),
    (11.0, "B"),
    (13.0, "B-"),
    (16.0, "C+"),
    (19.0, "C"),
    (22.0, "C-"),
    (26.0, "D+"),
    (30.0, "D"),
    (35.0, "D-"),
]


class DispersionMaps:
    """
    Dispersion Maps for PGA TOUR 2K25.

    Analyzes session shot data to build personalized dispersion patterns
    for every club.  Reveals true miss tendencies and grades consistency
    to drive smarter club and target selection.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def build_dispersion_map(
        self,
        user_id: uuid.UUID,
        shots: list[SessionShot],
        clubs: Optional[list[str]] = None,
        min_shots_per_club: int = 5,
    ) -> DispersionMap:
        """Build a full dispersion map from session shot data."""
        # Group shots by club
        club_shots: dict[str, list[SessionShot]] = {}
        for shot in shots:
            club_shots.setdefault(shot.club, []).append(shot)

        # Filter by requested clubs and minimum shots
        if clubs:
            club_shots = {c: s for c, s in club_shots.items() if c in clubs}
        club_shots = {
            c: s for c, s in club_shots.items() if len(s) >= min_shots_per_club
        }

        # Build per-club dispersion
        dispersions: list[ClubDispersion] = []
        for club_name, club_shot_list in sorted(club_shots.items()):
            disp = self._analyze_club(club_name, club_shot_list)
            dispersions.append(disp)

        # Determine best/worst clubs
        most_consistent = None
        least_consistent = None
        improvement_priority = None

        if dispersions:
            sorted_by_grade = sorted(dispersions, key=lambda d: d.dispersion_radius_yards)
            most_consistent = sorted_by_grade[0].club
            least_consistent = sorted_by_grade[-1].club
            improvement_priority = least_consistent

        # Overall grade
        if dispersions:
            avg_radius = sum(d.dispersion_radius_yards for d in dispersions) / len(dispersions)
            overall_grade = self._grade_dispersion(avg_radius)
        else:
            overall_grade = "N/A"

        return DispersionMap(
            user_id=user_id,
            clubs=dispersions,
            total_shots_analyzed=len(shots),
            most_consistent_club=most_consistent,
            least_consistent_club=least_consistent,
            overall_dispersion_grade=overall_grade,
            improvement_priority=improvement_priority,
            confidence=min(0.95, 0.50 + len(shots) * 0.005),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    async def get_club_dispersion(
        self,
        user_id: uuid.UUID,
        club: str,
        shots: list[SessionShot],
    ) -> ClubDispersion:
        """Get dispersion data for a single club."""
        club_shots = [s for s in shots if s.club == club]
        if not club_shots:
            return self._empty_dispersion(club)
        return self._analyze_club(club, club_shots)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _analyze_club(self, club: str, shots: list[SessionShot]) -> ClubDispersion:
        """Analyze dispersion for a single club."""
        n = len(shots)

        # Compute averages
        avg_carry = sum(s.actual_distance for s in shots) / n
        avg_total = avg_carry * 1.06  # Approximate roll factor

        # Offline stats
        offlines = [s.offline_yards for s in shots]
        long_shorts = [s.long_short_yards for s in shots]

        avg_offline = sum(offlines) / n
        avg_ls = sum(long_shorts) / n

        std_offline = self._std_dev(offlines)
        std_ls = self._std_dev(long_shorts)

        left_count = sum(1 for x in offlines if x < -1)
        right_count = sum(1 for x in offlines if x > 1)
        short_count = sum(1 for x in long_shorts if x < -2)
        long_count = sum(1 for x in long_shorts if x > 2)

        miss_pattern = MissPattern(
            avg_offline=round(avg_offline, 1),
            avg_long_short=round(avg_ls, 1),
            std_offline=round(std_offline, 1),
            std_long_short=round(std_ls, 1),
            left_miss_pct=round(left_count / n, 2),
            right_miss_pct=round(right_count / n, 2),
            short_miss_pct=round(short_count / n, 2),
            long_miss_pct=round(long_count / n, 2),
            total_shots=n,
        )

        # Dispersion radius (1 standard deviation circle)
        radius = math.sqrt(std_offline ** 2 + std_ls ** 2)
        area = math.pi * std_offline * std_ls  # Ellipse area

        # Pressure multiplier
        pressure_shots = [s for s in shots if s.pressure_situation]
        if len(pressure_shots) >= 3:
            p_offlines = [s.offline_yards for s in pressure_shots]
            p_std = self._std_dev(p_offlines)
            pressure_mult = (p_std / std_offline) if std_offline > 0 else 1.0
        else:
            pressure_mult = 1.15  # Default assumption

        grade = self._grade_dispersion(radius)

        return ClubDispersion(
            club=club,
            avg_carry=round(avg_carry, 1),
            avg_total=round(avg_total, 1),
            miss_pattern=miss_pattern,
            dispersion_radius_yards=round(radius, 1),
            dispersion_area_sq_yards=round(area, 1),
            consistency_grade=grade,
            pressure_dispersion_multiplier=round(min(2.0, pressure_mult), 2),
        )

    @staticmethod
    def _std_dev(values: list[float]) -> float:
        """Calculate population standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    @staticmethod
    def _grade_dispersion(radius: float) -> str:
        """Grade dispersion radius into a letter grade."""
        for threshold, grade in _GRADE_THRESHOLDS:
            if radius <= threshold:
                return grade
        return "F"

    @staticmethod
    def _empty_dispersion(club: str) -> ClubDispersion:
        """Return an empty dispersion for a club with no data."""
        return ClubDispersion(
            club=club,
            avg_carry=0.0,
            avg_total=0.0,
            miss_pattern=MissPattern(
                avg_offline=0.0,
                avg_long_short=0.0,
                std_offline=0.0,
                std_long_short=0.0,
                left_miss_pct=0.0,
                right_miss_pct=0.0,
                short_miss_pct=0.0,
                long_miss_pct=0.0,
                total_shots=0,
            ),
            dispersion_radius_yards=0.0,
            dispersion_area_sq_yards=0.0,
            consistency_grade="N/A",
            notes="Insufficient data — no shots recorded for this club",
        )
