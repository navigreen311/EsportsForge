"""FightIQ — opponent archetype engine, style matchup cards, finish pattern analysis.

Classifies opponents into archetypes, generates matchup advantage cards,
and identifies the most likely finish patterns for each style.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.ufc5.combat import (
    ArchetypeStyle,
    FighterArchetype,
    FinishPattern,
    StrikeType,
    StyleMatchup,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — matchup matrix (row = player, col = opponent)
# Positive = player advantage, negative = opponent advantage
# ---------------------------------------------------------------------------

_MATCHUP_MATRIX: dict[ArchetypeStyle, dict[ArchetypeStyle, float]] = {
    ArchetypeStyle.PRESSURE: {
        ArchetypeStyle.PRESSURE: 0.0,
        ArchetypeStyle.COUNTER: -0.3,
        ArchetypeStyle.VOLUME: 0.1,
        ArchetypeStyle.WRESTLER: -0.1,
        ArchetypeStyle.GRAPPLER: -0.2,
        ArchetypeStyle.KICKBOXER: 0.2,
        ArchetypeStyle.BRAWLER: 0.1,
        ArchetypeStyle.POINT_FIGHTER: 0.3,
        ArchetypeStyle.SWITCH_STANCE: 0.0,
    },
    ArchetypeStyle.COUNTER: {
        ArchetypeStyle.PRESSURE: 0.3,
        ArchetypeStyle.COUNTER: 0.0,
        ArchetypeStyle.VOLUME: -0.2,
        ArchetypeStyle.WRESTLER: -0.2,
        ArchetypeStyle.GRAPPLER: -0.3,
        ArchetypeStyle.KICKBOXER: 0.1,
        ArchetypeStyle.BRAWLER: 0.4,
        ArchetypeStyle.POINT_FIGHTER: -0.1,
        ArchetypeStyle.SWITCH_STANCE: 0.0,
    },
    ArchetypeStyle.VOLUME: {
        ArchetypeStyle.PRESSURE: -0.1,
        ArchetypeStyle.COUNTER: 0.2,
        ArchetypeStyle.VOLUME: 0.0,
        ArchetypeStyle.WRESTLER: -0.2,
        ArchetypeStyle.GRAPPLER: -0.1,
        ArchetypeStyle.KICKBOXER: 0.0,
        ArchetypeStyle.BRAWLER: 0.2,
        ArchetypeStyle.POINT_FIGHTER: 0.1,
        ArchetypeStyle.SWITCH_STANCE: 0.0,
    },
    ArchetypeStyle.WRESTLER: {
        ArchetypeStyle.PRESSURE: 0.1,
        ArchetypeStyle.COUNTER: 0.2,
        ArchetypeStyle.VOLUME: 0.2,
        ArchetypeStyle.WRESTLER: 0.0,
        ArchetypeStyle.GRAPPLER: -0.1,
        ArchetypeStyle.KICKBOXER: 0.3,
        ArchetypeStyle.BRAWLER: 0.2,
        ArchetypeStyle.POINT_FIGHTER: 0.1,
        ArchetypeStyle.SWITCH_STANCE: 0.1,
    },
    ArchetypeStyle.GRAPPLER: {
        ArchetypeStyle.PRESSURE: 0.2,
        ArchetypeStyle.COUNTER: 0.3,
        ArchetypeStyle.VOLUME: 0.1,
        ArchetypeStyle.WRESTLER: 0.1,
        ArchetypeStyle.GRAPPLER: 0.0,
        ArchetypeStyle.KICKBOXER: 0.3,
        ArchetypeStyle.BRAWLER: 0.2,
        ArchetypeStyle.POINT_FIGHTER: 0.2,
        ArchetypeStyle.SWITCH_STANCE: 0.1,
    },
    ArchetypeStyle.KICKBOXER: {
        ArchetypeStyle.PRESSURE: -0.2,
        ArchetypeStyle.COUNTER: -0.1,
        ArchetypeStyle.VOLUME: 0.0,
        ArchetypeStyle.WRESTLER: -0.3,
        ArchetypeStyle.GRAPPLER: -0.3,
        ArchetypeStyle.KICKBOXER: 0.0,
        ArchetypeStyle.BRAWLER: 0.3,
        ArchetypeStyle.POINT_FIGHTER: 0.2,
        ArchetypeStyle.SWITCH_STANCE: 0.0,
    },
    ArchetypeStyle.BRAWLER: {
        ArchetypeStyle.PRESSURE: -0.1,
        ArchetypeStyle.COUNTER: -0.4,
        ArchetypeStyle.VOLUME: -0.2,
        ArchetypeStyle.WRESTLER: -0.2,
        ArchetypeStyle.GRAPPLER: -0.2,
        ArchetypeStyle.KICKBOXER: -0.3,
        ArchetypeStyle.BRAWLER: 0.0,
        ArchetypeStyle.POINT_FIGHTER: 0.1,
        ArchetypeStyle.SWITCH_STANCE: -0.1,
    },
    ArchetypeStyle.POINT_FIGHTER: {
        ArchetypeStyle.PRESSURE: -0.3,
        ArchetypeStyle.COUNTER: 0.1,
        ArchetypeStyle.VOLUME: -0.1,
        ArchetypeStyle.WRESTLER: -0.1,
        ArchetypeStyle.GRAPPLER: -0.2,
        ArchetypeStyle.KICKBOXER: -0.2,
        ArchetypeStyle.BRAWLER: -0.1,
        ArchetypeStyle.POINT_FIGHTER: 0.0,
        ArchetypeStyle.SWITCH_STANCE: -0.1,
    },
    ArchetypeStyle.SWITCH_STANCE: {
        ArchetypeStyle.PRESSURE: 0.0,
        ArchetypeStyle.COUNTER: 0.0,
        ArchetypeStyle.VOLUME: 0.0,
        ArchetypeStyle.WRESTLER: -0.1,
        ArchetypeStyle.GRAPPLER: -0.1,
        ArchetypeStyle.KICKBOXER: 0.0,
        ArchetypeStyle.BRAWLER: 0.1,
        ArchetypeStyle.POINT_FIGHTER: 0.1,
        ArchetypeStyle.SWITCH_STANCE: 0.0,
    },
}

_ARCHETYPE_STRATEGIES: dict[tuple[ArchetypeStyle, ArchetypeStyle], list[str]] = {
    (ArchetypeStyle.PRESSURE, ArchetypeStyle.COUNTER): [
        "Feint heavy to bait counter, then level-change",
        "Use body work to reduce counter timing",
        "Close distance with jab-cross, not lunging strikes",
    ],
    (ArchetypeStyle.COUNTER, ArchetypeStyle.PRESSURE): [
        "Keep range with teep/front kick",
        "Time the check hook on their entries",
        "Circle away from power hand",
    ],
    (ArchetypeStyle.WRESTLER, ArchetypeStyle.KICKBOXER): [
        "Use feinted strikes to set up takedowns",
        "Pressure against cage for wrestling exchanges",
        "Avoid standing in kicking range",
    ],
    (ArchetypeStyle.KICKBOXER, ArchetypeStyle.WRESTLER): [
        "Maintain distance with leg kicks",
        "Sprawl early and punish failed shots",
        "Use lateral movement to avoid cage pressure",
    ],
}

_FINISH_PATTERNS: dict[ArchetypeStyle, FinishPattern] = {
    ArchetypeStyle.PRESSURE: FinishPattern(
        archetype=ArchetypeStyle.PRESSURE,
        primary_finish="TKO (cage pressure ground and pound)",
        setup_sequence=[
            "Sustained pressure to drain stamina",
            "Body work to lower guard",
            "Overhand or uppercut to hurt",
            "Swarm with hooks against cage",
        ],
        round_tendency=3,
        success_rate=0.35,
    ),
    ArchetypeStyle.COUNTER: FinishPattern(
        archetype=ArchetypeStyle.COUNTER,
        primary_finish="KO (counter hook/uppercut)",
        setup_sequence=[
            "Patient range management",
            "Bait opponent into overcommitting",
            "Time check hook or counter uppercut",
            "Follow up with ground finish if rocked",
        ],
        round_tendency=2,
        success_rate=0.30,
    ),
    ArchetypeStyle.GRAPPLER: FinishPattern(
        archetype=ArchetypeStyle.GRAPPLER,
        primary_finish="Submission (rear naked choke)",
        setup_sequence=[
            "Secure takedown to guard",
            "Pass to side control or mount",
            "Take the back on scramble",
            "Lock in rear naked choke",
        ],
        round_tendency=2,
        success_rate=0.40,
    ),
    ArchetypeStyle.WRESTLER: FinishPattern(
        archetype=ArchetypeStyle.WRESTLER,
        primary_finish="TKO (ground and pound from mount)",
        setup_sequence=[
            "Chain wrestling to secure top position",
            "Advance to mount or half guard",
            "Ground and pound to force shell-up",
            "Referee stoppage via unanswered strikes",
        ],
        round_tendency=3,
        success_rate=0.30,
    ),
    ArchetypeStyle.KICKBOXER: FinishPattern(
        archetype=ArchetypeStyle.KICKBOXER,
        primary_finish="KO (head kick)",
        setup_sequence=[
            "Establish leg kicks to lower guard",
            "Mix in body kicks to condition",
            "Set up high kick behind jab-cross",
            "Follow up on stun with combinations",
        ],
        round_tendency=2,
        success_rate=0.25,
    ),
    ArchetypeStyle.BRAWLER: FinishPattern(
        archetype=ArchetypeStyle.BRAWLER,
        primary_finish="KO (overhand/hook)",
        setup_sequence=[
            "Walk forward and absorb to land",
            "Throw power overhand on entry",
            "Swarm with hooks on hurt opponent",
        ],
        round_tendency=1,
        success_rate=0.35,
    ),
    ArchetypeStyle.VOLUME: FinishPattern(
        archetype=ArchetypeStyle.VOLUME,
        primary_finish="TKO (accumulation stoppage)",
        setup_sequence=[
            "High output combinations",
            "Target cut-prone areas repeatedly",
            "Sustained pace to accumulate damage",
            "Late-round stoppage from accumulation",
        ],
        round_tendency=4,
        success_rate=0.20,
    ),
    ArchetypeStyle.POINT_FIGHTER: FinishPattern(
        archetype=ArchetypeStyle.POINT_FIGHTER,
        primary_finish="Decision (unanimous)",
        setup_sequence=[
            "Out-point with jab and movement",
            "Win rounds on volume and control",
            "Avoid exchanges, stick and move",
        ],
        round_tendency=5,
        success_rate=0.10,
    ),
    ArchetypeStyle.SWITCH_STANCE: FinishPattern(
        archetype=ArchetypeStyle.SWITCH_STANCE,
        primary_finish="KO (angle-created power shot)",
        setup_sequence=[
            "Switch stances to create angles",
            "Disguise power shots from southpaw",
            "Exploit opponent's slow adjustment",
            "Land cross from switch as finisher",
        ],
        round_tendency=2,
        success_rate=0.28,
    ),
}

# Default archetype templates for common opponent reads
_DEFAULT_ARCHETYPES: dict[str, FighterArchetype] = {
    "pressure": FighterArchetype(
        style=ArchetypeStyle.PRESSURE,
        aggression_rating=0.8,
        takedown_threat=0.3,
        clinch_tendency=0.4,
        finish_rate=0.35,
        common_openers=[StrikeType.JAB, StrikeType.CROSS, StrikeType.BODY_HOOK],
        danger_strikes=[StrikeType.OVERHAND, StrikeType.UPPERCUT],
    ),
    "counter": FighterArchetype(
        style=ArchetypeStyle.COUNTER,
        aggression_rating=0.3,
        takedown_threat=0.1,
        clinch_tendency=0.1,
        finish_rate=0.30,
        common_openers=[StrikeType.JAB, StrikeType.LEG_KICK],
        danger_strikes=[StrikeType.HOOK, StrikeType.UPPERCUT, StrikeType.HEAD_KICK],
    ),
    "wrestler": FighterArchetype(
        style=ArchetypeStyle.WRESTLER,
        aggression_rating=0.6,
        takedown_threat=0.7,
        clinch_tendency=0.5,
        finish_rate=0.30,
        common_openers=[StrikeType.JAB, StrikeType.OVERHAND],
        danger_strikes=[StrikeType.OVERHAND, StrikeType.ELBOW],
    ),
    "grappler": FighterArchetype(
        style=ArchetypeStyle.GRAPPLER,
        aggression_rating=0.5,
        takedown_threat=0.6,
        clinch_tendency=0.6,
        finish_rate=0.40,
        common_openers=[StrikeType.JAB, StrikeType.FRONT_KICK],
        danger_strikes=[StrikeType.KNEE, StrikeType.ELBOW],
    ),
    "kickboxer": FighterArchetype(
        style=ArchetypeStyle.KICKBOXER,
        aggression_rating=0.5,
        takedown_threat=0.05,
        clinch_tendency=0.15,
        finish_rate=0.25,
        common_openers=[StrikeType.LEG_KICK, StrikeType.JAB, StrikeType.BODY_KICK],
        danger_strikes=[StrikeType.HEAD_KICK, StrikeType.SPINNING_BACK_KICK],
    ),
    "brawler": FighterArchetype(
        style=ArchetypeStyle.BRAWLER,
        aggression_rating=0.9,
        takedown_threat=0.1,
        clinch_tendency=0.3,
        finish_rate=0.35,
        common_openers=[StrikeType.OVERHAND, StrikeType.HOOK],
        danger_strikes=[StrikeType.OVERHAND, StrikeType.HOOK, StrikeType.UPPERCUT],
    ),
}


class FightIQ:
    """Opponent archetype engine — classifies styles, generates matchup cards, analyzes finish patterns."""

    def list_archetypes(self) -> list[dict[str, str]]:
        """Return all recognized fighter archetypes with descriptions."""
        descriptions = {
            ArchetypeStyle.PRESSURE: "Relentless forward pressure, cage cutting, cardio-dependent",
            ArchetypeStyle.COUNTER: "Patient, reactive, high fight IQ, devastating counters",
            ArchetypeStyle.VOLUME: "High output, point accumulation, cardio monster",
            ArchetypeStyle.WRESTLER: "Takedown-centric, top control, ground and pound",
            ArchetypeStyle.GRAPPLER: "Submission specialist, guard player, positional chess",
            ArchetypeStyle.KICKBOXER: "Range management, kick-heavy, technical striking",
            ArchetypeStyle.BRAWLER: "Power-first, wild exchanges, chin-dependent",
            ArchetypeStyle.POINT_FIGHTER: "Out-scoring, movement-heavy, low damage output",
            ArchetypeStyle.SWITCH_STANCE: "Stance switches for angles, unpredictable, technical",
        }
        return [
            {"name": s.value, "description": descriptions.get(s, "")}
            for s in ArchetypeStyle
        ]

    def classify_opponent(self, tendencies: dict[str, Any]) -> FighterArchetype:
        """
        Classify an opponent into an archetype based on observed tendencies.

        Args:
            tendencies: Dict with keys like aggression, takedown_rate, clinch_rate,
                        striking_volume, movement_style, etc.
        """
        aggression = tendencies.get("aggression", 0.5)
        td_rate = tendencies.get("takedown_rate", 0.1)
        clinch_rate = tendencies.get("clinch_rate", 0.1)
        volume = tendencies.get("striking_volume", 0.5)
        power = tendencies.get("power_ratio", 0.5)

        # Classification logic based on dominant tendency
        if td_rate > 0.5:
            style = ArchetypeStyle.WRESTLER
        elif clinch_rate > 0.5 and td_rate > 0.3:
            style = ArchetypeStyle.GRAPPLER
        elif aggression > 0.7 and power > 0.6:
            style = ArchetypeStyle.BRAWLER
        elif aggression > 0.6:
            style = ArchetypeStyle.PRESSURE
        elif aggression < 0.3 and volume < 0.4:
            style = ArchetypeStyle.COUNTER
        elif volume > 0.7:
            style = ArchetypeStyle.VOLUME
        elif aggression < 0.4 and volume > 0.3:
            style = ArchetypeStyle.POINT_FIGHTER
        else:
            style = ArchetypeStyle.KICKBOXER

        template = _DEFAULT_ARCHETYPES.get(style.value)
        if template:
            return template.model_copy(
                update={"aggression_rating": aggression, "takedown_threat": td_rate}
            )

        return FighterArchetype(
            style=style,
            aggression_rating=aggression,
            takedown_threat=td_rate,
            clinch_tendency=clinch_rate,
            finish_rate=power * 0.5,
            common_openers=[StrikeType.JAB],
            danger_strikes=[StrikeType.CROSS],
        )

    def get_matchup_card(
        self,
        player_style: ArchetypeStyle,
        opponent_style: ArchetypeStyle,
    ) -> StyleMatchup:
        """Generate a matchup advantage card between two styles."""
        advantage = _MATCHUP_MATRIX.get(player_style, {}).get(opponent_style, 0.0)

        strategies = _ARCHETYPE_STRATEGIES.get(
            (player_style, opponent_style), []
        )
        if not strategies:
            strategies = self._generate_default_strategies(player_style, opponent_style)

        avoid = self._get_avoid_patterns(player_style, opponent_style)
        windows = self._get_finish_windows(player_style, opponent_style)

        return StyleMatchup(
            player_style=player_style,
            opponent_style=opponent_style,
            advantage=advantage,
            key_strategies=strategies,
            avoid_patterns=avoid,
            finish_windows=windows,
        )

    def get_finish_pattern(self, archetype: ArchetypeStyle) -> FinishPattern:
        """Return the typical finish pattern for a given archetype."""
        pattern = _FINISH_PATTERNS.get(archetype)
        if not pattern:
            return FinishPattern(
                archetype=archetype,
                primary_finish="Decision",
                setup_sequence=["Outwork opponent over 3/5 rounds"],
                round_tendency=5,
                success_rate=0.15,
            )
        return pattern

    def analyze_all_matchups(
        self, player_style: ArchetypeStyle
    ) -> list[StyleMatchup]:
        """Generate matchup cards against every archetype."""
        return [
            self.get_matchup_card(player_style, opp)
            for opp in ArchetypeStyle
        ]

    # --- private helpers ---

    def _generate_default_strategies(
        self,
        player: ArchetypeStyle,
        opponent: ArchetypeStyle,
    ) -> list[str]:
        """Fallback strategy generation."""
        advantage = _MATCHUP_MATRIX.get(player, {}).get(opponent, 0.0)
        if advantage > 0.1:
            return [
                f"Play to your {player.value} strengths",
                f"Exploit {opponent.value} weaknesses at range",
                "Maintain your preferred distance",
            ]
        elif advantage < -0.1:
            return [
                f"Neutralize {opponent.value} gameplan with movement",
                "Force the fight to uncomfortable positions",
                "Be patient and pick your spots",
            ]
        return [
            "Even matchup — conditioning and execution decide",
            "Focus on winning the first exchange cleanly",
            "Adapt based on opponent tendencies mid-fight",
        ]

    def _get_avoid_patterns(
        self,
        player: ArchetypeStyle,
        opponent: ArchetypeStyle,
    ) -> list[str]:
        """Common mistakes to avoid in a matchup."""
        avoid: list[str] = []
        if opponent == ArchetypeStyle.COUNTER:
            avoid.append("Don't lead with power shots — you'll eat counters")
            avoid.append("Avoid lunging entries without feints")
        if opponent == ArchetypeStyle.WRESTLER:
            avoid.append("Don't back straight to the cage")
            avoid.append("Avoid throwing naked kicks without setup")
        if opponent == ArchetypeStyle.BRAWLER:
            avoid.append("Don't trade in the pocket")
            avoid.append("Avoid ego-fighting — stick to the plan")
        if opponent == ArchetypeStyle.GRAPPLER:
            avoid.append("Don't clinch unnecessarily")
            avoid.append("Avoid going to the ground without advantage")
        if not avoid:
            avoid = [
                "Avoid falling into a predictable rhythm",
                "Don't over-commit on single strikes",
            ]
        return avoid

    def _get_finish_windows(
        self,
        player: ArchetypeStyle,
        opponent: ArchetypeStyle,
    ) -> list[str]:
        """Identify the best moments to pursue a finish."""
        windows: list[str] = []
        if player in (ArchetypeStyle.PRESSURE, ArchetypeStyle.BRAWLER):
            windows.append("When opponent is against the cage with low stamina")
        if player in (ArchetypeStyle.COUNTER, ArchetypeStyle.KICKBOXER):
            windows.append("After a clean counter lands and opponent is rocked")
        if player in (ArchetypeStyle.WRESTLER, ArchetypeStyle.GRAPPLER):
            windows.append("After a successful takedown with opponent gassed")
        if opponent == ArchetypeStyle.BRAWLER:
            windows.append("Late rounds when their chin is compromised")
        if not windows:
            windows = ["When opponent is visibly hurt or stunned"]
        return windows
