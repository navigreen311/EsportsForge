"""CFB RosterIQ — school-by-school depth chart intelligence and dynasty projection."""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

POSITION_WEIGHTS = {
    "spread": {"QB": 1.0, "WR": 0.9, "RB": 0.6, "OL": 0.7, "CB": 0.8, "S": 0.7, "LB": 0.6, "DL": 0.7},
    "pro_style": {"QB": 0.9, "WR": 0.7, "RB": 0.8, "OL": 0.9, "TE": 0.8, "CB": 0.7, "S": 0.6, "LB": 0.7, "DL": 0.8},
    "option": {"QB": 1.0, "RB": 0.9, "FB": 0.8, "OL": 0.9, "WR": 0.4, "LB": 0.8, "DL": 0.7, "CB": 0.6},
    "air_raid": {"QB": 1.0, "WR": 1.0, "OL": 0.8, "RB": 0.4, "CB": 0.9, "S": 0.8, "DL": 0.6},
}


@dataclass
class DepthChartAnalysis:
    school: str
    overall_rating: float
    position_grades: dict
    depth_concerns: list
    strengths: list
    starter_count: int
    backup_quality: float


@dataclass
class PositionNeed:
    position: str
    urgency: str  # "critical", "high", "moderate", "low"
    current_starter_rating: float
    depth_count: int
    reason: str


@dataclass
class DynastyProjection:
    year: int
    projected_overall: float
    graduating_starters: list
    incoming_recruits: list
    position_improvements: dict
    risk_areas: list


class CFBRosterIQ:
    """School-by-school depth chart intelligence and dynasty roster projection."""

    def analyze_depth_chart(self, school: str, roster: list[dict]) -> DepthChartAnalysis:
        position_groups = {}
        for player in roster:
            pos = player.get("position", "UNKNOWN")
            if pos not in position_groups:
                position_groups[pos] = []
            position_groups[pos].append(player)

        position_grades = {}
        strengths = []
        concerns = []
        starter_count = 0

        for pos, players in position_groups.items():
            sorted_players = sorted(players, key=lambda p: p.get("overall", 0), reverse=True)
            starter = sorted_players[0] if sorted_players else None
            backups = sorted_players[1:] if len(sorted_players) > 1 else []

            starter_rating = starter.get("overall", 0) if starter else 0
            backup_avg = sum(p.get("overall", 0) for p in backups) / max(len(backups), 1)
            grade = (starter_rating * 0.7 + backup_avg * 0.3) if backups else starter_rating * 0.6

            position_grades[pos] = round(grade, 1)
            if starter_rating > 0:
                starter_count += 1
            if grade >= 80:
                strengths.append(f"{pos}: Elite depth ({len(sorted_players)} players, {starter_rating} starter)")
            if len(sorted_players) < 2 and starter_rating < 75:
                concerns.append(f"{pos}: Thin depth ({len(sorted_players)} players, {starter_rating} starter)")

        overall = sum(position_grades.values()) / max(len(position_grades), 1)
        backup_quality = sum(
            sum(p.get("overall", 0) for p in players[1:]) / max(len(players) - 1, 1)
            for players in position_groups.values() if len(players) > 1
        ) / max(sum(1 for p in position_groups.values() if len(p) > 1), 1)

        return DepthChartAnalysis(
            school=school,
            overall_rating=round(overall, 1),
            position_grades=position_grades,
            depth_concerns=concerns,
            strengths=strengths,
            starter_count=starter_count,
            backup_quality=round(backup_quality, 1),
        )

    def get_position_needs(self, roster: list[dict], scheme: str = "spread") -> list[PositionNeed]:
        weights = POSITION_WEIGHTS.get(scheme, POSITION_WEIGHTS["spread"])
        position_groups = {}
        for player in roster:
            pos = player.get("position", "UNKNOWN")
            if pos not in position_groups:
                position_groups[pos] = []
            position_groups[pos].append(player)

        needs = []
        for pos, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            players = position_groups.get(pos, [])
            starter_rating = max((p.get("overall", 0) for p in players), default=0)
            depth = len(players)

            if depth == 0:
                urgency = "critical"
                reason = f"No {pos} on roster — must recruit immediately"
            elif depth == 1 and starter_rating < 70:
                urgency = "critical"
                reason = f"Only 1 {pos} at {starter_rating} OVR — no backup, low quality"
            elif starter_rating < 72 and weight >= 0.8:
                urgency = "high"
                reason = f"Key position in {scheme} scheme but starter only {starter_rating} OVR"
            elif depth < 2:
                urgency = "moderate"
                reason = f"No backup {pos} — one injury away from crisis"
            else:
                urgency = "low"
                reason = f"Adequate depth ({depth} players, {starter_rating} starter)"

            needs.append(PositionNeed(
                position=pos, urgency=urgency,
                current_starter_rating=starter_rating,
                depth_count=depth, reason=reason,
            ))

        return sorted(needs, key=lambda n: {"critical": 0, "high": 1, "moderate": 2, "low": 3}[n.urgency])

    def project_dynasty_roster(self, roster: list[dict], recruits: list[dict], years: int = 3) -> list[DynastyProjection]:
        projections = []
        current_roster = list(roster)

        for year in range(1, years + 1):
            graduating = [p for p in current_roster if p.get("year", 1) + year > 4]
            remaining = [p for p in current_roster if p.get("year", 1) + year <= 4]
            for p in remaining:
                p["overall"] = min(99, p.get("overall", 70) + 2)

            year_recruits = recruits[:3] if year == 1 else []
            new_roster = remaining + year_recruits
            overall = sum(p.get("overall", 0) for p in new_roster) / max(len(new_roster), 1)

            projections.append(DynastyProjection(
                year=year,
                projected_overall=round(overall, 1),
                graduating_starters=[p.get("name", "Unknown") for p in graduating[:5]],
                incoming_recruits=[r.get("name", "Unknown") for r in year_recruits],
                position_improvements={},
                risk_areas=[p.get("position", "?") for p in graduating if p.get("overall", 0) > 80],
            ))
            current_roster = new_roster

        return projections
