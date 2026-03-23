"""GameplanAI — Pre-game scheme generator: player vs opponent vs roster for Madden 26."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.schemas.madden26.gameplan import (
    AudibleBranch,
    AudibleTree,
    Gameplan,
    KillSheet,
    MetaReport,
    Play,
    PlayType,
    ValidatedGameplan,
)
from app.schemas.madden26.scheme import CoverageType, Situation
from app.services.agents.madden26.scheme_ai import SchemeAI
from app.services.agents.madden26.meta_bot import MetaBot


class GameplanAI:
    """
    GameplanAI for Madden 26.

    Generates complete 10-play gameplans tailored to a player's skill level,
    their opponent's tendencies, roster strengths, and the current meta.
    """

    def __init__(self) -> None:
        self._scheme_ai = SchemeAI()
        self._meta_bot = MetaBot()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_gameplan(
        self,
        user_id: uuid.UUID,
        opponent_id: Optional[uuid.UUID] = None,
        roster: Optional[dict[str, Any]] = None,
        scheme: Optional[str] = None,
        meta_aware: bool = True,
    ) -> Gameplan:
        """Generate a full 10-play gameplan."""
        effective_scheme = scheme or "west_coast"

        # Build core plays from scheme concepts
        core_plays = await self._build_core_plays(effective_scheme, roster)

        # Build situational packages
        rz_package = await self._build_red_zone_package(effective_scheme)
        ab_package = await self._build_anti_blitz_package(effective_scheme)

        # Opening script — first 5 plays designed to probe the defense
        opening = [p.name for p in core_plays[:5]]

        # Build audible tree for the primary play
        audible_tree = await self.generate_audible_tree(
            base_play=core_plays[0].name if core_plays else "PA Boot Over",
            reads=[CoverageType.COVER_3, CoverageType.COVER_1, CoverageType.COVER_0],
        )

        meta_snapshot: Optional[str] = None
        if meta_aware:
            meta = await self._meta_bot.scan_weekly_meta()
            meta_snapshot = meta.meta_summary
            # Optionally adjust based on meta
            core_plays = self._apply_meta_adjustments(core_plays, meta)

        gameplan = Gameplan(
            id=uuid.uuid4(),
            user_id=user_id,
            opponent_id=opponent_id,
            scheme=effective_scheme,
            plays=core_plays[:10],
            opening_script=opening,
            audible_tree=audible_tree,
            red_zone_package=rz_package,
            anti_blitz_package=ab_package,
            meta_snapshot=meta_snapshot,
            confidence=0.78,
            generated_at=datetime.now(timezone.utc).isoformat(),
            notes=f"Gameplan built on {effective_scheme} scheme.",
        )

        return gameplan

    async def build_kill_sheet(
        self, opponent_data: dict[str, Any], opponent_id: Optional[uuid.UUID] = None,
    ) -> KillSheet:
        """Generate 5 specific plays designed to exploit a specific opponent."""
        oid = opponent_id or uuid.uuid4()

        # Analyse opponent tendencies
        tendencies = opponent_data.get("tendencies", {})
        favorite_coverage = tendencies.get("favorite_coverage", "cover_3")
        blitz_rate = tendencies.get("blitz_rate", 0.3)
        run_stop_rate = tendencies.get("run_stop_rate", 0.5)

        kill_plays: list[Play] = []
        exploit_notes: list[str] = []
        counter_warnings: list[str] = []

        # Exploit their favorite coverage
        try:
            cov = CoverageType(favorite_coverage)
        except ValueError:
            cov = CoverageType.COVER_3

        hot_routes = await self._scheme_ai.suggest_hot_routes("Base Play", cov)
        kill_plays.append(
            Play(
                name=f"Coverage Buster vs {cov.value}",
                formation="Gun Trips",
                play_type=PlayType.PASS_MEDIUM,
                concept="Flood",
                primary_read=hot_routes[0].reason if hot_routes else "Read the flat defender",
                beats=[cov.value],
                situation_tags=["kill_sheet"],
                notes=f"Designed to beat their {cov.value} tendency.",
            )
        )
        exploit_notes.append(f"Opponent favors {cov.value} — attack with Flood/Smash concepts.")

        # Exploit high blitz rate
        if blitz_rate > 0.25:
            kill_plays.append(
                Play(
                    name="Quick Screen vs Blitz",
                    formation="Gun Spread",
                    play_type=PlayType.SCREEN,
                    concept="Screen",
                    primary_read="RB to the edge",
                    beats=["blitz", "cover_0"],
                    situation_tags=["anti_blitz", "kill_sheet"],
                    notes="Screen to punish aggressive blitzing.",
                )
            )
            exploit_notes.append(f"High blitz rate ({blitz_rate:.0%}) — screens and quick passes.")

        # Exploit weak run defense
        if run_stop_rate < 0.5:
            kill_plays.append(
                Play(
                    name="Zone Run Exploit",
                    formation="Singleback Ace",
                    play_type=PlayType.RUN,
                    concept="Zone Run",
                    primary_read="Follow the lead blocker",
                    beats=["weak_run_d"],
                    situation_tags=["kill_sheet"],
                    notes="Pound the rock against their weak run front.",
                )
            )
            exploit_notes.append(f"Run stop rate only {run_stop_rate:.0%} — run the ball.")

        # Add PA shot play
        kill_plays.append(
            Play(
                name="PA Deep Shot",
                formation="Singleback Wing",
                play_type=PlayType.PLAY_ACTION,
                concept="Post-Wheel",
                primary_read="Deep post after play action fake",
                beats=["aggressive_run_fits"],
                situation_tags=["kill_sheet", "shot_play"],
                notes="Play action off the run game to hit deep.",
            )
        )

        # Add RPO
        kill_plays.append(
            Play(
                name="RPO Glance",
                formation="Pistol Spread",
                play_type=PlayType.RPO,
                concept="RPO Read",
                primary_read="Read the end man on the line",
                beats=["undisciplined_defense"],
                situation_tags=["kill_sheet"],
                notes="RPO keeps the defense honest.",
            )
        )

        counter_warnings.append("If they adjust to Cover 2, switch to smash/post concepts.")
        counter_warnings.append("If blitz rate drops, remove screens and add vertical shots.")

        return KillSheet(
            opponent_id=oid,
            opponent_summary=self._summarize_opponent(opponent_data),
            kill_plays=kill_plays[:5],
            exploit_notes=exploit_notes,
            counter_warnings=counter_warnings,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    async def validate_with_player_twin(
        self, gameplan: Gameplan, player_profile: dict[str, Any]
    ) -> ValidatedGameplan:
        """Filter a gameplan through the player's execution ceiling."""
        execution_ceiling = player_profile.get("execution_ceiling", {})
        timing_skill = execution_ceiling.get("timing", 0.7)
        read_skill = execution_ceiling.get("reads", 0.7)
        scramble_skill = execution_ceiling.get("scramble", 0.5)

        kept_plays: list[Play] = []
        removed: list[dict[str, str]] = []
        replacements: list[Play] = []
        warnings: list[str] = []

        for play in gameplan.plays:
            difficulty = self._estimate_difficulty(play)

            # Check if the player can execute this play
            can_execute = True
            reason = ""

            if "deep" in play.concept.lower() and timing_skill < 0.6:
                can_execute = False
                reason = "Deep timing routes require higher timing skill"
            elif play.play_type == PlayType.RPO and read_skill < 0.5:
                can_execute = False
                reason = "RPO reads require higher read skill"
            elif play.play_type == PlayType.QB_RUN and scramble_skill < 0.4:
                can_execute = False
                reason = "QB runs require higher scramble ability"
            elif difficulty > 0.8 and timing_skill < 0.6:
                can_execute = False
                reason = "Play complexity exceeds execution ceiling"

            if can_execute:
                kept_plays.append(play)
            else:
                removed.append({"play": play.name, "reason": reason})
                replacement = self._find_simpler_alternative(play)
                replacements.append(replacement)
                kept_plays.append(replacement)

        # Rebuild the gameplan with filtered plays
        filtered = gameplan.model_copy(update={"plays": kept_plays[:10]})

        exec_score = min(1.0, (timing_skill + read_skill + scramble_skill) / 3)

        if exec_score < 0.5:
            warnings.append("Low execution ceiling — gameplan simplified significantly.")
        if len(removed) > 3:
            warnings.append(f"{len(removed)} plays replaced — consider a simpler scheme.")

        return ValidatedGameplan(
            gameplan=filtered,
            removed_plays=removed,
            replacement_plays=replacements,
            execution_score=round(exec_score, 2),
            warnings=warnings,
        )

    async def adjust_for_meta(
        self, gameplan: Gameplan, meta_state: MetaReport
    ) -> Gameplan:
        """Adjust a gameplan based on the current meta state."""
        adjusted_plays = self._apply_meta_adjustments(gameplan.plays, meta_state)

        return gameplan.model_copy(
            update={
                "plays": adjusted_plays[:10],
                "meta_snapshot": meta_state.meta_summary,
                "notes": (gameplan.notes or "")
                + f" | Meta-adjusted for patch {meta_state.patch_version}.",
            }
        )

    async def generate_audible_tree(
        self,
        base_play: str,
        reads: Optional[list[CoverageType]] = None,
    ) -> AudibleTree:
        """Build an if-then decision tree for audibles at the line."""
        effective_reads = reads or [
            CoverageType.COVER_0,
            CoverageType.COVER_2,
            CoverageType.COVER_3,
        ]

        branches: list[AudibleBranch] = []
        for cov in effective_reads:
            audible_map: dict[CoverageType, tuple[str, str]] = {
                CoverageType.COVER_0: (
                    "Quick Slants",
                    "Zero blitz detected — get the ball out fast",
                ),
                CoverageType.COVER_1: (
                    "Deep Post",
                    "Single high safety — attack the post window",
                ),
                CoverageType.COVER_2: (
                    "Smash Concept",
                    "Two high safeties — corner route between CB and safety",
                ),
                CoverageType.COVER_3: (
                    "Flood Right",
                    "Cover 3 — high-low the flat defender",
                ),
                CoverageType.COVER_4: (
                    "Dig Route",
                    "Quarters coverage — sit in the intermediate window",
                ),
                CoverageType.MAN_PRESS: (
                    "Mesh Cross",
                    "Press man — rub routes to create separation",
                ),
            }

            play_name, reason = audible_map.get(
                cov, ("Check Down", f"Fallback vs {cov.value}")
            )
            branches.append(
                AudibleBranch(
                    condition=f"Read {cov.value} pre-snap",
                    audible_to=play_name,
                    reason=reason,
                )
            )

        return AudibleTree(
            base_play=base_play,
            branches=branches,
            stay_conditions=[
                "Defense shows the expected look the play is designed to beat",
                "No clear pre-snap read — run the called play",
                "Under 3 seconds on the play clock — no time to audible",
            ],
        )

    async def get_red_zone_package(self, gameplan: Gameplan) -> list[Play]:
        """Extract or generate a red-zone-specific package."""
        if gameplan.red_zone_package:
            return gameplan.red_zone_package
        return await self._build_red_zone_package(gameplan.scheme)

    async def get_anti_blitz_package(self, gameplan: Gameplan) -> list[Play]:
        """Extract or generate an anti-blitz package."""
        if gameplan.anti_blitz_package:
            return gameplan.anti_blitz_package
        return await self._build_anti_blitz_package(gameplan.scheme)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _build_core_plays(
        self, scheme: str, roster: Optional[dict[str, Any]] = None
    ) -> list[Play]:
        """Build the 10-play core from scheme concepts."""
        play_templates = [
            ("PA Boot Over", "Singleback Ace", PlayType.PLAY_ACTION, "Flood",
             "TE on the boot side"),
            ("Mesh Cross", "Gun Bunch", PlayType.PASS_SHORT, "Mesh",
             "Crossing routes underneath"),
            ("Zone Run Left", "Singleback Wing", PlayType.RUN, "Zone Run",
             "Follow the zone blocking"),
            ("Deep Post", "Gun Doubles", PlayType.PASS_DEEP, "Post-Wheel",
             "Deep post between safeties"),
            ("Quick Slants", "Gun Spread", PlayType.PASS_SHORT, "Drive",
             "Quick slant to the boundary"),
            ("Power Run", "I-Form Pro", PlayType.RUN, "Power Run",
             "Downhill behind the fullback"),
            ("RPO Glance", "Pistol Spread", PlayType.RPO, "RPO Read",
             "Read the EMOL and decide"),
            ("Screen Left", "Gun Trips", PlayType.SCREEN, "Screen",
             "RB screen to the left"),
            ("Smash Concept", "Gun Doubles", PlayType.PASS_MEDIUM, "Smash",
             "Corner and hitch combo"),
            ("Four Verticals", "Gun Spread", PlayType.PASS_DEEP, "Four Verticals",
             "All verticals — read the safeties"),
        ]

        plays: list[Play] = []
        for name, formation, ptype, concept, read in play_templates:
            plays.append(
                Play(
                    name=name,
                    formation=formation,
                    play_type=ptype,
                    concept=concept,
                    primary_read=read,
                    beats=self._get_concept_beats(concept),
                    situation_tags=self._get_concept_situations(concept),
                )
            )

        return plays

    async def _build_red_zone_package(self, scheme: str) -> list[Play]:
        """Build a red zone specific package."""
        return [
            Play(
                name="PA Crossers",
                formation="Singleback Ace",
                play_type=PlayType.PLAY_ACTION,
                concept="Mesh",
                primary_read="Crossing route in the back of the end zone",
                beats=["cover_3", "cover_1"],
                situation_tags=["red_zone"],
            ),
            Play(
                name="Fade Route",
                formation="Gun Doubles",
                play_type=PlayType.PASS_SHORT,
                concept="Fade",
                primary_read="Back shoulder fade to WR1",
                beats=["man_press", "cover_1"],
                situation_tags=["red_zone", "goal_line"],
            ),
            Play(
                name="Goal Line Power",
                formation="Goal Line",
                play_type=PlayType.RUN,
                concept="Power Run",
                primary_read="Follow the pulling guard",
                beats=["light_box"],
                situation_tags=["red_zone", "goal_line"],
            ),
        ]

    async def _build_anti_blitz_package(self, scheme: str) -> list[Play]:
        """Build an anti-blitz package."""
        return [
            Play(
                name="Quick Screen",
                formation="Gun Spread",
                play_type=PlayType.SCREEN,
                concept="Screen",
                primary_read="WR screen to the flat",
                beats=["blitz", "cover_0"],
                situation_tags=["anti_blitz"],
            ),
            Play(
                name="Slant-Flat",
                formation="Gun Doubles",
                play_type=PlayType.PASS_SHORT,
                concept="Drive",
                primary_read="Quick slant inside the blitz",
                beats=["blitz", "man_press"],
                situation_tags=["anti_blitz"],
            ),
            Play(
                name="Draw Play",
                formation="Gun Spread",
                play_type=PlayType.RUN,
                concept="Draw",
                primary_read="Let the rush go by, hit the hole",
                beats=["over_blitz"],
                situation_tags=["anti_blitz"],
            ),
        ]

    @staticmethod
    def _apply_meta_adjustments(plays: list[Play], meta: MetaReport) -> list[Play]:
        """Adjust plays based on meta insights."""
        declining = {s.lower() for s in meta.declining_strategies}

        adjusted: list[Play] = []
        for play in plays:
            # If the play concept is declining in meta, add a warning note
            if play.concept.lower() in declining:
                play = play.model_copy(
                    update={
                        "notes": (play.notes or "")
                        + " [META WARNING: This concept is declining in effectiveness.]"
                    }
                )
            adjusted.append(play)

        return adjusted

    @staticmethod
    def _estimate_difficulty(play: Play) -> float:
        """Estimate the execution difficulty of a play (0.0 - 1.0)."""
        difficulty = 0.5
        if play.play_type in (PlayType.PASS_DEEP, PlayType.PLAY_ACTION):
            difficulty += 0.2
        if play.play_type == PlayType.RPO:
            difficulty += 0.15
        if play.hot_route_adjustments and len(play.hot_route_adjustments) > 1:
            difficulty += 0.15
        return min(1.0, difficulty)

    @staticmethod
    def _find_simpler_alternative(play: Play) -> Play:
        """Return a simpler version of a play."""
        simple_map: dict[PlayType, tuple[str, str, PlayType, str]] = {
            PlayType.PASS_DEEP: ("Quick Slants", "Gun Spread", PlayType.PASS_SHORT, "Drive"),
            PlayType.RPO: ("Zone Run", "Singleback Ace", PlayType.RUN, "Zone Run"),
            PlayType.QB_RUN: ("Power Run", "I-Form Pro", PlayType.RUN, "Power Run"),
            PlayType.PLAY_ACTION: ("Quick Out", "Gun Doubles", PlayType.PASS_SHORT, "Out"),
        }
        replacement = simple_map.get(
            play.play_type,
            ("Check Down", "Gun Doubles", PlayType.PASS_SHORT, "Check"),
        )
        return Play(
            name=replacement[0],
            formation=replacement[1],
            play_type=replacement[2],
            concept=replacement[3],
            primary_read="Simplified read for execution ceiling",
            beats=play.beats,
            situation_tags=play.situation_tags,
            notes=f"Simplified replacement for {play.name}",
        )

    @staticmethod
    def _get_concept_beats(concept: str) -> list[str]:
        """Return coverages a concept typically beats."""
        beats_map: dict[str, list[str]] = {
            "Flood": ["cover_3", "cover_4"],
            "Mesh": ["cover_1", "man_press", "cover_0"],
            "Smash": ["cover_2", "cover_4_palms"],
            "Post-Wheel": ["cover_2", "cover_4"],
            "Drive": ["cover_3", "cover_3_match"],
            "Four Verticals": ["cover_3", "cover_1"],
            "Screen": ["cover_0", "blitz"],
            "RPO Read": ["cover_3", "cover_4"],
            "Zone Run": [],
            "Power Run": [],
        }
        return beats_map.get(concept, [])

    @staticmethod
    def _get_concept_situations(concept: str) -> list[str]:
        """Return situations a concept fits."""
        sit_map: dict[str, list[str]] = {
            "Flood": ["1st_and_10", "2nd_and_medium"],
            "Mesh": ["3rd_and_short", "red_zone"],
            "Smash": ["1st_and_10"],
            "Post-Wheel": ["shot_play", "1st_and_10"],
            "Drive": ["3rd_and_medium"],
            "Four Verticals": ["2nd_and_long", "3rd_and_long"],
            "Screen": ["3rd_and_long", "anti_blitz"],
            "RPO Read": ["1st_and_10", "2nd_and_short"],
            "Zone Run": ["1st_and_10", "2nd_and_short"],
            "Power Run": ["3rd_and_short", "goal_line"],
        }
        return sit_map.get(concept, [])

    @staticmethod
    def _summarize_opponent(data: dict[str, Any]) -> str:
        """Generate a human-readable opponent summary."""
        tendencies = data.get("tendencies", {})
        cov = tendencies.get("favorite_coverage", "unknown")
        blitz = tendencies.get("blitz_rate", 0)
        run_stop = tendencies.get("run_stop_rate", 0)
        return (
            f"Opponent favors {cov} coverage with a {blitz:.0%} blitz rate "
            f"and {run_stop:.0%} run stop rate."
        )
