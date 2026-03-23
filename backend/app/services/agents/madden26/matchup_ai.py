"""MatchupAI — Pre-snap personnel advantage finder, leverage matchup isolation.

Analyzes offensive vs defensive personnel to surface exploitable mismatches,
recommend formations/motions, and evaluate groupings against specific looks.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.madden26.roster import (
    MismatchSeverity,
    PersonnelPackage,
    Player,
    Position,
    RosterData,
)
from app.schemas.madden26.matchup import (
    AdvantageType,
    ConfidenceLevel,
    GroupingEvaluation,
    LeverageMatchup,
    MatchupAdvantage,
    MatchupResult,
    MotionSuggestion,
    MotionType,
)
from app.services.agents.madden26.roster_iq import RosterIQ

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_COVERAGE_POSITIONS = {Position.CB, Position.FS, Position.SS}
_LB_POSITIONS = {Position.LOLB, Position.MLB, Position.ROLB}
_SKILL_POSITIONS = {Position.WR, Position.TE, Position.HB}

_ADVANTAGE_THRESHOLD = 5  # rating-point gap to count as an advantage


# ---------------------------------------------------------------------------
# MatchupAI
# ---------------------------------------------------------------------------

class MatchupAI:
    """Personnel advantage finder and matchup isolation engine for Madden 26."""

    def __init__(self) -> None:
        self._roster_iq = RosterIQ()

    # ------------------------------------------------------------------
    # find_matchup_advantages
    # ------------------------------------------------------------------

    def find_matchup_advantages(
        self,
        offense: RosterData,
        defense: RosterData,
    ) -> list[MatchupAdvantage]:
        """Identify all pre-snap personnel advantages offense has over defense."""
        advantages: list[MatchupAdvantage] = []

        off_skill = [p for p in offense.players if p.position in _SKILL_POSITIONS]
        def_coverage = [p for p in defense.players if p.position in _COVERAGE_POSITIONS | _LB_POSITIONS]

        for op in off_skill:
            for dp in def_coverage:
                advs = self._compare_players(op, dp)
                advantages.extend(advs)

        return sorted(advantages, key=lambda a: a.advantage_score, reverse=True)

    # ------------------------------------------------------------------
    # isolate_leverage_matchup
    # ------------------------------------------------------------------

    def isolate_leverage_matchup(
        self,
        personnel: list[Player],
        formation: str,
    ) -> LeverageMatchup:
        """Find the single best mismatch to target from the given formation.

        Uses a heuristic: the player with the best weighted score
        (speed + route_running + catching) vs the weakest likely
        coverage defender is the leverage point.
        """
        skill = [p for p in personnel if p.position in _SKILL_POSITIONS]
        if not skill:
            return LeverageMatchup(
                target_player="N/A",
                target_position=Position.WR,
                matched_against="N/A",
                matched_position=Position.CB,
                leverage_score=0,
                route_suggestion="No skill players available",
                formation_alignment=formation,
                reasoning="No skill position players found in personnel.",
            )

        best = max(
            skill,
            key=lambda p: (
                p.ratings.speed
                + (p.ratings.route_running or 0)
                + (p.ratings.catching or 0)
            ),
        )

        route = self._suggest_route(best)
        alignment = self._alignment_for_formation(best.position, formation)

        return LeverageMatchup(
            target_player=best.name,
            target_position=best.position,
            matched_against="Weakest coverage defender",
            matched_position=Position.CB,
            leverage_score=round(min(
                (best.ratings.speed + (best.ratings.route_running or 0)) / 2, 100
            ), 1),
            route_suggestion=route,
            formation_alignment=alignment,
            reasoning=(
                f"{best.name} has the best combination of speed "
                f"({best.ratings.speed}) and receiving attributes "
                f"to isolate from {formation}."
            ),
        )

    # ------------------------------------------------------------------
    # suggest_motion_to_create
    # ------------------------------------------------------------------

    def suggest_motion_to_create(
        self,
        matchup: LeverageMatchup,
    ) -> MotionSuggestion:
        """Recommend pre-snap motion that forces a favorable matchup or reveals coverage."""
        pos = matchup.target_position

        if pos == Position.WR:
            motion_type = MotionType.JET
            purpose = f"Put {matchup.target_player} in jet motion to force man/zone reveal"
            reveals = "If defender follows across the formation, it's man. If they stay, it's zone."
            if_man = f"Throw the jet sweep or quick screen to {matchup.target_player} with blockers."
            if_zone = f"Let {matchup.target_player} settle into a soft zone window for an easy catch."
        elif pos == Position.TE:
            motion_type = MotionType.TRADE
            purpose = f"Trade {matchup.target_player} to the opposite side to create a numbers advantage"
            reveals = "Watch if a LB bumps or a safety rotates — indicates coverage responsibility."
            if_man = f"Run a seam route with {matchup.target_player} against the trailing LB."
            if_zone = f"Sit {matchup.target_player} in the void between hook and curl zone."
        else:
            motion_type = MotionType.ORBIT
            purpose = f"Orbit {matchup.target_player} to stress the edge and test coverage"
            reveals = "LB reaction shows blitz or coverage assignment."
            if_man = f"Dump off to {matchup.target_player} in space with speed advantage."
            if_zone = f"Use {matchup.target_player} as a decoy and hit the vacated area."

        return MotionSuggestion(
            motion_type=motion_type,
            motion_player=matchup.target_player,
            purpose=purpose,
            reveals=reveals,
            if_man=if_man,
            if_zone=if_zone,
            confidence=ConfidenceLevel.HIGH,
        )

    # ------------------------------------------------------------------
    # evaluate_personnel_grouping
    # ------------------------------------------------------------------

    def evaluate_personnel_grouping(
        self,
        grouping: PersonnelPackage,
        defense: RosterData,
    ) -> GroupingEvaluation:
        """Evaluate how effective a personnel grouping is vs a defensive roster."""
        def_players = defense.players
        def_speed_avg = (
            sum(p.ratings.speed for p in def_players) / len(def_players)
            if def_players else 75
        )
        def_coverage_avg = (
            sum(
                (p.ratings.man_coverage or 0) + (p.ratings.zone_coverage or 0)
                for p in def_players
                if p.position in _COVERAGE_POSITIONS
            ) / max(
                sum(1 for p in def_players if p.position in _COVERAGE_POSITIONS), 1
            ) / 2
        )

        eff = grouping.effectiveness_score
        strengths: list[str] = []
        vulns: list[str] = []
        plays: list[str] = []

        code = grouping.code
        if code in ("11", "10"):
            strengths.append("Spread the field — forces nickel/dime personnel")
            if def_coverage_avg < 80:
                strengths.append("Weak coverage secondary — attack with routes")
                eff = min(eff + 10, 100)
            else:
                vulns.append("Strong coverage secondary may limit passing")
            plays.extend(["Mesh Concept", "Four Verticals", "RPO Zone Read"])
        elif code in ("12", "13"):
            strengths.append("Two-TE sets create blocking and receiving versatility")
            if def_speed_avg < 82:
                strengths.append("Slower defense — TEs can exploit the seam")
                eff = min(eff + 8, 100)
            else:
                vulns.append("Fast defense can cover TEs in the seam")
            plays.extend(["PA Boot Over", "Inside Zone", "TE Angle"])
        elif code in ("21", "22"):
            strengths.append("Heavy personnel — imposing run game presence")
            plays.extend(["Power", "Counter", "Play Action Deep"])
            if def_speed_avg > 85:
                vulns.append("Fast defense can pursue outside runs")

        if not vulns:
            vulns.append("No glaring vulnerability detected")

        verdict = (
            f"{grouping.code} personnel scores {round(eff, 1)} effectiveness "
            f"vs this defense."
        )

        return GroupingEvaluation(
            grouping_code=grouping.code,
            defense_look=defense.team_name,
            effectiveness_score=round(eff, 1),
            strengths=strengths,
            vulnerabilities=vulns,
            recommended_plays=plays,
            verdict=verdict,
        )

    # ------------------------------------------------------------------
    # get_matchup_history
    # ------------------------------------------------------------------

    def get_matchup_history(
        self,
        user_id: str,
        opponent_id: str,
        history: list[dict[str, Any]] | None = None,
    ) -> list[MatchupResult]:
        """Return historical matchup results.

        In production this queries a database. ``history`` param allows
        direct injection for testing.
        """
        if not history:
            return []

        results: list[MatchupResult] = []
        for h in history:
            user_score = h.get("user_score", 0)
            opp_score = h.get("opponent_score", 0)
            if user_score > opp_score:
                result = "win"
            elif user_score < opp_score:
                result = "loss"
            else:
                result = "draw"

            results.append(MatchupResult(
                game_id=h.get("game_id", "unknown"),
                opponent_id=opponent_id,
                opponent_name=h.get("opponent_name", "Unknown"),
                user_score=user_score,
                opponent_score=opp_score,
                result=result,
                offensive_yards=h.get("offensive_yards"),
                defensive_yards_allowed=h.get("defensive_yards_allowed"),
                key_matchup_exploited=h.get("key_matchup_exploited"),
                timestamp=h.get("timestamp", ""),
            ))

        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compare_players(
        self, off: Player, defn: Player,
    ) -> list[MatchupAdvantage]:
        """Compare an offensive skill player vs a defender across key dimensions."""
        advs: list[MatchupAdvantage] = []

        # Speed advantage
        speed_delta = off.ratings.speed - defn.ratings.speed
        if speed_delta >= _ADVANTAGE_THRESHOLD:
            advs.append(self._build_advantage(
                AdvantageType.SPEED, off, defn,
                score=min(speed_delta * 5, 100),
                desc=f"{off.name} has {speed_delta}-point speed edge over {defn.name}",
                plays=["Streak", "Post", "Wheel Route"],
            ))

        # Route running vs coverage
        rr = off.ratings.route_running or 0
        man = defn.ratings.man_coverage or 0
        if rr and man and (rr - man) >= _ADVANTAGE_THRESHOLD:
            advs.append(self._build_advantage(
                AdvantageType.ROUTE_RUNNING, off, defn,
                score=min((rr - man) * 5, 100),
                desc=f"{off.name} route running ({rr}) beats {defn.name} man coverage ({man})",
                plays=["Curl", "Out", "Double Move"],
            ))

        # Size advantage (strength as proxy)
        str_delta = off.ratings.strength - defn.ratings.strength
        if str_delta >= _ADVANTAGE_THRESHOLD and off.position == Position.TE:
            advs.append(self._build_advantage(
                AdvantageType.SIZE, off, defn,
                score=min(str_delta * 5, 100),
                desc=f"{off.name} has {str_delta}-point strength edge for contested catches",
                plays=["Fade", "Back Shoulder", "Jump Ball"],
            ))

        return advs

    @staticmethod
    def _build_advantage(
        adv_type: AdvantageType,
        off: Player,
        defn: Player,
        score: float,
        desc: str,
        plays: list[str],
    ) -> MatchupAdvantage:
        severity = MismatchSeverity.LOW
        if score >= 80:
            severity = MismatchSeverity.CRITICAL
        elif score >= 60:
            severity = MismatchSeverity.HIGH
        elif score >= 40:
            severity = MismatchSeverity.MEDIUM

        return MatchupAdvantage(
            advantage_type=adv_type,
            offensive_player=off.name,
            offensive_position=off.position,
            defensive_player=defn.name,
            defensive_position=defn.position,
            advantage_score=round(score, 1),
            severity=severity,
            description=desc,
            suggested_play_concepts=plays,
        )

    @staticmethod
    def _suggest_route(player: Player) -> str:
        if player.position == Position.WR:
            if player.ratings.speed >= 92:
                return "Go / streak — attack vertically with elite speed"
            if (player.ratings.route_running or 0) >= 88:
                return "Out / curl — win with sharp route breaks"
            return "Slant — quick inside release"
        if player.position == Position.TE:
            return "Seam / corner — exploit the middle of the field"
        return "Wheel / swing — get into open space"

    @staticmethod
    def _alignment_for_formation(pos: Position, formation: str) -> str:
        formation_lower = formation.lower()
        if "spread" in formation_lower or "trips" in formation_lower:
            if pos == Position.WR:
                return "Split wide to the boundary"
            return "Slot or detached from formation"
        if "ace" in formation_lower or "i-form" in formation_lower:
            if pos == Position.TE:
                return "Inline on the strong side"
            return "Flanker or split end"
        return f"Standard {pos.value} alignment in {formation}"
