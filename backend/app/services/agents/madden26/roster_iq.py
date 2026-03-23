"""RosterIQ — NFL personnel analysis, patch-adjusted ratings, speed mismatch detection.

Provides roster intelligence for Madden 26 by analyzing personnel packages,
detecting exploitable speed gaps, recommending scheme fits, and tracking
patch-driven rating changes.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.madden26.roster import (
    AdjustedRatings,
    HiddenGem,
    MismatchSeverity,
    PersonnelPackage,
    Player,
    PlayerRating,
    Position,
    PositionGroupGrade,
    RatingChange,
    RosterAnalysis,
    RosterData,
    SchemeRecommendation,
    SchemeType,
    SpeedMismatch,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

POSITION_GROUPS: dict[str, list[Position]] = {
    "QB": [Position.QB],
    "Backfield": [Position.HB, Position.FB],
    "WR Corps": [Position.WR],
    "Tight Ends": [Position.TE],
    "Offensive Line": [Position.LT, Position.LG, Position.C, Position.RG, Position.RT],
    "Defensive Line": [Position.LE, Position.RE, Position.DT],
    "Linebackers": [Position.LOLB, Position.MLB, Position.ROLB],
    "Secondary": [Position.CB, Position.FS, Position.SS],
    "Special Teams": [Position.K, Position.P],
}

PERSONNEL_DEFINITIONS: dict[str, dict[str, int]] = {
    "11": {"HB": 1, "TE": 1, "WR": 3},
    "12": {"HB": 1, "TE": 2, "WR": 2},
    "13": {"HB": 1, "TE": 3, "WR": 1},
    "21": {"HB": 2, "TE": 1, "WR": 2},
    "22": {"HB": 2, "TE": 2, "WR": 1},
    "10": {"HB": 1, "TE": 0, "WR": 4},
    "20": {"HB": 2, "TE": 0, "WR": 3},
    "01": {"HB": 0, "TE": 1, "WR": 4},
}

_GRADE_THRESHOLDS = [
    (95, "A+"), (90, "A"), (85, "A-"),
    (80, "B+"), (75, "B"), (70, "B-"),
    (65, "C+"), (60, "C"), (55, "C-"),
    (50, "D+"), (45, "D"), (40, "D-"),
    (0, "F"),
]

SPEED_MISMATCH_THRESHOLDS: dict[MismatchSeverity, int] = {
    MismatchSeverity.CRITICAL: 8,
    MismatchSeverity.HIGH: 5,
    MismatchSeverity.MEDIUM: 3,
    MismatchSeverity.LOW: 1,
}

# Scheme affinity weights — which ratings matter most per scheme
SCHEME_WEIGHTS: dict[SchemeType, dict[str, float]] = {
    SchemeType.SPREAD: {"speed": 0.3, "route_running": 0.25, "catching": 0.2, "throw_accuracy_short": 0.15, "agility": 0.1},
    SchemeType.WEST_COAST: {"throw_accuracy_short": 0.25, "route_running": 0.2, "catching": 0.2, "awareness": 0.15, "agility": 0.1, "speed": 0.1},
    SchemeType.AIR_RAID: {"throw_power": 0.2, "throw_accuracy_deep": 0.2, "speed": 0.2, "route_running": 0.2, "catching": 0.2},
    SchemeType.POWER_RUN: {"strength": 0.3, "acceleration": 0.2, "awareness": 0.15, "speed": 0.15, "agility": 0.1, "throw_power": 0.1},
    SchemeType.RPO_HEAVY: {"speed": 0.2, "throw_accuracy_short": 0.2, "agility": 0.2, "acceleration": 0.15, "awareness": 0.15, "catching": 0.1},
    SchemeType.ZONE_RUN: {"agility": 0.25, "acceleration": 0.2, "speed": 0.2, "awareness": 0.15, "strength": 0.2},
    SchemeType.BALANCED: {"speed": 0.15, "strength": 0.15, "agility": 0.15, "awareness": 0.15, "acceleration": 0.15, "throw_accuracy_short": 0.13, "catching": 0.12},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _score_to_grade(score: float) -> str:
    for threshold, grade in _GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def _players_at_positions(players: list[Player], positions: list[Position]) -> list[Player]:
    return [p for p in players if p.position in positions]


def _avg_overall(players: list[Player]) -> float:
    if not players:
        return 0.0
    return sum(p.ratings.overall for p in players) / len(players)


def _get_rating_attr(ratings: PlayerRating, attr: str) -> int:
    val = getattr(ratings, attr, None)
    return val if val is not None else 0


# ---------------------------------------------------------------------------
# RosterIQ
# ---------------------------------------------------------------------------

class RosterIQ:
    """NFL personnel analysis engine for Madden 26."""

    # ------------------------------------------------------------------
    # analyze_roster
    # ------------------------------------------------------------------

    def analyze_roster(self, roster_data: RosterData) -> RosterAnalysis:
        """Full roster breakdown — grades every position group, finds needs, recommends scheme."""
        players = roster_data.players

        position_grades: list[PositionGroupGrade] = []
        for group_name, positions in POSITION_GROUPS.items():
            group_players = _players_at_positions(players, positions)
            avg = _avg_overall(group_players)
            grade = _score_to_grade(avg)

            strengths: list[str] = []
            weaknesses: list[str] = []
            for p in group_players:
                if p.ratings.overall >= 85:
                    strengths.append(f"{p.name} ({p.ratings.overall} OVR)")
                elif p.ratings.overall < 70:
                    weaknesses.append(f"{p.name} ({p.ratings.overall} OVR) — upgrade candidate")

            position_grades.append(PositionGroupGrade(
                group=group_name,
                grade=grade,
                score=round(avg, 1),
                strengths=strengths,
                weaknesses=weaknesses,
            ))

        overall_score = round(
            sum(pg.score for pg in position_grades) / max(len(position_grades), 1), 1
        )
        overall_grade = _score_to_grade(overall_score)

        top_players = sorted(players, key=lambda p: p.ratings.overall, reverse=True)[:5]

        biggest_needs = [
            pg.group for pg in sorted(position_grades, key=lambda pg: pg.score)[:3]
            if pg.score < 75
        ]

        scheme_rec = self.recommend_scheme_for_roster(roster_data)

        summary = (
            f"{roster_data.team_name} grades out at {overall_grade} ({overall_score}). "
            f"Best fit: {scheme_rec.primary_scheme.value}. "
            f"Top player: {top_players[0].name if top_players else 'N/A'}. "
            f"Biggest needs: {', '.join(biggest_needs) if biggest_needs else 'None critical'}."
        )

        return RosterAnalysis(
            team_name=roster_data.team_name,
            overall_grade=overall_grade,
            overall_score=overall_score,
            position_grades=position_grades,
            top_players=top_players,
            biggest_needs=biggest_needs,
            scheme_fit=scheme_rec.primary_scheme,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # get_personnel_packages
    # ------------------------------------------------------------------

    def get_personnel_packages(self, roster: RosterData) -> list[PersonnelPackage]:
        """Return available personnel packages based on roster composition."""
        players = roster.players
        packages: list[PersonnelPackage] = []

        position_map: dict[str, list[Player]] = {}
        for p in players:
            key = p.position.value
            # Normalize HB/FB
            if key == "FB":
                key = "HB"
            position_map.setdefault(key, []).append(p)

        for code, requirements in PERSONNEL_DEFINITIONS.items():
            can_fill = True
            available: dict[str, list[str]] = {}

            for pos, count in requirements.items():
                pool = sorted(
                    position_map.get(pos, []),
                    key=lambda p: p.ratings.overall,
                    reverse=True,
                )
                if len(pool) < count:
                    can_fill = False
                    break
                available[pos] = [p.name for p in pool[:count]]

            if not can_fill:
                continue

            # Always need 5 OL and 1 QB
            ol_pool = []
            for pos in ["LT", "LG", "C", "RG", "RT"]:
                ol_pool.extend(position_map.get(pos, []))
            qb_pool = position_map.get("QB", [])
            if len(ol_pool) < 5 or not qb_pool:
                continue

            available["QB"] = [qb_pool[0].name]
            available["OL"] = [p.name for p in sorted(ol_pool, key=lambda p: p.ratings.overall, reverse=True)[:5]]

            # Effectiveness: average OVR of all slotted players
            all_slotted = []
            for names in available.values():
                for name in names:
                    matched = next((p for p in players if p.name == name), None)
                    if matched:
                        all_slotted.append(matched)
            eff = _avg_overall(all_slotted) if all_slotted else 50.0

            desc_parts = []
            for pos in ["HB", "TE", "WR"]:
                cnt = requirements.get(pos, 0)
                if cnt:
                    desc_parts.append(f"{cnt} {pos}")
            description = ", ".join(desc_parts)

            best_against: list[str] = []
            if code in ("11", "10"):
                best_against = ["Nickel", "Dime", "Cover 3 Zone"]
            elif code in ("12", "13"):
                best_against = ["Base 4-3", "Cover 2", "Goal Line"]
            elif code in ("21", "22"):
                best_against = ["Base 3-4", "Light Box", "Cover 1"]

            packages.append(PersonnelPackage(
                code=code,
                description=description,
                available_players=available,
                effectiveness_score=round(eff, 1),
                best_against=best_against,
            ))

        return sorted(packages, key=lambda p: p.effectiveness_score, reverse=True)

    # ------------------------------------------------------------------
    # detect_speed_mismatches
    # ------------------------------------------------------------------

    def detect_speed_mismatches(
        self,
        offense_roster: RosterData,
        defense_roster: RosterData,
    ) -> list[SpeedMismatch]:
        """Find exploitable speed gaps between offensive playmakers and defensive coverage."""
        mismatches: list[SpeedMismatch] = []

        skill_positions = {Position.WR, Position.TE, Position.HB}
        coverage_positions = {Position.CB, Position.FS, Position.SS, Position.LOLB, Position.MLB, Position.ROLB}

        off_players = [p for p in offense_roster.players if p.position in skill_positions]
        def_players = [p for p in defense_roster.players if p.position in coverage_positions]

        for op in off_players:
            for dp in def_players:
                delta = op.ratings.speed - dp.ratings.speed
                if delta < 1:
                    continue

                severity = MismatchSeverity.LOW
                for sev in [MismatchSeverity.CRITICAL, MismatchSeverity.HIGH, MismatchSeverity.MEDIUM, MismatchSeverity.LOW]:
                    if delta >= SPEED_MISMATCH_THRESHOLDS[sev]:
                        severity = sev
                        break

                tip = self._generate_exploit_tip(op, dp, delta)

                mismatches.append(SpeedMismatch(
                    offensive_player=op.name,
                    offensive_position=op.position,
                    offensive_speed=op.ratings.speed,
                    defensive_player=dp.name,
                    defensive_position=dp.position,
                    defensive_speed=dp.ratings.speed,
                    speed_delta=delta,
                    severity=severity,
                    exploit_tip=tip,
                ))

        return sorted(mismatches, key=lambda m: m.speed_delta, reverse=True)

    # ------------------------------------------------------------------
    # recommend_scheme_for_roster
    # ------------------------------------------------------------------

    def recommend_scheme_for_roster(self, roster: RosterData) -> SchemeRecommendation:
        """Determine which offensive scheme best fits the roster's strengths."""
        players = roster.players
        scheme_scores: dict[SchemeType, float] = {}

        for scheme, weights in SCHEME_WEIGHTS.items():
            total = 0.0
            for attr, weight in weights.items():
                vals = [_get_rating_attr(p.ratings, attr) for p in players if _get_rating_attr(p.ratings, attr) > 0]
                avg = sum(vals) / len(vals) if vals else 50.0
                total += avg * weight
            scheme_scores[scheme] = total

        ranked = sorted(scheme_scores.items(), key=lambda x: x[1], reverse=True)
        best_scheme, best_score = ranked[0]
        alt_scheme = ranked[1][0] if len(ranked) > 1 else None

        max_possible = 99.0
        confidence = round(min(best_score / max_possible, 1.0), 2)

        key_players: list[str] = []
        for p in sorted(players, key=lambda p: p.ratings.overall, reverse=True)[:5]:
            key_players.append(p.name)

        playbook_suggestions = self._playbook_for_scheme(best_scheme)

        reasoning = (
            f"Roster attributes align best with {best_scheme.value} "
            f"(score {best_score:.1f}). "
            f"Key strengths match scheme requirements."
        )

        return SchemeRecommendation(
            primary_scheme=best_scheme,
            confidence=confidence,
            reasoning=reasoning,
            alternate_scheme=alt_scheme,
            key_players_for_scheme=key_players,
            playbook_suggestions=playbook_suggestions,
        )

    # ------------------------------------------------------------------
    # get_patch_adjusted_ratings
    # ------------------------------------------------------------------

    def get_patch_adjusted_ratings(
        self,
        player_name: str,
        patch_version: str,
        base_ratings: PlayerRating | None = None,
        patch_deltas: dict[str, int] | None = None,
    ) -> AdjustedRatings:
        """Return ratings after applying patch adjustments.

        In production this would query a patch database. Here we accept
        explicit deltas for testability.
        """
        if base_ratings is None:
            base_ratings = PlayerRating(
                overall=80, speed=80, acceleration=80, agility=80,
                strength=80, awareness=80,
            )

        if patch_deltas is None:
            patch_deltas = {}

        original_overall = base_ratings.overall
        adjusted_overall = original_overall
        rating_changes: dict[str, int] = {}

        for attr, delta in patch_deltas.items():
            current = _get_rating_attr(base_ratings, attr)
            if current > 0:
                rating_changes[attr] = delta
                if attr == "overall":
                    adjusted_overall = max(0, min(99, current + delta))

        if "overall" not in patch_deltas and rating_changes:
            avg_delta = sum(rating_changes.values()) / len(rating_changes)
            adjusted_overall = max(0, min(99, original_overall + round(avg_delta)))

        net = sum(rating_changes.values()) if rating_changes else 0
        impact = "buffed" if net > 0 else "nerfed" if net < 0 else "unchanged"

        return AdjustedRatings(
            player_name=player_name,
            patch_version=patch_version,
            original_overall=original_overall,
            adjusted_overall=adjusted_overall,
            rating_changes=rating_changes,
            net_impact=impact,
        )

    # ------------------------------------------------------------------
    # get_ratings_impact_alert
    # ------------------------------------------------------------------

    def get_ratings_impact_alert(
        self,
        patch_notes: str,
        known_changes: list[dict[str, Any]] | None = None,
    ) -> list[RatingChange]:
        """Parse patch notes and return structured rating changes.

        ``known_changes`` allows direct injection for testing; each dict
        should contain: player_name, position, team, attribute,
        old_value, new_value.
        """
        changes: list[RatingChange] = []

        if known_changes:
            for kc in known_changes:
                delta = kc["new_value"] - kc["old_value"]
                direction = "buffed" if delta > 0 else "nerfed" if delta < 0 else "unchanged"
                changes.append(RatingChange(
                    player_name=kc["player_name"],
                    position=Position(kc["position"]),
                    team=kc["team"],
                    attribute=kc["attribute"],
                    old_value=kc["old_value"],
                    new_value=kc["new_value"],
                    delta=delta,
                    impact_summary=f"{kc['player_name']} {kc['attribute']} {direction} by {abs(delta)}",
                ))

        return sorted(changes, key=lambda c: abs(c.delta), reverse=True)

    # ------------------------------------------------------------------
    # find_hidden_gems
    # ------------------------------------------------------------------

    def find_hidden_gems(self, roster: RosterData) -> list[HiddenGem]:
        """Identify underrated players whose attributes fit the scheme better than OVR suggests."""
        scheme_rec = self.recommend_scheme_for_roster(roster)
        scheme = scheme_rec.primary_scheme
        weights = SCHEME_WEIGHTS.get(scheme, SCHEME_WEIGHTS[SchemeType.BALANCED])

        gems: list[HiddenGem] = []

        for player in roster.players:
            if player.ratings.overall >= 85:
                continue  # Not hidden if already top-rated

            weighted_score = 0.0
            for attr, weight in weights.items():
                val = _get_rating_attr(player.ratings, attr)
                weighted_score += val * weight

            gem_score = weighted_score - player.ratings.overall
            if gem_score < 3.0:
                continue

            role = self._best_role_for_scheme(player, scheme)

            gems.append(HiddenGem(
                player=player,
                gem_score=round(min(gem_score * 3, 100), 1),
                reasoning=(
                    f"{player.name} has scheme-relevant attributes "
                    f"(weighted score {weighted_score:.1f}) above their "
                    f"{player.ratings.overall} OVR in a {scheme.value} system."
                ),
                best_role=role,
                comparable_to=None,
            ))

        return sorted(gems, key=lambda g: g.gem_score, reverse=True)[:10]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_exploit_tip(off: Player, defn: Player, delta: int) -> str:
        if off.position == Position.WR:
            if delta >= 8:
                return f"Streak / go route — {off.name} will burn {defn.name} deep."
            if delta >= 5:
                return f"Post or corner route to use {off.name}'s speed advantage."
            return f"Out route or slant to exploit the marginal speed edge."
        if off.position == Position.TE:
            return f"Seam route — {off.name} outruns {defn.name} up the middle."
        if off.position == Position.HB:
            return f"Swing / wheel route — {off.name} has open-field speed over {defn.name}."
        return f"Use {off.name} in space to exploit {delta}-point speed gap."

    @staticmethod
    def _playbook_for_scheme(scheme: SchemeType) -> list[str]:
        mapping: dict[SchemeType, list[str]] = {
            SchemeType.SPREAD: ["Gun Spread Y-Flex", "Gun Trips TE", "Gun Empty Base"],
            SchemeType.WEST_COAST: ["Singleback Ace", "Gun Doubles", "I-Form Pro"],
            SchemeType.AIR_RAID: ["Gun Spread", "Gun Trips", "Gun Empty Trey"],
            SchemeType.POWER_RUN: ["I-Form Tight", "Strong Close", "Goal Line"],
            SchemeType.RPO_HEAVY: ["Gun Spread Y-Flex", "Pistol Ace", "Singleback Ace"],
            SchemeType.ZONE_RUN: ["Gun Split Close", "Singleback Ace", "Pistol Ace"],
            SchemeType.BALANCED: ["Singleback Ace", "Gun Doubles", "I-Form Pro"],
        }
        return mapping.get(scheme, ["Singleback Ace"])

    @staticmethod
    def _best_role_for_scheme(player: Player, scheme: SchemeType) -> str:
        pos = player.position
        if pos == Position.WR:
            if scheme in (SchemeType.SPREAD, SchemeType.AIR_RAID):
                return "Outside speed threat / deep route specialist"
            return "Possession receiver / chain mover"
        if pos == Position.HB:
            if scheme in (SchemeType.POWER_RUN, SchemeType.ZONE_RUN):
                return "Primary ball carrier"
            return "Pass-catching back / change-of-pace"
        if pos == Position.TE:
            if scheme in (SchemeType.WEST_COAST, SchemeType.RPO_HEAVY):
                return "Seam threat / red-zone target"
            return "Inline blocker with receiving upside"
        if pos in (Position.CB, Position.FS, Position.SS):
            return "Coverage specialist in secondary"
        return f"Rotational contributor at {pos.value}"
