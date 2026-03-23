"""OnlineCareer Forge — fighter build optimizer, perk ranking, style-path by win rate.

Provides build recommendations for UFC 5 online career mode, ranking perks
by effectiveness, optimizing attribute allocation, and selecting style paths
based on win rate data.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.ufc5.combat import (
    ArchetypeStyle,
    FighterArchetype,
    FighterBuild,
    FighterStylePath,
    PerkRanking,
    StrikeType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — Perk database
# ---------------------------------------------------------------------------

_PERKS: list[dict[str, Any]] = [
    {
        "name": "Iron Chin",
        "tier": "S",
        "styles": [ArchetypeStyle.BRAWLER, ArchetypeStyle.PRESSURE],
        "impact": 0.06,
        "desc": "Reduces KO vulnerability by 25%. Essential for fighters who trade.",
    },
    {
        "name": "Cardio King",
        "tier": "S",
        "styles": [ArchetypeStyle.VOLUME, ArchetypeStyle.PRESSURE, ArchetypeStyle.WRESTLER],
        "impact": 0.07,
        "desc": "Reduces stamina drain by 20%. Dominant in championship rounds.",
    },
    {
        "name": "Fast Hands",
        "tier": "A",
        "styles": [ArchetypeStyle.COUNTER, ArchetypeStyle.VOLUME, ArchetypeStyle.POINT_FIGHTER],
        "impact": 0.05,
        "desc": "Increases hand speed by 10%. Better interrupt and counter windows.",
    },
    {
        "name": "Granite Legs",
        "tier": "A",
        "styles": [ArchetypeStyle.KICKBOXER, ArchetypeStyle.COUNTER],
        "impact": 0.04,
        "desc": "Reduces leg damage by 30%. Counters calf kick meta.",
    },
    {
        "name": "Takedown Artist",
        "tier": "S",
        "styles": [ArchetypeStyle.WRESTLER, ArchetypeStyle.GRAPPLER],
        "impact": 0.06,
        "desc": "Increases takedown success by 15%. Wrestling becomes dominant.",
    },
    {
        "name": "Submission Ace",
        "tier": "A",
        "styles": [ArchetypeStyle.GRAPPLER],
        "impact": 0.05,
        "desc": "Faster submission gates and higher finish rate on the ground.",
    },
    {
        "name": "Slick Movement",
        "tier": "A",
        "styles": [ArchetypeStyle.COUNTER, ArchetypeStyle.POINT_FIGHTER, ArchetypeStyle.SWITCH_STANCE],
        "impact": 0.04,
        "desc": "Better lateral movement and angle creation on footwork.",
    },
    {
        "name": "Power Puncher",
        "tier": "A",
        "styles": [ArchetypeStyle.BRAWLER, ArchetypeStyle.COUNTER],
        "impact": 0.05,
        "desc": "Increases punch damage by 12%. Higher KO probability per shot.",
    },
    {
        "name": "Body Snatcher",
        "tier": "B",
        "styles": [ArchetypeStyle.PRESSURE, ArchetypeStyle.VOLUME],
        "impact": 0.03,
        "desc": "Body shots deal 20% more damage. Accelerates stamina drain.",
    },
    {
        "name": "Sprawl Master",
        "tier": "A",
        "styles": [ArchetypeStyle.KICKBOXER, ArchetypeStyle.COUNTER, ArchetypeStyle.BRAWLER],
        "impact": 0.04,
        "desc": "Improves takedown defense by 15%. Keep the fight standing.",
    },
    {
        "name": "Ground Control",
        "tier": "B",
        "styles": [ArchetypeStyle.WRESTLER, ArchetypeStyle.GRAPPLER],
        "impact": 0.03,
        "desc": "Reduces opponent's escape and transition success from bottom.",
    },
    {
        "name": "Precision Kicks",
        "tier": "B",
        "styles": [ArchetypeStyle.KICKBOXER, ArchetypeStyle.SWITCH_STANCE],
        "impact": 0.03,
        "desc": "Increases kick accuracy and damage by 10%.",
    },
    {
        "name": "Cage Cutter",
        "tier": "B",
        "styles": [ArchetypeStyle.PRESSURE, ArchetypeStyle.WRESTLER],
        "impact": 0.03,
        "desc": "Better octagon control footwork, harder for opponent to circle out.",
    },
    {
        "name": "Recovery Boost",
        "tier": "B",
        "styles": [ArchetypeStyle.BRAWLER, ArchetypeStyle.PRESSURE],
        "impact": 0.02,
        "desc": "Faster recovery from rocked/stunned state.",
    },
    {
        "name": "Clinch King",
        "tier": "C",
        "styles": [ArchetypeStyle.WRESTLER, ArchetypeStyle.GRAPPLER],
        "impact": 0.02,
        "desc": "Better clinch control and dirty boxing damage.",
    },
    {
        "name": "Head Movement",
        "tier": "A",
        "styles": [ArchetypeStyle.COUNTER, ArchetypeStyle.BRAWLER, ArchetypeStyle.SWITCH_STANCE],
        "impact": 0.05,
        "desc": "Improves slip and weave effectiveness by 15%.",
    },
]

# Win rate data by style + weight class
_STYLE_WIN_RATES: dict[tuple[ArchetypeStyle, str], float] = {
    (ArchetypeStyle.WRESTLER, "lightweight"): 0.62,
    (ArchetypeStyle.WRESTLER, "welterweight"): 0.60,
    (ArchetypeStyle.WRESTLER, "middleweight"): 0.58,
    (ArchetypeStyle.WRESTLER, "heavyweight"): 0.55,
    (ArchetypeStyle.GRAPPLER, "lightweight"): 0.58,
    (ArchetypeStyle.GRAPPLER, "welterweight"): 0.56,
    (ArchetypeStyle.GRAPPLER, "bantamweight"): 0.60,
    (ArchetypeStyle.COUNTER, "lightweight"): 0.57,
    (ArchetypeStyle.COUNTER, "welterweight"): 0.56,
    (ArchetypeStyle.COUNTER, "middleweight"): 0.55,
    (ArchetypeStyle.COUNTER, "featherweight"): 0.58,
    (ArchetypeStyle.PRESSURE, "lightweight"): 0.55,
    (ArchetypeStyle.PRESSURE, "welterweight"): 0.56,
    (ArchetypeStyle.PRESSURE, "bantamweight"): 0.57,
    (ArchetypeStyle.VOLUME, "bantamweight"): 0.56,
    (ArchetypeStyle.VOLUME, "featherweight"): 0.55,
    (ArchetypeStyle.VOLUME, "flyweight"): 0.58,
    (ArchetypeStyle.KICKBOXER, "middleweight"): 0.54,
    (ArchetypeStyle.KICKBOXER, "light_heavyweight"): 0.55,
    (ArchetypeStyle.KICKBOXER, "welterweight"): 0.53,
    (ArchetypeStyle.BRAWLER, "heavyweight"): 0.53,
    (ArchetypeStyle.BRAWLER, "middleweight"): 0.50,
    (ArchetypeStyle.POINT_FIGHTER, "featherweight"): 0.52,
    (ArchetypeStyle.POINT_FIGHTER, "bantamweight"): 0.51,
    (ArchetypeStyle.SWITCH_STANCE, "lightweight"): 0.54,
    (ArchetypeStyle.SWITCH_STANCE, "welterweight"): 0.53,
}

# Recommended minimum attributes by style
_STYLE_ATTRIBUTES: dict[ArchetypeStyle, dict[str, int]] = {
    ArchetypeStyle.PRESSURE: {
        "punch_speed": 80, "punch_power": 75, "cardio": 85,
        "footwork": 78, "chin": 80, "body_toughness": 80,
    },
    ArchetypeStyle.COUNTER: {
        "punch_speed": 85, "punch_power": 80, "head_movement": 88,
        "footwork": 85, "chin": 75, "reaction": 90,
    },
    ArchetypeStyle.VOLUME: {
        "punch_speed": 85, "cardio": 90, "footwork": 80,
        "punch_power": 70, "chin": 75, "body_toughness": 78,
    },
    ArchetypeStyle.WRESTLER: {
        "takedown": 90, "top_control": 85, "clinch_control": 80,
        "cardio": 82, "punch_power": 70, "chin": 78,
    },
    ArchetypeStyle.GRAPPLER: {
        "submission_offense": 90, "takedown": 80, "bottom_game": 88,
        "top_control": 82, "cardio": 80, "clinch_control": 78,
    },
    ArchetypeStyle.KICKBOXER: {
        "kick_power": 88, "kick_speed": 85, "footwork": 85,
        "punch_speed": 78, "takedown_defense": 80, "cardio": 78,
    },
    ArchetypeStyle.BRAWLER: {
        "punch_power": 92, "chin": 90, "body_toughness": 85,
        "recovery": 85, "punch_speed": 70, "footwork": 65,
    },
    ArchetypeStyle.POINT_FIGHTER: {
        "footwork": 90, "punch_speed": 85, "head_movement": 85,
        "cardio": 82, "takedown_defense": 78, "reaction": 85,
    },
    ArchetypeStyle.SWITCH_STANCE: {
        "punch_speed": 82, "footwork": 88, "head_movement": 82,
        "punch_power": 78, "kick_speed": 80, "reaction": 85,
    },
}

_SKILL_PRIORITY: dict[ArchetypeStyle, list[str]] = {
    ArchetypeStyle.PRESSURE: ["Cardio", "Striking", "Clinch", "Movement"],
    ArchetypeStyle.COUNTER: ["Head Movement", "Striking", "Footwork", "Cardio"],
    ArchetypeStyle.VOLUME: ["Cardio", "Striking Speed", "Footwork", "Chin"],
    ArchetypeStyle.WRESTLER: ["Takedowns", "Top Control", "Clinch", "Cardio"],
    ArchetypeStyle.GRAPPLER: ["Submissions", "Takedowns", "Ground Game", "Cardio"],
    ArchetypeStyle.KICKBOXER: ["Kicks", "Footwork", "TDD", "Striking"],
    ArchetypeStyle.BRAWLER: ["Power", "Chin", "Recovery", "Body Toughness"],
    ArchetypeStyle.POINT_FIGHTER: ["Footwork", "Speed", "Head Movement", "TDD"],
    ArchetypeStyle.SWITCH_STANCE: ["Footwork", "Speed", "Striking", "Head Movement"],
}


class OnlineCareerForge:
    """Fighter build optimizer for UFC 5 online career mode.

    Ranks perks, recommends attribute allocations, and selects optimal
    style paths based on win rate data across weight classes.
    """

    def get_perk_rankings(
        self,
        style: ArchetypeStyle | None = None,
    ) -> list[PerkRanking]:
        """
        Return all perks ranked by effectiveness.

        Optionally filter by synergy with a given style.
        """
        rankings = [
            PerkRanking(
                perk_name=p["name"],
                tier=p["tier"],
                synergy_styles=p["styles"],
                win_rate_impact=p["impact"],
                description=p["desc"],
            )
            for p in _PERKS
        ]

        if style:
            # Sort by: perks that synergize with style first, then by tier
            tier_order = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}
            rankings.sort(
                key=lambda r: (
                    0 if style in r.synergy_styles else 1,
                    tier_order.get(r.tier, 5),
                    -r.win_rate_impact,
                )
            )
        else:
            tier_order = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}
            rankings.sort(
                key=lambda r: (tier_order.get(r.tier, 5), -r.win_rate_impact)
            )

        return rankings

    def get_style_paths(
        self,
        weight_class: str | None = None,
    ) -> list[FighterStylePath]:
        """
        Return style paths ranked by win rate.

        Optionally filter to a specific weight class.
        """
        paths: list[FighterStylePath] = []
        for (style, wc), win_rate in _STYLE_WIN_RATES.items():
            if weight_class and wc != weight_class:
                continue
            perks = self._top_perks_for_style(style, limit=3)
            attrs = _STYLE_ATTRIBUTES.get(style, {})
            skills = _SKILL_PRIORITY.get(style, [])

            paths.append(
                FighterStylePath(
                    style=style,
                    weight_class=wc,
                    win_rate=win_rate,
                    recommended_perks=perks,
                    key_attributes=attrs,
                    skill_priority=skills,
                )
            )

        paths.sort(key=lambda p: -p.win_rate)
        return paths

    def build_fighter(
        self,
        name: str,
        weight_class: str,
        style: ArchetypeStyle,
    ) -> FighterBuild:
        """
        Generate an optimized fighter build for the given style and weight class.

        Allocates attributes, selects perks, and provides matchup notes.
        """
        win_rate = _STYLE_WIN_RATES.get((style, weight_class), 0.50)
        perks = self._top_perks_for_style(style, limit=5)
        attrs = _STYLE_ATTRIBUTES.get(style, {})
        skills = _SKILL_PRIORITY.get(style, [])

        style_path = FighterStylePath(
            style=style,
            weight_class=weight_class,
            win_rate=win_rate,
            recommended_perks=perks[:3],
            key_attributes=attrs,
            skill_priority=skills,
        )

        archetype = self._build_archetype(style)
        overall = self._calculate_overall(attrs)
        strengths, weaknesses = self._analyze_strengths_weaknesses(style)
        matchup_notes = self._build_matchup_notes(style)

        return FighterBuild(
            name=name,
            weight_class=weight_class,
            style_path=style_path,
            archetype=archetype,
            equipped_perks=perks[:5],
            attributes=attrs,
            overall_rating=overall,
            strengths=strengths,
            weaknesses=weaknesses,
            matchup_notes=matchup_notes,
        )

    def compare_builds(
        self,
        build_a: FighterBuild,
        build_b: FighterBuild,
    ) -> dict[str, Any]:
        """Compare two fighter builds head-to-head."""
        return {
            "build_a": build_a.name,
            "build_b": build_b.name,
            "win_rate_a": build_a.style_path.win_rate,
            "win_rate_b": build_b.style_path.win_rate,
            "overall_a": build_a.overall_rating,
            "overall_b": build_b.overall_rating,
            "advantage": (
                build_a.name
                if build_a.style_path.win_rate > build_b.style_path.win_rate
                else build_b.name
            ),
            "perk_synergy_a": len(build_a.equipped_perks),
            "perk_synergy_b": len(build_b.equipped_perks),
        }

    # --- private helpers ---

    def _top_perks_for_style(
        self, style: ArchetypeStyle, limit: int = 3
    ) -> list[PerkRanking]:
        all_perks = self.get_perk_rankings(style=style)
        return all_perks[:limit]

    def _build_archetype(self, style: ArchetypeStyle) -> FighterArchetype:
        defaults: dict[ArchetypeStyle, dict[str, Any]] = {
            ArchetypeStyle.PRESSURE: {
                "aggression_rating": 0.8, "takedown_threat": 0.3,
                "clinch_tendency": 0.4, "finish_rate": 0.35,
                "common_openers": [StrikeType.JAB, StrikeType.CROSS],
                "danger_strikes": [StrikeType.OVERHAND, StrikeType.UPPERCUT],
            },
            ArchetypeStyle.COUNTER: {
                "aggression_rating": 0.3, "takedown_threat": 0.1,
                "clinch_tendency": 0.1, "finish_rate": 0.30,
                "common_openers": [StrikeType.JAB],
                "danger_strikes": [StrikeType.HOOK, StrikeType.UPPERCUT],
            },
            ArchetypeStyle.WRESTLER: {
                "aggression_rating": 0.6, "takedown_threat": 0.7,
                "clinch_tendency": 0.5, "finish_rate": 0.30,
                "common_openers": [StrikeType.JAB, StrikeType.OVERHAND],
                "danger_strikes": [StrikeType.OVERHAND],
            },
            ArchetypeStyle.GRAPPLER: {
                "aggression_rating": 0.5, "takedown_threat": 0.6,
                "clinch_tendency": 0.6, "finish_rate": 0.40,
                "common_openers": [StrikeType.JAB],
                "danger_strikes": [StrikeType.KNEE],
            },
            ArchetypeStyle.KICKBOXER: {
                "aggression_rating": 0.5, "takedown_threat": 0.05,
                "clinch_tendency": 0.15, "finish_rate": 0.25,
                "common_openers": [StrikeType.LEG_KICK, StrikeType.JAB],
                "danger_strikes": [StrikeType.HEAD_KICK],
            },
            ArchetypeStyle.BRAWLER: {
                "aggression_rating": 0.9, "takedown_threat": 0.1,
                "clinch_tendency": 0.3, "finish_rate": 0.35,
                "common_openers": [StrikeType.OVERHAND],
                "danger_strikes": [StrikeType.OVERHAND, StrikeType.HOOK],
            },
            ArchetypeStyle.VOLUME: {
                "aggression_rating": 0.7, "takedown_threat": 0.1,
                "clinch_tendency": 0.2, "finish_rate": 0.20,
                "common_openers": [StrikeType.JAB, StrikeType.CROSS],
                "danger_strikes": [StrikeType.HOOK],
            },
            ArchetypeStyle.POINT_FIGHTER: {
                "aggression_rating": 0.3, "takedown_threat": 0.1,
                "clinch_tendency": 0.1, "finish_rate": 0.10,
                "common_openers": [StrikeType.JAB],
                "danger_strikes": [StrikeType.CROSS],
            },
            ArchetypeStyle.SWITCH_STANCE: {
                "aggression_rating": 0.5, "takedown_threat": 0.15,
                "clinch_tendency": 0.15, "finish_rate": 0.28,
                "common_openers": [StrikeType.JAB, StrikeType.LEG_KICK],
                "danger_strikes": [StrikeType.CROSS, StrikeType.HEAD_KICK],
            },
        }
        d = defaults.get(style, {
            "aggression_rating": 0.5, "takedown_threat": 0.2,
            "clinch_tendency": 0.2, "finish_rate": 0.25,
            "common_openers": [StrikeType.JAB],
            "danger_strikes": [StrikeType.CROSS],
        })
        return FighterArchetype(style=style, **d)

    def _calculate_overall(self, attrs: dict[str, int]) -> float:
        if not attrs:
            return 75.0
        return round(sum(attrs.values()) / len(attrs), 1)

    def _analyze_strengths_weaknesses(
        self, style: ArchetypeStyle
    ) -> tuple[list[str], list[str]]:
        strengths_map: dict[ArchetypeStyle, list[str]] = {
            ArchetypeStyle.PRESSURE: ["Relentless pace", "Cage cutting", "Volume damage"],
            ArchetypeStyle.COUNTER: ["KO power on counters", "Defense", "Fight IQ"],
            ArchetypeStyle.VOLUME: ["Cardio", "Point accumulation", "Late-round endurance"],
            ArchetypeStyle.WRESTLER: ["Takedowns", "Top control", "Cage wrestling"],
            ArchetypeStyle.GRAPPLER: ["Submissions", "Guard play", "Positional control"],
            ArchetypeStyle.KICKBOXER: ["Range control", "Kicks", "Damage output at distance"],
            ArchetypeStyle.BRAWLER: ["KO power", "Durability", "Exciting style"],
            ArchetypeStyle.POINT_FIGHTER: ["Defense", "Movement", "Cardio efficiency"],
            ArchetypeStyle.SWITCH_STANCE: ["Angles", "Unpredictability", "Technical striking"],
        }
        weaknesses_map: dict[ArchetypeStyle, list[str]] = {
            ArchetypeStyle.PRESSURE: ["Vulnerable to counters", "Stamina dependent"],
            ArchetypeStyle.COUNTER: ["Slow starters", "Struggle vs wrestlers"],
            ArchetypeStyle.VOLUME: ["Low single-shot power", "Predictable rhythm"],
            ArchetypeStyle.WRESTLER: ["Weak on feet", "Predictable entries"],
            ArchetypeStyle.GRAPPLER: ["Striking liability", "Takedown dependent"],
            ArchetypeStyle.KICKBOXER: ["Vulnerable to wrestlers", "Inside fighting weak"],
            ArchetypeStyle.BRAWLER: ["Defensively limited", "Gasses in later rounds"],
            ArchetypeStyle.POINT_FIGHTER: ["Low finish rate", "Boring under pressure"],
            ArchetypeStyle.SWITCH_STANCE: ["Jack of all trades", "Stamina cost of switching"],
        }
        return (
            strengths_map.get(style, ["Balanced"]),
            weaknesses_map.get(style, ["No clear weakness"]),
        )

    def _build_matchup_notes(self, style: ArchetypeStyle) -> dict[str, str]:
        notes: dict[str, str] = {}
        for opp in ArchetypeStyle:
            if opp == style:
                notes[opp.value] = "Mirror match — execution and conditioning decide"
            elif opp in (ArchetypeStyle.WRESTLER, ArchetypeStyle.GRAPPLER):
                notes[opp.value] = "Stay off the cage, defend takedowns early"
            elif opp == ArchetypeStyle.COUNTER:
                notes[opp.value] = "Feint more, don't lead with power"
            elif opp == ArchetypeStyle.PRESSURE:
                notes[opp.value] = "Use lateral movement, avoid backing straight up"
            else:
                notes[opp.value] = "Play to your strengths, adapt mid-fight"
        return notes
