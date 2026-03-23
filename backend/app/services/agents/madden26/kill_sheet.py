"""Kill Sheet Generator — 5 specific plays that beat a specific opponent.

Analyzes opponent tendencies, roster strengths, and historical data to
produce a targeted kill sheet of high-probability plays.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.schemas.madden26.killsheet import (
    FormationType,
    GameResult,
    KillSheet,
    OpponentData,
    RankedPlay,
    Roster,
    ScoredKillSheet,
    ScoredPlay,
    Situation,
    SituationalKill,
    SituationalKills,
)


# ---------------------------------------------------------------------------
# Internal play database (would be backed by real data in production)
# ---------------------------------------------------------------------------

_PLAY_CATALOG: list[dict] = [
    {
        "play_name": "Gun Bunch Wk - Corner Strike",
        "playbook": "Gun Bunch",
        "formation": FormationType.GUN_BUNCH,
        "concept": "corner route vs cover 3",
        "base_effectiveness": 0.72,
        "beats_zone": True,
        "beats_man": False,
        "beats_blitz": False,
        "situation_tags": ["third_down", "red_zone"],
    },
    {
        "play_name": "Shotgun Trips TE - Mesh Concept",
        "playbook": "Shotgun Trips TE",
        "formation": FormationType.SHOTGUN,
        "concept": "mesh crossing routes",
        "base_effectiveness": 0.68,
        "beats_zone": True,
        "beats_man": True,
        "beats_blitz": False,
        "situation_tags": ["third_down"],
    },
    {
        "play_name": "I-Form Close - Power O",
        "playbook": "I-Form Close",
        "formation": FormationType.I_FORM,
        "concept": "power run behind pulling guard",
        "base_effectiveness": 0.65,
        "beats_zone": False,
        "beats_man": True,
        "beats_blitz": True,
        "situation_tags": ["goal_line", "red_zone"],
    },
    {
        "play_name": "Singleback Ace - PA Crossers",
        "playbook": "Singleback Ace",
        "formation": FormationType.SINGLEBACK,
        "concept": "play action deep crosser",
        "base_effectiveness": 0.70,
        "beats_zone": True,
        "beats_man": False,
        "beats_blitz": False,
        "situation_tags": ["third_down"],
    },
    {
        "play_name": "Pistol Strong - Counter",
        "playbook": "Pistol Strong",
        "formation": FormationType.PISTOL,
        "concept": "counter run misdirection",
        "base_effectiveness": 0.63,
        "beats_zone": False,
        "beats_man": True,
        "beats_blitz": True,
        "situation_tags": ["red_zone", "goal_line"],
    },
    {
        "play_name": "Gun Empty Trey - Blitz Beater",
        "playbook": "Gun Empty",
        "formation": FormationType.EMPTY,
        "concept": "quick slant hot route vs blitz",
        "base_effectiveness": 0.75,
        "beats_zone": False,
        "beats_man": True,
        "beats_blitz": True,
        "situation_tags": ["blitz", "third_down"],
    },
    {
        "play_name": "Gun Bunch Wk - Screen Wheel",
        "playbook": "Gun Bunch",
        "formation": FormationType.GUN_BUNCH,
        "concept": "RB screen with wheel route",
        "base_effectiveness": 0.60,
        "beats_zone": False,
        "beats_man": False,
        "beats_blitz": True,
        "situation_tags": ["blitz"],
    },
    {
        "play_name": "Shotgun Cluster - Out Route",
        "playbook": "Shotgun Cluster",
        "formation": FormationType.SHOTGUN,
        "concept": "out route vs off coverage",
        "base_effectiveness": 0.62,
        "beats_zone": True,
        "beats_man": False,
        "beats_blitz": False,
        "situation_tags": ["two_point"],
    },
    {
        "play_name": "Singleback Bunch - HB Dive",
        "playbook": "Singleback Bunch",
        "formation": FormationType.SINGLEBACK,
        "concept": "inside zone run",
        "base_effectiveness": 0.58,
        "beats_zone": False,
        "beats_man": True,
        "beats_blitz": True,
        "situation_tags": ["goal_line"],
    },
    {
        "play_name": "Under Center Ace - Boot Over",
        "playbook": "Under Center Ace",
        "formation": FormationType.UNDER_CENTER,
        "concept": "bootleg with crossing route",
        "base_effectiveness": 0.66,
        "beats_zone": True,
        "beats_man": False,
        "beats_blitz": False,
        "situation_tags": ["red_zone", "two_point"],
    },
]


class KillSheetGenerator:
    """Generates kill sheets — 5 plays proven to beat a specific opponent.

    Combines opponent scouting data with the user's roster strengths to
    rank and select the highest-probability plays.
    """

    TARGET_KILLS: int = 5

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def generate_kill_sheet(
        self,
        user_id: str,
        opponent_data: OpponentData,
        roster: Roster,
    ) -> KillSheet:
        """Generate a kill sheet of 5 plays proven to beat this opponent."""
        ranked = self.rank_plays_by_opponent(_PLAY_CATALOG, opponent_data)

        # Apply roster adjustments
        for rp in ranked:
            rp.effectiveness_score = self._apply_roster_bonus(rp, roster)

        # Re-sort after roster adjustments and take top 5
        ranked.sort(key=lambda p: p.effectiveness_score, reverse=True)
        top_kills = ranked[: self.TARGET_KILLS]

        return KillSheet(
            id=str(uuid.uuid4()),
            user_id=user_id,
            opponent_id=opponent_data.opponent_id,
            opponent_name=opponent_data.opponent_name,
            kills=top_kills,
            generated_at=datetime.now(timezone.utc).isoformat(),
            version=1,
        )

    def rank_plays_by_opponent(
        self,
        plays: list[dict],
        opponent_tendencies: OpponentData,
    ) -> list[RankedPlay]:
        """Rank plays by predicted effectiveness vs. opponent tendencies."""
        ranked: list[RankedPlay] = []

        for play in plays:
            score = play["base_effectiveness"]
            weakness = ""

            # Boost plays that counter opponent's tendencies
            if opponent_tendencies.zone_coverage_rate > 0.5 and play.get("beats_zone"):
                score += 0.10
                weakness = "high zone coverage rate"
            if opponent_tendencies.man_coverage_rate > 0.5 and play.get("beats_man"):
                score += 0.10
                weakness = "high man coverage rate"
            if opponent_tendencies.blitz_rate > 0.3 and play.get("beats_blitz"):
                score += 0.12
                weakness = "frequent blitzing"

            # Cap at 1.0
            score = min(1.0, score)

            ranked.append(
                RankedPlay(
                    play_name=play["play_name"],
                    playbook=play["playbook"],
                    formation=play["formation"],
                    concept=play["concept"],
                    effectiveness_score=round(score, 3),
                    yards_per_attempt=round(score * 10, 1),  # Rough YPA estimate
                    opponent_weakness_exploited=weakness or "general scheme beater",
                    hot_route_adjustments=[],
                    setup_notes="",
                )
            )

        ranked.sort(key=lambda p: p.effectiveness_score, reverse=True)
        return ranked

    def add_confidence_scores(
        self,
        kill_sheet: KillSheet,
        player_twin: dict | None = None,
    ) -> ScoredKillSheet:
        """Attach ConfidenceAI scores to each play in the kill sheet.

        Args:
            kill_sheet: Base kill sheet to score.
            player_twin: Optional player digital twin data for personalization.
        """
        scored_plays: list[ScoredPlay] = []
        total_confidence = 0.0

        for kill in kill_sheet.kills:
            # Base confidence from effectiveness
            confidence = kill.effectiveness_score * 0.85

            # Player twin adjustment
            if player_twin:
                exec_bonus = player_twin.get("execution_rating", 0.5) * 0.15
                confidence += exec_bonus

            confidence = round(min(1.0, max(0.0, confidence)), 3)
            total_confidence += confidence

            scored_plays.append(
                ScoredPlay(
                    play_name=kill.play_name,
                    playbook=kill.playbook,
                    formation=kill.formation,
                    concept=kill.concept,
                    effectiveness_score=kill.effectiveness_score,
                    yards_per_attempt=kill.yards_per_attempt,
                    opponent_weakness_exploited=kill.opponent_weakness_exploited,
                    hot_route_adjustments=kill.hot_route_adjustments,
                    setup_notes=kill.setup_notes,
                    confidence_score=confidence,
                    confidence_reasoning=f"Based on {kill.effectiveness_score:.0%} effectiveness vs opponent tendencies.",
                )
            )

        avg_confidence = round(total_confidence / len(scored_plays), 3) if scored_plays else 0.0

        return ScoredKillSheet(
            id=kill_sheet.id,
            user_id=kill_sheet.user_id,
            opponent_id=kill_sheet.opponent_id,
            opponent_name=kill_sheet.opponent_name,
            kills=scored_plays,
            average_confidence=avg_confidence,
            generated_at=kill_sheet.generated_at,
            version=kill_sheet.version,
        )

    def generate_situational_kills(self, opponent_data: OpponentData) -> SituationalKills:
        """Generate situation-specific kill plays (red zone, 3rd down, blitz)."""
        ranked = self.rank_plays_by_opponent(_PLAY_CATALOG, opponent_data)

        def _filter_situation(tag: str, situation: Situation) -> list[SituationalKill]:
            matching = [
                p for p in ranked
                if any(
                    tag in play.get("situation_tags", [])
                    for play in _PLAY_CATALOG
                    if play["play_name"] == p.play_name
                )
            ]
            return [
                SituationalKill(
                    situation=situation,
                    play=p,
                    situation_success_rate=round(p.effectiveness_score * 0.95, 3),
                )
                for p in matching[:3]
            ]

        return SituationalKills(
            opponent_id=opponent_data.opponent_id,
            red_zone_kills=_filter_situation("red_zone", Situation.RED_ZONE),
            third_down_kills=_filter_situation("third_down", Situation.THIRD_DOWN),
            blitz_kills=_filter_situation("blitz", Situation.BLITZ),
            goal_line_kills=_filter_situation("goal_line", Situation.GOAL_LINE),
            two_point_kills=_filter_situation("two_point", Situation.TWO_POINT),
        )

    def update_kill_sheet_from_game(
        self,
        kill_sheet: KillSheet,
        game_result: GameResult,
    ) -> KillSheet:
        """Update kill sheet based on post-game results."""
        updated_kills: list[RankedPlay] = []

        for kill in kill_sheet.kills:
            new_kill = kill.model_copy()
            if kill.play_name in game_result.plays_successful:
                # Boost effectiveness for plays that worked
                new_kill.effectiveness_score = min(1.0, kill.effectiveness_score + 0.05)
                new_kill.setup_notes = f"[CONFIRMED] Worked in game {game_result.game_id}. {kill.setup_notes}"
            elif kill.play_name in game_result.plays_used:
                # Slight decrease for plays used but not successful
                new_kill.effectiveness_score = max(0.0, kill.effectiveness_score - 0.03)
                new_kill.setup_notes = f"[REVIEW] Used but unsuccessful in {game_result.game_id}. {kill.setup_notes}"
            updated_kills.append(new_kill)

        return KillSheet(
            id=kill_sheet.id,
            user_id=kill_sheet.user_id,
            opponent_id=kill_sheet.opponent_id,
            opponent_name=kill_sheet.opponent_name,
            kills=updated_kills,
            generated_at=kill_sheet.generated_at,
            version=kill_sheet.version + 1,
            notes=f"Updated after game {game_result.game_id}. Score: {game_result.final_score_user}-{game_result.final_score_opponent}",
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _apply_roster_bonus(self, play: RankedPlay, roster: Roster) -> float:
        """Adjust effectiveness based on roster strengths."""
        score = play.effectiveness_score

        # Passing plays benefit from QB + WR ratings
        if play.formation in (FormationType.SHOTGUN, FormationType.GUN_BUNCH, FormationType.EMPTY):
            qb_bonus = (roster.qb_overall - 80) * 0.002
            wr_bonus = (roster.wr1_overall - 80) * 0.001
            score += qb_bonus + wr_bonus

        # Run plays benefit from RB + OLine
        if play.formation in (FormationType.I_FORM, FormationType.SINGLEBACK, FormationType.PISTOL):
            rb_bonus = (roster.rb_overall - 80) * 0.002
            ol_bonus = (roster.oline_avg - 80) * 0.002
            score += rb_bonus + ol_bonus

        return round(min(1.0, max(0.0, score)), 3)
