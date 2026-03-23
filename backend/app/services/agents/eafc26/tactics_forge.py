"""TacticsForge — formation meta tracker, custom instruction optimizer, counter-tactical library.

Tracks the EA FC 26 competitive meta across formations, generates custom
tactical instructions, and provides a counter-tactic library for in-game adjustments.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.schemas.eafc26.tactics import (
    CounterTactic,
    CustomInstruction,
    FormationMeta,
    FormationRating,
    FormationTrend,
    InstructionPreset,
    TacticalReport,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Meta formation data
# ---------------------------------------------------------------------------

_CURRENT_PATCH = "4.1"

_FORMATIONS: dict[str, dict[str, Any]] = {
    "4-3-3 (4)": {
        "rating": "S",
        "trend": "stable",
        "usage_pct": 18.5,
        "strengths": ["Wide play", "Wing overloads", "CAM creativity"],
        "weaknesses": ["Vulnerable to counter-attacks through the middle", "CDM gap exploitable"],
        "best_playstyle": "Possession / Tiki-Taka",
    },
    "4-2-3-1": {
        "rating": "S",
        "trend": "rising",
        "usage_pct": 16.2,
        "strengths": ["Defensive solidity", "Double pivot protection", "Counter-attack speed"],
        "weaknesses": ["Isolated striker", "Predictable build-up"],
        "best_playstyle": "Fast Build Up",
    },
    "4-1-2-1-2 (2)": {
        "rating": "A",
        "trend": "declining",
        "usage_pct": 12.8,
        "strengths": ["Central overloads", "Quick passing triangles", "Two-striker partnership"],
        "weaknesses": ["No width without fullbacks", "Exposed flanks"],
        "best_playstyle": "Direct Passing",
    },
    "4-4-2": {
        "rating": "A",
        "trend": "rising",
        "usage_pct": 10.5,
        "strengths": ["Balanced shape", "Defensive compactness", "Easy to learn"],
        "weaknesses": ["Midfield can be outnumbered", "Limited creative options"],
        "best_playstyle": "Balanced",
    },
    "3-5-2": {
        "rating": "B",
        "trend": "stable",
        "usage_pct": 7.3,
        "strengths": ["Midfield dominance", "Wing-back width", "Striker partnership"],
        "weaknesses": ["Three-back is risky on counters", "Wing-backs must be fit"],
        "best_playstyle": "Possession",
    },
    "4-3-2-1": {
        "rating": "B",
        "trend": "declining",
        "usage_pct": 5.8,
        "strengths": ["Compact midfield", "Inside forwards cut in", "Strong through the middle"],
        "weaknesses": ["Narrow shape", "Wing play limited"],
        "best_playstyle": "Direct Passing",
    },
    "5-2-1-2": {
        "rating": "C",
        "trend": "stable",
        "usage_pct": 3.2,
        "strengths": ["Defensive fortress", "Hard to break down", "Counter-attack"],
        "weaknesses": ["Requires manual trigger runs", "Predictable park-the-bus feel"],
        "best_playstyle": "Long Ball / Counter",
    },
}

# Counter-tactic library
_COUNTER_TACTICS: dict[str, CounterTactic] = {
    "4-3-3 (4)": CounterTactic(
        opponent_formation="4-3-3 (4)",
        recommended_formation="4-2-3-1",
        key_adjustments=[
            "Double pivot neutralizes the CAM",
            "Drop back to 45 depth, absorb pressure",
            "Quick counter through the middle when they push fullbacks forward",
        ],
        player_instructions=[
            "CDMs: Stay back while attacking, Cover center",
            "Wingers: Come back on defense, Get in behind on attack",
            "ST: Stay central, Target man to hold up play",
        ],
        critical_moment="When opponent's fullbacks push up, hit the space behind with through balls",
        confidence=0.82,
    ),
    "4-2-3-1": CounterTactic(
        opponent_formation="4-2-3-1",
        recommended_formation="4-1-2-1-2 (2)",
        key_adjustments=[
            "Narrow diamond overwhelms the double pivot",
            "Two strikers create 2v2 against their CBs",
            "Press after bad touch to force turnovers in their build-up",
        ],
        player_instructions=[
            "CAM: Stay forward, Free roam",
            "CMs: Get forward, Cover wing",
            "STs: Get in behind, Stay central",
        ],
        critical_moment="When their CDMs are caught square, play a quick one-two through the gap",
        confidence=0.78,
    ),
    "4-1-2-1-2 (2)": CounterTactic(
        opponent_formation="4-1-2-1-2 (2)",
        recommended_formation="4-3-3 (4)",
        key_adjustments=[
            "Width exploits the narrow diamond — use wingers high and wide",
            "Full-backs overlap to create 2v1 on the flanks",
            "Stretch play to pull their CMs out of position",
        ],
        player_instructions=[
            "Wingers: Stay wide, Get in behind",
            "Fullbacks: Join the attack, Overlap",
            "CDM: Stay back while attacking, Cut passing lanes",
        ],
        critical_moment="Isolate your winger against their CM who got dragged out wide",
        confidence=0.80,
    ),
    "4-4-2": CounterTactic(
        opponent_formation="4-4-2",
        recommended_formation="4-3-3 (4)",
        key_adjustments=[
            "Extra midfielder creates numerical advantage in the center",
            "CAM operates between the lines of their midfield and defense",
            "Quick passing to bypass their flat-four midfield line",
        ],
        player_instructions=[
            "CAM: Stay forward, Drift wide occasionally",
            "CMs: Balanced attack, Cover center",
            "Wingers: Cut inside to overload the middle",
        ],
        critical_moment="Find the CAM in the pocket between their lines — they can't track the runner",
        confidence=0.76,
    ),
}

# Custom instruction presets
_INSTRUCTION_PRESETS: dict[str, InstructionPreset] = {
    "possession": InstructionPreset(
        name="Possession Master",
        description="Slow, controlled build-up with maximum passing options",
        build_up="Slow Build Up",
        chance_creation="Possession",
        defence="Balanced",
        width=55,
        depth=50,
        players_in_box=4,
        corners="Short",
        free_kicks="Short",
    ),
    "counter_attack": InstructionPreset(
        name="Lightning Counter",
        description="Absorb pressure and hit on the break with pace",
        build_up="Fast Build Up",
        chance_creation="Direct Passing",
        defence="Drop Back",
        width=40,
        depth=35,
        players_in_box=3,
        corners="Default",
        free_kicks="Default",
    ),
    "press_heavy": InstructionPreset(
        name="High Press",
        description="Aggressive pressing to win the ball high up the pitch",
        build_up="Short Passing",
        chance_creation="Forward Runs",
        defence="Press After Possession Loss",
        width=50,
        depth=70,
        players_in_box=5,
        corners="Default",
        free_kicks="Default",
    ),
    "park_the_bus": InstructionPreset(
        name="Lockdown",
        description="Ultra-defensive setup for protecting a lead",
        build_up="Long Ball",
        chance_creation="Direct Passing",
        defence="Drop Back",
        width=35,
        depth=25,
        players_in_box=2,
        corners="Short",
        free_kicks="Default",
    ),
}


class TacticsForge:
    """EA FC 26 tactical analysis and counter-tactic engine.

    Tracks formation meta, optimizes custom instructions, and provides
    a counter-tactical library for adapting during matches.
    """

    # ------------------------------------------------------------------
    # Formation meta tracker
    # ------------------------------------------------------------------

    def get_formation_meta(self) -> TacticalReport:
        """Return the current formation meta snapshot across all tracked formations."""
        formations: list[FormationMeta] = []
        for name, data in _FORMATIONS.items():
            trend_map = {"rising": FormationTrend.RISING, "declining": FormationTrend.DECLINING}
            trend = trend_map.get(data["trend"], FormationTrend.STABLE)

            rating_map = {"S": FormationRating.S, "A": FormationRating.A,
                          "B": FormationRating.B, "C": FormationRating.C}
            rating = rating_map.get(data["rating"], FormationRating.B)

            formations.append(FormationMeta(
                name=name,
                rating=rating,
                trend=trend,
                usage_pct=data["usage_pct"],
                strengths=data["strengths"],
                weaknesses=data["weaknesses"],
                best_playstyle=data["best_playstyle"],
            ))

        formations.sort(key=lambda f: f.usage_pct, reverse=True)
        top = formations[0] if formations else None

        return TacticalReport(
            patch_version=_CURRENT_PATCH,
            report_date=datetime.now(timezone.utc).date().isoformat(),
            formations=formations,
            top_formation=top.name if top else "Unknown",
            meta_summary=(
                f"EA FC 26 patch {_CURRENT_PATCH}: 4-3-3 (4) and 4-2-3-1 dominate the meta. "
                f"4-2-3-1 is rising due to its counter-attack potential. "
                f"Narrow diamonds are declining as players exploit width."
            ),
        )

    def rate_formation(self, formation: str) -> FormationMeta:
        """Rate a specific formation against the current meta."""
        data = _FORMATIONS.get(formation)
        if not data:
            return FormationMeta(
                name=formation,
                rating=FormationRating.C,
                trend=FormationTrend.STABLE,
                usage_pct=0.0,
                strengths=["Unknown formation — not tracked in current meta"],
                weaknesses=["No data available"],
                best_playstyle="Unknown",
            )

        trend_map = {"rising": FormationTrend.RISING, "declining": FormationTrend.DECLINING}
        trend = trend_map.get(data["trend"], FormationTrend.STABLE)
        rating_map = {"S": FormationRating.S, "A": FormationRating.A,
                      "B": FormationRating.B, "C": FormationRating.C}
        rating = rating_map.get(data["rating"], FormationRating.B)

        return FormationMeta(
            name=formation,
            rating=rating,
            trend=trend,
            usage_pct=data["usage_pct"],
            strengths=data["strengths"],
            weaknesses=data["weaknesses"],
            best_playstyle=data["best_playstyle"],
        )

    # ------------------------------------------------------------------
    # Custom instruction optimizer
    # ------------------------------------------------------------------

    def optimize_instructions(
        self,
        formation: str,
        playstyle: str = "balanced",
        opponent_formation: str | None = None,
    ) -> CustomInstruction:
        """Generate optimized custom tactical instructions for a formation.

        Takes the formation, desired playstyle, and optionally the opponent
        formation to produce tuned width/depth/pressing instructions.
        """
        preset = _INSTRUCTION_PRESETS.get(playstyle, _INSTRUCTION_PRESETS["possession"])

        # Adjust depth/width based on opponent
        depth = preset.depth
        width = preset.width
        adjustments: list[str] = []

        if opponent_formation:
            opp_data = _FORMATIONS.get(opponent_formation, {})
            opp_strengths = opp_data.get("strengths", [])

            # If opponent is wide, compress width
            if any("wide" in s.lower() or "wing" in s.lower() for s in opp_strengths):
                width = max(30, width - 10)
                adjustments.append("Reduced width to counter opponent's wide play")

            # If opponent is narrow, expand width
            if any("central" in s.lower() or "narrow" in s.lower() for s in opp_strengths):
                width = min(70, width + 10)
                adjustments.append("Increased width to stretch opponent's narrow shape")

            # If opponent counters, increase depth
            if any("counter" in s.lower() for s in opp_strengths):
                depth = max(30, depth - 10)
                adjustments.append("Dropped depth to limit counter-attack space")

        # Formation-specific tweaks
        if "3-5-2" in formation:
            adjustments.append("Wing-backs set to Always Overlap for width coverage")
            width = max(width, 50)
        elif "4-1-2-1-2" in formation:
            adjustments.append("Fullbacks set to Join the Attack for width")

        return CustomInstruction(
            formation=formation,
            preset_name=preset.name,
            build_up=preset.build_up,
            chance_creation=preset.chance_creation,
            defence=preset.defence,
            width=width,
            depth=depth,
            players_in_box=preset.players_in_box,
            corners=preset.corners,
            free_kicks=preset.free_kicks,
            adjustments=adjustments,
        )

    # ------------------------------------------------------------------
    # Counter-tactical library
    # ------------------------------------------------------------------

    def get_counter_tactic(self, opponent_formation: str) -> CounterTactic:
        """Retrieve a counter-tactic for the given opponent formation."""
        ct = _COUNTER_TACTICS.get(opponent_formation)
        if ct:
            return ct

        # Build a generic counter
        return CounterTactic(
            opponent_formation=opponent_formation,
            recommended_formation="4-2-3-1",
            key_adjustments=[
                "Default to 4-2-3-1 for defensive security",
                "Double pivot provides numerical safety in midfield",
                "Observe opponent patterns in first 10 minutes before committing to a press",
            ],
            player_instructions=[
                "CDMs: Stay back, Cover center",
                "Wingers: Come back on defense",
                "ST: False 9 or Target man based on opponent back line height",
            ],
            critical_moment="Identify the opponent's preferred attacking lane before half-time",
            confidence=0.55,
        )

    def list_counter_tactics(self) -> list[CounterTactic]:
        """Return all available counter-tactics in the library."""
        return list(_COUNTER_TACTICS.values())

    # ------------------------------------------------------------------
    # Instruction presets
    # ------------------------------------------------------------------

    def list_presets(self) -> list[InstructionPreset]:
        """Return all available instruction presets."""
        return list(_INSTRUCTION_PRESETS.values())


# Module-level singleton
tactics_forge = TacticsForge()
