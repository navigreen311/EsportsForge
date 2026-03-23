"""InstallAI — converts recommendations into executable install packages.

Generates call sheets, mini eBooks, audible trees, red zone packages, and
anti-blitz scripts.  Every audible tree follows the three-layer structure:
base call -> if bagged -> if they adjust.
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4

from app.schemas.install import (
    AntiBlitzScript,
    AudibleLayer,
    AudibleTree,
    CallSheet,
    InstallPackage,
    MiniEBook,
    RedZonePackage,
)

logger = logging.getLogger(__name__)


class InstallAI:
    """Converts gameplans and recommendations into install packages.

    In production, each generator integrates with the recommendation engine
    and player twin for personalisation.  Current MVP uses deterministic
    logic to produce structurally complete packages.
    """

    # ------------------------------------------------------------------
    # Call sheet generation
    # ------------------------------------------------------------------

    def generate_call_sheet(
        self,
        gameplan: dict,
        player_profile: dict | None = None,
    ) -> CallSheet:
        """Convert a gameplan into a formatted call sheet.

        Organises plays by situation, adds red zone / two-minute sections,
        and generates audible trees for key plays.

        Args:
            gameplan: Raw gameplan data with plays, formations, situations.
            player_profile: Optional player twin data for personalisation.

        Returns:
            Formatted CallSheet ready for study.
        """
        player_profile = player_profile or {}
        title = gameplan.get("title", "madden26")

        # Build situation groups from gameplan
        situation_groups: dict[str, list[str]] = {}
        for play in gameplan.get("plays", []):
            situation = play.get("situation", "general")
            name = play.get("name", "Unknown Play")
            situation_groups.setdefault(situation, []).append(name)

        # Extract red zone and two-minute plays
        red_zone_calls = [
            p.get("name", "")
            for p in gameplan.get("plays", [])
            if p.get("situation") == "red_zone"
        ]
        two_minute_calls = [
            p.get("name", "")
            for p in gameplan.get("plays", [])
            if p.get("situation") == "two_minute"
        ]

        # Generate audible trees for key plays
        audibles = []
        key_plays = gameplan.get("key_plays", [])
        for play_data in key_plays[:5]:  # Cap at 5 audible trees
            reads = play_data.get("reads", [])
            tree = self.generate_audible_tree(
                play_data.get("name", "Unknown"),
                reads,
            )
            audibles.append(tree)

        notes = gameplan.get("notes", "")
        style = player_profile.get("style", "")
        if style:
            notes = f"[{style} style adjustments applied] {notes}"

        call_sheet = CallSheet(
            title=title,
            situation_groups=situation_groups,
            red_zone_calls=red_zone_calls,
            two_minute_calls=two_minute_calls,
            audibles=audibles,
            notes=notes,
        )
        logger.info("Generated call sheet for title=%s with %d situations", title, len(situation_groups))
        return call_sheet

    # ------------------------------------------------------------------
    # Mini eBook generation
    # ------------------------------------------------------------------

    def generate_ebook(
        self,
        topic: str,
        recommendations: list[dict] | None = None,
    ) -> MiniEBook:
        """Generate a mini eBook for a concept.

        Produces a condensed learning document with summary, sections,
        key takeaways, and practice drills.

        Args:
            topic: The concept being taught.
            recommendations: Optional list of recommendation dicts.

        Returns:
            MiniEBook with structured learning content.
        """
        recommendations = recommendations or []

        summary = f"Complete guide to mastering {topic}."
        if recommendations:
            summary += f" Covers {len(recommendations)} key recommendation(s)."

        # Build sections from recommendations
        sections: list[dict[str, str]] = [
            {"heading": "Overview", "content": f"Understanding {topic} and why it matters."},
        ]
        key_takeaways: list[str] = []
        practice_drills: list[str] = []

        for i, rec in enumerate(recommendations, start=1):
            label = rec.get("label", f"Concept {i}")
            detail = rec.get("description", f"Details for {label}.")
            drill = rec.get("drill", "")

            sections.append({"heading": label, "content": detail})
            key_takeaways.append(f"Master {label} for immediate impact.")
            if drill:
                practice_drills.append(drill)

        if not key_takeaways:
            key_takeaways.append(f"Focus on understanding {topic} fundamentals.")
        if not practice_drills:
            practice_drills.append(f"Practice {topic} concepts in lab mode.")

        ebook = MiniEBook(
            topic=topic,
            summary=summary,
            sections=sections,
            key_takeaways=key_takeaways,
            practice_drills=practice_drills,
        )
        logger.info("Generated mini eBook for topic=%s with %d sections", topic, len(sections))
        return ebook

    # ------------------------------------------------------------------
    # Audible tree generation
    # ------------------------------------------------------------------

    def generate_audible_tree(
        self,
        base_play: str,
        reads: list[dict] | None = None,
    ) -> AudibleTree:
        """Generate a three-layer if-then decision tree.

        Layer 1 (base_call): The primary read and action.
        Layer 2 (if_bagged): What to do if the base call is taken away.
        Layer 3 (if_they_adjust): Counter when opponent adapts to layer 2.

        Args:
            base_play: The base play name.
            reads: Optional list of read dicts with condition/action pairs.

        Returns:
            AudibleTree with three decision layers.
        """
        reads = reads or []

        # Layer 1: base read
        if len(reads) >= 1:
            base_read = reads[0]
            base_call = AudibleLayer(
                condition=base_read.get("condition", "Default coverage look"),
                action=base_read.get("action", f"Execute {base_play} as called"),
                notes=base_read.get("notes", ""),
            )
        else:
            base_call = AudibleLayer(
                condition="Standard defensive alignment",
                action=f"Execute {base_play} as called",
                notes="No pre-snap adjustment needed.",
            )

        # Layer 2: if bagged
        if len(reads) >= 2:
            bagged_read = reads[1]
            if_bagged = AudibleLayer(
                condition=bagged_read.get("condition", "Base look taken away"),
                action=bagged_read.get("action", f"Check to {base_play} counter"),
                notes=bagged_read.get("notes", ""),
            )
        else:
            if_bagged = AudibleLayer(
                condition=f"{base_play} coverage detected / play taken away",
                action=f"Audible to {base_play} counter — attack opposite side",
                notes="Look for the void left by overcommitment.",
            )

        # Layer 3: if they adjust
        if len(reads) >= 3:
            adjust_read = reads[2]
            if_they_adjust = AudibleLayer(
                condition=adjust_read.get("condition", "Opponent adjusts to counter"),
                action=adjust_read.get("action", f"Go back to original {base_play} with wrinkle"),
                notes=adjust_read.get("notes", ""),
            )
        else:
            if_they_adjust = AudibleLayer(
                condition="Opponent adjusts to your counter",
                action=f"Reset to {base_play} — their adjustment reopens the original look",
                notes="The chess match resets. Trust the base read.",
            )

        tree = AudibleTree(
            base_play=base_play,
            base_call=base_call,
            if_bagged=if_bagged,
            if_they_adjust=if_they_adjust,
        )
        logger.info("Generated audible tree for base_play=%s", base_play)
        return tree

    # ------------------------------------------------------------------
    # Red zone package
    # ------------------------------------------------------------------

    def generate_red_zone_package(
        self,
        gameplan: dict,
    ) -> RedZonePackage:
        """Generate a red zone specific install from a gameplan.

        Extracts red zone formations, plays, goal line packages,
        and builds audible trees for scoring-area reads.

        Args:
            gameplan: Raw gameplan data.

        Returns:
            RedZonePackage with scoring-area specifics.
        """
        rz_data = gameplan.get("red_zone", {})

        formations = rz_data.get("formations", [])
        plays = rz_data.get("plays", [])
        goal_line = rz_data.get("goal_line", [])
        fade_routes = rz_data.get("fades", [])

        # Default formations if none specified
        if not formations:
            formations = ["Shotgun Bunch", "Singleback Ace", "Goal Line"]
        if not plays:
            plays = [
                p.get("name", "")
                for p in gameplan.get("plays", [])
                if p.get("situation") == "red_zone"
            ]
        if not goal_line:
            goal_line = ["QB Sneak", "Power Run", "PA Goal Line"]

        # Build red zone audible trees
        rz_reads: list[AudibleTree] = []
        for play_name in plays[:3]:
            tree = self.generate_audible_tree(play_name, rz_data.get("reads", []))
            rz_reads.append(tree)

        package = RedZonePackage(
            formations=formations,
            plays=plays,
            reads=rz_reads,
            goal_line_package=goal_line,
            fade_routes=fade_routes,
            notes=rz_data.get("notes", "Score. Every. Time."),
        )
        logger.info("Generated red zone package with %d plays", len(plays))
        return package

    # ------------------------------------------------------------------
    # Anti-blitz scripts
    # ------------------------------------------------------------------

    def generate_anti_blitz_package(
        self,
        gameplan: dict,
    ) -> list[AntiBlitzScript]:
        """Generate anti-blitz scripts from a gameplan.

        Creates counter-scripts for each identified blitz type, including
        hot routes, quick passes, and protection adjustments.

        Args:
            gameplan: Raw gameplan data with blitz scouting info.

        Returns:
            List of AntiBlitzScript, one per blitz type.
        """
        blitz_data = gameplan.get("blitz_scouting", [])

        # Default blitz types if none provided
        if not blitz_data:
            blitz_data = [
                {
                    "type": "edge_blitz",
                    "hot_routes": ["Slant", "Quick Out"],
                    "quick_passes": ["Quick Slant", "Bubble Screen"],
                    "protections": ["Slide Left", "Max Protect"],
                },
                {
                    "type": "a_gap_blitz",
                    "hot_routes": ["Seam", "Drag"],
                    "quick_passes": ["Draw", "Screen Pass"],
                    "protections": ["ID Mike", "Double A-Gap"],
                },
            ]

        scripts: list[AntiBlitzScript] = []
        for blitz in blitz_data:
            blitz_type = blitz.get("type", "unknown_blitz")
            hot_routes = blitz.get("hot_routes", [])
            quick_passes = blitz.get("quick_passes", [])
            protections = blitz.get("protections", [])

            # Build an audible tree for this blitz type
            reads = [
                {"condition": f"{blitz_type} detected pre-snap", "action": hot_routes[0] if hot_routes else "Hot route"},
                {"condition": "Delayed blitz / disguised", "action": quick_passes[0] if quick_passes else "Quick pass"},
                {"condition": "Blitz + coverage rotation", "action": "Attack vacated zone"},
            ]
            tree = self.generate_audible_tree(f"Anti-{blitz_type}", reads)

            script = AntiBlitzScript(
                blitz_type=blitz_type,
                hot_routes=hot_routes,
                quick_passes=quick_passes,
                protection_adjustments=protections,
                audible_tree=tree,
                notes=f"Counter package for {blitz_type}.",
            )
            scripts.append(script)

        logger.info("Generated %d anti-blitz scripts", len(scripts))
        return scripts

    # ------------------------------------------------------------------
    # Full install package
    # ------------------------------------------------------------------

    def create_full_install(
        self,
        gameplan: dict,
        player_profile: dict | None = None,
        opponent: str = "",
    ) -> InstallPackage:
        """Create a complete install package from a gameplan.

        Combines call sheet, mini eBook, audible trees, red zone package,
        and anti-blitz scripts into a single deliverable.

        Args:
            gameplan: Raw gameplan data.
            player_profile: Optional player twin data for personalisation.
            opponent: Optional opponent identifier.

        Returns:
            Complete InstallPackage ready for study and execution.
        """
        player_profile = player_profile or {}
        title = gameplan.get("title", "madden26")
        user_id = player_profile.get("user_id", "unknown")

        call_sheet = self.generate_call_sheet(gameplan, player_profile)

        # Build eBook from gameplan recommendations
        recommendations = gameplan.get("recommendations", [])
        topic = gameplan.get("topic", f"Gameplan vs {opponent}" if opponent else "Weekly Gameplan")
        ebook = self.generate_ebook(topic, recommendations)

        # Collect all audible trees from call sheet + extras
        audible_trees = list(call_sheet.audibles)
        for play_data in gameplan.get("audible_plays", []):
            tree = self.generate_audible_tree(
                play_data.get("name", "Unknown"),
                play_data.get("reads", []),
            )
            audible_trees.append(tree)

        red_zone_package = self.generate_red_zone_package(gameplan)
        anti_blitz_scripts = self.generate_anti_blitz_package(gameplan)

        package = InstallPackage(
            user_id=user_id,
            title=title,
            opponent=opponent,
            call_sheet=call_sheet,
            ebook=ebook,
            audible_trees=audible_trees,
            red_zone_package=red_zone_package,
            anti_blitz_scripts=anti_blitz_scripts,
        )
        logger.info(
            "Created full install package for user=%s title=%s opponent=%s",
            user_id, title, opponent,
        )
        return package


# Module-level singleton for use by the API layer
install_ai_engine = InstallAI()
