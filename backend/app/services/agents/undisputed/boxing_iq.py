"""BoxingIQ — opponent archetype classification, southpaw/orthodox matchups, and gameplan.

Classifies opponent fighting styles into archetypes, calculates stance
matchup advantages, generates fight gameplans, and identifies patterns.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.undisputed.boxing import (
    ArchetypeClassification,
    BoxingArchetype,
    FightGameplan,
    StanceAdvantage,
    StanceMatchup,
    StanceType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Archetype definitions
# ---------------------------------------------------------------------------

_ARCHETYPES: dict[BoxingArchetype, dict[str, Any]] = {
    BoxingArchetype.SWARMER: {
        "description": "Relentless pressure fighter who closes distance and throws volume",
        "strengths": ["Pressure", "Volume", "Inside fighting", "Stamina"],
        "weaknesses": ["Counter punches", "Reach disadvantage", "Ring cutting defense"],
        "key_stats": {"punch_volume": 0.85, "pressure": 0.90, "inside_work": 0.80},
    },
    BoxingArchetype.OUT_BOXER: {
        "description": "Technical fighter who maintains distance and uses the jab",
        "strengths": ["Jab", "Footwork", "Distance management", "Ring generalship"],
        "weaknesses": ["Inside fighting", "Body work", "Aggressive pressure"],
        "key_stats": {"jab_usage": 0.85, "footwork": 0.90, "defense": 0.80},
    },
    BoxingArchetype.SLUGGER: {
        "description": "Power puncher who loads up on every shot looking for the KO",
        "strengths": ["Power", "KO ability", "Intimidation", "Single-shot damage"],
        "weaknesses": ["Speed", "Stamina", "Jab", "Volume"],
        "key_stats": {"power": 0.92, "ko_rate": 0.85, "chin": 0.75},
    },
    BoxingArchetype.COUNTER_PUNCHER: {
        "description": "Reactive fighter who waits for mistakes and punishes them",
        "strengths": ["Timing", "Counter accuracy", "Defense", "Ring IQ"],
        "weaknesses": ["Low output", "Judges favor aggression", "Needs opponent to lead"],
        "key_stats": {"counter_accuracy": 0.88, "defense": 0.85, "timing": 0.90},
    },
    BoxingArchetype.BOXER_PUNCHER: {
        "description": "Well-rounded fighter with technique and power in equal measure",
        "strengths": ["Versatility", "Combination punching", "Adaptability"],
        "weaknesses": ["Master of none", "Can be outclassed by specialists"],
        "key_stats": {"power": 0.78, "technique": 0.80, "versatility": 0.85},
    },
    BoxingArchetype.SWITCH_HITTER: {
        "description": "Fights from both stances to create angles and confuse opponents",
        "strengths": ["Angle creation", "Unpredictability", "Adaptability"],
        "weaknesses": ["Neither stance fully mastered", "Transition moments are vulnerable"],
        "key_stats": {"adaptability": 0.88, "angles": 0.85, "switch_frequency": 0.80},
    },
}

# Archetype matchup advantages (row beats column by this amount)
_MATCHUP_MATRIX: dict[BoxingArchetype, dict[BoxingArchetype, float]] = {
    BoxingArchetype.SWARMER: {
        BoxingArchetype.SWARMER: 0.0,
        BoxingArchetype.OUT_BOXER: 0.15,
        BoxingArchetype.SLUGGER: -0.10,
        BoxingArchetype.COUNTER_PUNCHER: 0.20,
        BoxingArchetype.BOXER_PUNCHER: 0.05,
        BoxingArchetype.SWITCH_HITTER: 0.0,
    },
    BoxingArchetype.OUT_BOXER: {
        BoxingArchetype.SWARMER: -0.15,
        BoxingArchetype.OUT_BOXER: 0.0,
        BoxingArchetype.SLUGGER: 0.25,
        BoxingArchetype.COUNTER_PUNCHER: -0.10,
        BoxingArchetype.BOXER_PUNCHER: 0.05,
        BoxingArchetype.SWITCH_HITTER: -0.05,
    },
    BoxingArchetype.SLUGGER: {
        BoxingArchetype.SWARMER: 0.10,
        BoxingArchetype.OUT_BOXER: -0.25,
        BoxingArchetype.SLUGGER: 0.0,
        BoxingArchetype.COUNTER_PUNCHER: -0.20,
        BoxingArchetype.BOXER_PUNCHER: 0.05,
        BoxingArchetype.SWITCH_HITTER: 0.0,
    },
    BoxingArchetype.COUNTER_PUNCHER: {
        BoxingArchetype.SWARMER: -0.20,
        BoxingArchetype.OUT_BOXER: 0.10,
        BoxingArchetype.SLUGGER: 0.20,
        BoxingArchetype.COUNTER_PUNCHER: 0.0,
        BoxingArchetype.BOXER_PUNCHER: 0.05,
        BoxingArchetype.SWITCH_HITTER: -0.05,
    },
    BoxingArchetype.BOXER_PUNCHER: {
        BoxingArchetype.SWARMER: -0.05,
        BoxingArchetype.OUT_BOXER: -0.05,
        BoxingArchetype.SLUGGER: -0.05,
        BoxingArchetype.COUNTER_PUNCHER: -0.05,
        BoxingArchetype.BOXER_PUNCHER: 0.0,
        BoxingArchetype.SWITCH_HITTER: 0.0,
    },
    BoxingArchetype.SWITCH_HITTER: {
        BoxingArchetype.SWARMER: 0.0,
        BoxingArchetype.OUT_BOXER: 0.05,
        BoxingArchetype.SLUGGER: 0.0,
        BoxingArchetype.COUNTER_PUNCHER: 0.05,
        BoxingArchetype.BOXER_PUNCHER: 0.0,
        BoxingArchetype.SWITCH_HITTER: 0.0,
    },
}

# Stance matchup advantages
_STANCE_ADVANTAGES: dict[tuple[StanceType, StanceType], StanceAdvantage] = {
    (StanceType.ORTHODOX, StanceType.ORTHODOX): StanceAdvantage(
        advantage=0.0, lead_hand="standard", power_hand="standard",
        notes="Mirror match — focus on fundamentals and ring craft.",
    ),
    (StanceType.ORTHODOX, StanceType.SOUTHPAW): StanceAdvantage(
        advantage=-0.05, lead_hand="contested", power_hand="open_angle",
        notes="Southpaw advantage in lead hand battles. Keep right foot outside their left.",
    ),
    (StanceType.SOUTHPAW, StanceType.ORTHODOX): StanceAdvantage(
        advantage=0.05, lead_hand="contested", power_hand="open_angle",
        notes="Natural advantage — left hand finds the chin easily. Control the foot position.",
    ),
    (StanceType.SOUTHPAW, StanceType.SOUTHPAW): StanceAdvantage(
        advantage=0.0, lead_hand="standard", power_hand="standard",
        notes="Southpaw mirror — rare matchup. Use angles and feints.",
    ),
}


class BoxingIQ:
    """Undisputed opponent archetype engine and matchup analyzer.

    Classifies fighters into archetypes, calculates stance advantages,
    generates fight gameplans, and identifies exploit patterns.
    """

    # ------------------------------------------------------------------
    # Opponent archetype classification
    # ------------------------------------------------------------------

    def classify_archetype(
        self,
        fight_stats: dict[str, Any],
    ) -> ArchetypeClassification:
        """Classify a fighter into an archetype based on fight statistics.

        Expected stats: punch_volume, jab_usage, power_shots_pct, counter_pct,
        pressure_rating, defense_rating, footwork_rating, ko_rate.
        """
        scores: dict[BoxingArchetype, float] = {}

        for archetype, data in _ARCHETYPES.items():
            score = 0.0
            key_stats = data["key_stats"]
            for stat_name, weight in key_stats.items():
                stat_val = fight_stats.get(stat_name, 0.5)
                score += stat_val * weight
            scores[archetype] = round(score / len(key_stats), 3)

        # Special rules
        if fight_stats.get("switch_frequency", 0) > 0.3:
            scores[BoxingArchetype.SWITCH_HITTER] *= 1.4
        if fight_stats.get("ko_rate", 0) > 0.7:
            scores[BoxingArchetype.SLUGGER] *= 1.3
        if fight_stats.get("jab_usage", 0) > 0.4 and fight_stats.get("footwork", 0) > 0.7:
            scores[BoxingArchetype.OUT_BOXER] *= 1.2

        primary = max(scores, key=scores.get)  # type: ignore[arg-type]
        secondary_candidates = sorted(
            [(a, s) for a, s in scores.items() if a != primary],
            key=lambda x: x[1], reverse=True,
        )
        secondary = secondary_candidates[0][0] if secondary_candidates else None

        archetype_data = _ARCHETYPES[primary]

        return ArchetypeClassification(
            primary_archetype=primary,
            secondary_archetype=secondary,
            confidence=round(scores[primary], 3),
            archetype_scores=scores,
            strengths=archetype_data["strengths"],
            weaknesses=archetype_data["weaknesses"],
            description=archetype_data["description"],
        )

    # ------------------------------------------------------------------
    # Stance matchup
    # ------------------------------------------------------------------

    def analyze_stance_matchup(
        self,
        player_stance: StanceType,
        opponent_stance: StanceType,
    ) -> StanceMatchup:
        """Analyze the stance matchup between two fighters.

        Returns foot positioning advice, lead hand strategy, and power hand angles.
        """
        advantage = _STANCE_ADVANTAGES.get(
            (player_stance, opponent_stance),
            StanceAdvantage(advantage=0.0, lead_hand="standard", power_hand="standard", notes="Unknown matchup"),
        )

        tips: list[str] = []
        if player_stance == StanceType.ORTHODOX and opponent_stance == StanceType.SOUTHPAW:
            tips.append("Keep your right foot outside their left foot for angle advantage.")
            tips.append("Double jab to set up the right hand — southpaws leave the chin exposed.")
            tips.append("Circle to your left to avoid their power hand.")
        elif player_stance == StanceType.SOUTHPAW and opponent_stance == StanceType.ORTHODOX:
            tips.append("Your left straight is your best weapon — the angle is open.")
            tips.append("Jab to the body to draw their guard down, then go upstairs.")
            tips.append("Circle to your right — stay away from their right hand.")
        else:
            tips.append("Standard matchup — fundamentals win. Jab, move, combo.")
            tips.append("Look for rhythm patterns to time your counter punches.")

        return StanceMatchup(
            player_stance=player_stance,
            opponent_stance=opponent_stance,
            advantage=advantage,
            tips=tips,
        )

    # ------------------------------------------------------------------
    # Fight gameplan
    # ------------------------------------------------------------------

    def generate_gameplan(
        self,
        player_archetype: BoxingArchetype,
        opponent_archetype: BoxingArchetype,
        player_stance: StanceType = StanceType.ORTHODOX,
        opponent_stance: StanceType = StanceType.ORTHODOX,
        fight_rounds: int = 12,
    ) -> FightGameplan:
        """Generate a comprehensive fight gameplan based on archetype and stance matchups."""
        matchup_edge = _MATCHUP_MATRIX.get(player_archetype, {}).get(opponent_archetype, 0.0)
        stance_data = _STANCE_ADVANTAGES.get((player_stance, opponent_stance))
        stance_edge = stance_data.advantage if stance_data else 0.0

        total_edge = matchup_edge + stance_edge

        opp_data = _ARCHETYPES[opponent_archetype]
        player_data = _ARCHETYPES[player_archetype]

        # Build round-by-round strategy
        early_rounds = "Establish the jab. Find your range and timing. Study their patterns."
        mid_rounds = "Increase output. Target identified weaknesses."
        late_rounds = "Push the pace if ahead. Protect the lead. Go for the finish if behind."

        if player_archetype == BoxingArchetype.SWARMER:
            early_rounds = "Close distance immediately. Establish pressure from round 1."
            mid_rounds = "Maintain constant pressure. Body work to drain stamina."
            late_rounds = "Overwhelm with volume. They should be fading by now."
        elif player_archetype == BoxingArchetype.COUNTER_PUNCHER:
            early_rounds = "Be patient. Let them come to you. Establish the counter rhythm."
            mid_rounds = "They should be frustrated. Time the counter right hand."
            late_rounds = "Pick your shots. Bank rounds on defense and counters."

        exploit_targets = opp_data["weaknesses"][:3]
        avoid_areas = opp_data["strengths"][:2]

        win_probability = 0.5 + total_edge
        win_probability = max(0.15, min(0.85, win_probability))

        return FightGameplan(
            player_archetype=player_archetype,
            opponent_archetype=opponent_archetype,
            matchup_edge=round(total_edge, 3),
            win_probability=round(win_probability, 3),
            early_rounds=early_rounds,
            mid_rounds=mid_rounds,
            late_rounds=late_rounds,
            exploit_targets=exploit_targets,
            avoid_areas=avoid_areas,
            key_weapon=player_data["strengths"][0],
            fight_rounds=fight_rounds,
        )

    # ------------------------------------------------------------------
    # Pattern identification
    # ------------------------------------------------------------------

    def identify_patterns(
        self,
        round_data: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Identify opponent patterns from round-by-round data.

        Expected keys per round: round_num, lead_jab_pct, power_pct,
        body_pct, movement_direction, pressure_level.
        """
        patterns: list[dict[str, Any]] = []

        if len(round_data) < 2:
            return [{"pattern": "Need more rounds to identify patterns."}]

        # Check for consistent body work
        body_rounds = [r for r in round_data if r.get("body_pct", 0) > 0.3]
        if len(body_rounds) >= 2:
            patterns.append({
                "pattern": "Body focus",
                "description": "Opponent invests in body work consistently — protect the midsection.",
                "counter": "Parry body shots and counter with hooks to the head.",
                "confidence": round(len(body_rounds) / len(round_data), 2),
            })

        # Check for lead hand dependence
        jab_heavy = [r for r in round_data if r.get("lead_jab_pct", 0) > 0.5]
        if len(jab_heavy) >= 2:
            patterns.append({
                "pattern": "Jab dependent",
                "description": "Opponent leads with the jab excessively — time the counter.",
                "counter": "Slip outside the jab and counter with the rear hand.",
                "confidence": round(len(jab_heavy) / len(round_data), 2),
            })

        # Pressure escalation
        if len(round_data) >= 3:
            pressures = [r.get("pressure_level", 0.5) for r in round_data]
            if pressures[-1] > pressures[0] + 0.2:
                patterns.append({
                    "pattern": "Increasing pressure",
                    "description": "Opponent escalates pressure as the fight progresses.",
                    "counter": "Maintain distance with the jab. Clinch to break momentum.",
                    "confidence": 0.70,
                })

        if not patterns:
            patterns.append({
                "pattern": "No clear pattern",
                "description": "Opponent is varying approach — stay adaptable.",
                "counter": "Stick to your gameplan and force them to adjust.",
                "confidence": 0.40,
            })

        return patterns


# Module-level singleton
boxing_iq = BoxingIQ()
