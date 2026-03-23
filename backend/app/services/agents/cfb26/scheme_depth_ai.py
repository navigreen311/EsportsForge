"""SchemeDepthAI — triple option, Air Raid, spread RPO, flexbone, West Coast mastery.

Analyzes playbook depth, tracks scheme mastery progression, provides option read
breakdowns, and generates counter-strategies against opponent schemes.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from app.schemas.cfb26.scheme import (
    ConceptMastery,
    CounterScheme,
    FormationAnalysis,
    MasteryLevel,
    MasteryTier,
    OptionRead,
    OptionReadProgression,
    PlaybookAnalysis,
    PlayType,
    SchemeProgression,
    SchemeType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scheme concept definitions
# ---------------------------------------------------------------------------

SCHEME_CONCEPTS: dict[SchemeType, list[str]] = {
    SchemeType.TRIPLE_OPTION: [
        "dive_read", "pitch_read", "qb_keep_lane", "fullback_alignment",
        "option_pitch_timing", "lead_blocker_assignment", "audible_recognition",
    ],
    SchemeType.AIR_RAID: [
        "mesh_concept", "y_cross", "four_verticals", "spacing",
        "screen_game", "hot_routes", "protection_slides",
    ],
    SchemeType.SPREAD_RPO: [
        "zone_read_give_pull", "bubble_screen_tag", "glance_rpo",
        "pre_snap_conflict_key", "tempo_management", "formation_shifts",
    ],
    SchemeType.FLEXBONE: [
        "triple_option_mesh", "midline_option", "rocket_toss",
        "counter_option", "play_action_boot", "speed_option",
    ],
    SchemeType.WEST_COAST: [
        "short_passing_timing", "yards_after_catch", "play_action_rollout",
        "check_down_progression", "route_combination_timing", "hot_routes",
    ],
    SchemeType.PRO_STYLE: [
        "under_center_play_action", "bootleg", "power_run",
        "screen_game", "audible_system", "red_zone_concepts",
    ],
    SchemeType.POWER_RUN: [
        "power_blocking", "counter_trey", "iso_lead", "sweep",
        "goal_line_package", "play_action_shot",
    ],
    SchemeType.PISTOL: [
        "zone_read", "draw_plays", "power_read", "sprint_out",
        "packaged_plays", "misdirection",
    ],
}

MASTERY_THRESHOLDS: dict[MasteryTier, float] = {
    MasteryTier.NOVICE: 0.0,
    MasteryTier.INTERMEDIATE: 0.20,
    MasteryTier.ADVANCED: 0.45,
    MasteryTier.EXPERT: 0.70,
    MasteryTier.MASTER: 0.90,
}

# ---------------------------------------------------------------------------
# Option read progressions database
# ---------------------------------------------------------------------------

OPTION_READS: dict[PlayType, list[OptionRead]] = {
    PlayType.TRIPLE_OPTION: [
        OptionRead(
            read_number=1,
            defender_key="DE",
            give_trigger="DE crashes down on dive back",
            pull_trigger="DE stays home or widens",
            tip="Watch the DE's first step — inside step = give, outside step = pull.",
        ),
        OptionRead(
            read_number=2,
            defender_key="OLB/pitch_key",
            give_trigger="N/A (QB already has ball)",
            pull_trigger="Pitch key attacks QB",
            tip="After pulling, immediately find the pitch key. If he commits to you, pitch it.",
        ),
    ],
    PlayType.ZONE_READ: [
        OptionRead(
            read_number=1,
            defender_key="backside DE",
            give_trigger="DE squeezes or follows RB into the hole",
            pull_trigger="DE stays outside or crashes hard",
            tip="Leave the backside DE unblocked — he IS the read.",
        ),
    ],
    PlayType.SPEED_OPTION: [
        OptionRead(
            read_number=1,
            defender_key="EMOL (end man on line)",
            give_trigger="N/A (no dive)",
            pull_trigger="EMOL attacks QB — pitch immediately",
            tip="Get to the edge fast. Read on the run, don't slow down to read.",
        ),
    ],
    PlayType.RPO_BUBBLE: [
        OptionRead(
            read_number=1,
            defender_key="slot defender / OLB",
            give_trigger="Defender widens to cover bubble screen",
            pull_trigger="Defender stays in the box — throw the bubble",
            tip="Pre-snap: count the box. Post-snap: confirm with the slot defender's movement.",
        ),
    ],
    PlayType.RPO_SLANT: [
        OptionRead(
            read_number=1,
            defender_key="Mike LB or conflict defender",
            give_trigger="LB drops into passing lane or stays shallow",
            pull_trigger="LB bites on run action — throw the slant behind him",
            tip="The slant must be thrown in rhythm — if you wait, the window closes.",
        ),
    ],
}

# ---------------------------------------------------------------------------
# Counter scheme database
# ---------------------------------------------------------------------------

COUNTER_SCHEMES: dict[SchemeType, CounterScheme] = {
    SchemeType.TRIPLE_OPTION: CounterScheme(
        opponent_scheme=SchemeType.TRIPLE_OPTION,
        counter_formations=["4-4 Stack", "3-4 Bear", "46 Defense"],
        counter_plays=["QB spy", "crash DE + scrape LB exchange", "pinch DL slant"],
        key_adjustments=[
            "Assign each defender a specific option responsibility (dive/QB/pitch)",
            "Use scrape exchange to confuse the QB read",
            "Force the pitch — the 3rd option is the hardest to execute",
        ],
        defensive_keys=[
            "Watch the mesh point — the QB's eyes tell you give or pull",
            "Pitch back alignment tells you if speed option or triple",
        ],
        confidence=0.75,
    ),
    SchemeType.AIR_RAID: CounterScheme(
        opponent_scheme=SchemeType.AIR_RAID,
        counter_formations=["Nickel", "Dime", "Cover 3 Match"],
        counter_plays=["zone blitz", "cover 2 robber", "press man with safety help"],
        key_adjustments=[
            "Pressure with 5+ rushers to speed up timing",
            "Pattern-match the mesh and spacing concepts",
            "Disguise coverages pre-snap to confuse the QB read",
        ],
        defensive_keys=[
            "Quick passing game — get hands on receivers at the line",
            "Watch for screen setups on obvious passing downs",
        ],
        confidence=0.70,
    ),
    SchemeType.SPREAD_RPO: CounterScheme(
        opponent_scheme=SchemeType.SPREAD_RPO,
        counter_formations=["3-3-5", "Nickel with LB spy", "Cover 6"],
        counter_plays=["scrape exchange", "spy the QB", "bracket the RPO receiver"],
        key_adjustments=[
            "Don't let the conflict defender get caught in no-man's land",
            "Play aggressive on the run — force the throw",
            "Rally to the bubble screen quickly from the secondary",
        ],
        defensive_keys=[
            "Pre-snap motion often reveals RPO vs pure run",
            "OL will tip run vs pass — linemen can't go downfield on pass",
        ],
        confidence=0.70,
    ),
    SchemeType.FLEXBONE: CounterScheme(
        opponent_scheme=SchemeType.FLEXBONE,
        counter_formations=["4-4", "3-4 Eagle", "6-2 Goal Line"],
        counter_plays=["slow play DE", "force the give", "overload the pitch side"],
        key_adjustments=[
            "Assign dive, QB, pitch responsibilities clearly",
            "Cross-face blockers — don't get sealed inside",
            "Be disciplined — the flexbone punishes freelancing",
        ],
        defensive_keys=[
            "Wingback alignment reveals play direction",
            "Watch the FB — his path tells you dive or counter",
        ],
        confidence=0.70,
    ),
    SchemeType.WEST_COAST: CounterScheme(
        opponent_scheme=SchemeType.WEST_COAST,
        counter_formations=["Cover 2", "Tampa 2", "Nickel zone blitz"],
        counter_plays=["jam receivers at the line", "zone blitz", "cover 2 sink"],
        key_adjustments=[
            "Disrupt timing with press coverage",
            "Keep everything in front — force long drives",
            "Tackle immediately — deny yards after catch",
        ],
        defensive_keys=[
            "Short crossing routes are the bread and butter",
            "Play action is dangerous — stay disciplined with eyes",
        ],
        confidence=0.65,
    ),
}


class SchemeDepthAI:
    """CFB 26 scheme mastery engine.

    MVP uses in-memory stores. Production version will persist to database
    and integrate with PlayerTwin for personalized learning paths.
    """

    def __init__(self) -> None:
        # In-memory mastery tracking: (user_id, scheme_type) -> MasteryLevel
        self._mastery_store: dict[tuple[str, str], MasteryLevel] = {}

    # ------------------------------------------------------------------
    # Playbook analysis
    # ------------------------------------------------------------------

    def analyze_playbook_depth(self, playbook: dict) -> PlaybookAnalysis:
        """Full playbook mastery analysis.

        Args:
            playbook: Dict with 'scheme_type', 'plays' (list of play dicts),
                and optional 'game_logs'.

        Returns:
            PlaybookAnalysis with formation breakdown, mastery score,
            strongest/weakest concepts, and diversity score.
        """
        scheme_type = SchemeType(playbook.get("scheme_type", "spread_rpo"))
        plays = playbook.get("plays", [])

        # Group plays by formation
        formation_groups: dict[str, list[dict]] = defaultdict(list)
        for play in plays:
            formation = play.get("formation", "unknown")
            formation_groups[formation].append(play)

        formations = []
        for fname, fplays in formation_groups.items():
            success_rates = [p.get("success_rate", 0.0) for p in fplays]
            avg_sr = sum(success_rates) / len(success_rates) if success_rates else 0.0

            best_sits = []
            weak_sits = []
            for p in fplays:
                tags = p.get("situation_tags", {})
                if p.get("success_rate", 0.0) >= 0.6:
                    best_sits.extend(tags.get("effective_in", []))
                elif p.get("success_rate", 0.0) < 0.4:
                    weak_sits.extend(tags.get("weak_in", []))

            formations.append(FormationAnalysis(
                formation_name=fname,
                play_count=len(fplays),
                avg_success_rate=round(avg_sr, 3),
                best_situations=list(set(best_sits))[:5],
                weakness_situations=list(set(weak_sits))[:5],
            ))

        # Overall mastery based on success rates
        all_rates = [p.get("success_rate", 0.0) for p in plays]
        overall = sum(all_rates) / len(all_rates) if all_rates else 0.0

        # Diversity: how evenly distributed are plays across formations
        if formation_groups:
            counts = [len(v) for v in formation_groups.values()]
            max_count = max(counts) if counts else 1
            diversity = 1.0 - (max_count / sum(counts)) if sum(counts) > 0 else 0.0
        else:
            diversity = 0.0

        # Concept analysis
        concepts = SCHEME_CONCEPTS.get(scheme_type, [])
        strongest = concepts[:3] if overall >= 0.5 else []
        weakest = concepts[-3:] if overall < 0.7 else []

        analysis = PlaybookAnalysis(
            scheme_type=scheme_type,
            total_plays=len(plays),
            formations=formations,
            overall_mastery=round(overall, 3),
            strongest_concepts=strongest,
            weakest_concepts=weakest,
            diversity_score=round(diversity, 3),
        )

        logger.info(
            "Analyzed playbook: scheme=%s plays=%d mastery=%.3f",
            scheme_type.value, len(plays), overall,
        )
        return analysis

    # ------------------------------------------------------------------
    # Scheme mastery
    # ------------------------------------------------------------------

    def get_scheme_mastery(self, user_id: str, scheme_type: SchemeType) -> MasteryLevel:
        """How well a user knows this scheme.

        Returns cached mastery or generates a default NOVICE level.
        """
        key = (user_id, scheme_type.value)
        if key in self._mastery_store:
            return self._mastery_store[key]

        # Default: novice with empty concept mastery
        concepts = SCHEME_CONCEPTS.get(scheme_type, [])
        concept_masteries = [
            ConceptMastery(concept_name=c, proficiency=0.0)
            for c in concepts
        ]

        mastery = MasteryLevel(
            user_id=user_id,
            scheme_type=scheme_type,
            tier=MasteryTier.NOVICE,
            score=0.0,
            concepts_mastered=concept_masteries,
        )
        self._mastery_store[key] = mastery
        return mastery

    def update_mastery(
        self,
        user_id: str,
        scheme_type: SchemeType,
        game_result: dict,
    ) -> MasteryLevel:
        """Update mastery after a game. Called by LoopAI.

        Args:
            game_result: Dict with 'success_rate', 'plays_run', 'win', etc.
        """
        mastery = self.get_scheme_mastery(user_id, scheme_type)
        sr = game_result.get("success_rate", 0.0)
        plays_run = game_result.get("plays_run", 0)

        # Update score with exponential moving average
        alpha = min(0.3, plays_run / 100.0) if plays_run > 0 else 0.1
        new_score = mastery.score * (1 - alpha) + sr * alpha
        new_score = round(min(new_score, 1.0), 4)

        # Determine tier
        tier = MasteryTier.NOVICE
        for t, threshold in sorted(MASTERY_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if new_score >= threshold:
                tier = t
                break

        mastery.score = new_score
        mastery.tier = tier
        mastery.games_played_with_scheme += 1
        if game_result.get("win"):
            total_games = mastery.games_played_with_scheme
            wins = mastery.win_rate_with_scheme * (total_games - 1) + 1.0
            mastery.win_rate_with_scheme = round(wins / total_games, 4)

        self._mastery_store[(user_id, scheme_type.value)] = mastery
        logger.info(
            "Updated mastery: user=%s scheme=%s score=%.4f tier=%s",
            user_id, scheme_type.value, new_score, tier.value,
        )
        return mastery

    # ------------------------------------------------------------------
    # Scheme progression
    # ------------------------------------------------------------------

    def suggest_progression(self, user_id: str, scheme_type: SchemeType) -> SchemeProgression:
        """Suggest next scheme concepts to learn.

        Analyzes current mastery and returns ordered list of concepts
        to focus on, with estimated time to next tier.
        """
        mastery = self.get_scheme_mastery(user_id, scheme_type)

        # Find next tier
        tiers = list(MasteryTier)
        current_idx = tiers.index(mastery.tier)
        next_tier = tiers[min(current_idx + 1, len(tiers) - 1)]
        next_threshold = MASTERY_THRESHOLDS[next_tier]
        progress = mastery.score / next_threshold if next_threshold > 0 else 1.0
        progress = min(progress, 1.0)

        # Find weakest concepts to suggest
        weak_concepts = sorted(
            mastery.concepts_mastered,
            key=lambda c: c.proficiency,
        )
        next_concepts = [c.concept_name for c in weak_concepts[:4]]

        # Estimate hours based on gap
        gap = max(next_threshold - mastery.score, 0.0)
        hours = gap * 50  # rough estimate: 50 hours per 1.0 mastery point

        drills = [
            f"Practice {concept} in free play mode"
            for concept in next_concepts[:3]
        ]

        return SchemeProgression(
            user_id=user_id,
            current_tier=mastery.tier,
            next_tier=next_tier,
            progress_to_next=round(progress, 3),
            next_concepts=next_concepts,
            recommended_drills=drills,
            estimated_hours_to_next_tier=round(hours, 1),
        )

    # ------------------------------------------------------------------
    # Option reads
    # ------------------------------------------------------------------

    def get_option_reads(self, play_type: PlayType) -> OptionReadProgression:
        """Get full read progression for an option/RPO play type.

        Returns pre-snap keys and ordered read progression with tips.
        """
        reads = OPTION_READS.get(play_type, [])

        pre_snap_keys = []
        if play_type in (PlayType.TRIPLE_OPTION, PlayType.SPEED_OPTION):
            pre_snap_keys = [
                "Check defensive front — 4-4 or odd front changes assignments",
                "Identify the pitch key pre-snap",
                "Check safety rotation for play-action opportunity",
            ]
        elif play_type in (PlayType.ZONE_READ,):
            pre_snap_keys = [
                "Identify the backside DE — he is your read",
                "Check for a potential QB spy",
                "Count the box for run/pass decision",
            ]
        elif play_type in (PlayType.RPO_BUBBLE, PlayType.RPO_SLANT, PlayType.RPO_GLANCE):
            pre_snap_keys = [
                "Count the box — 6+ in box = throw, 5 or fewer = hand off",
                "Identify the conflict defender",
                "Check leverage of the slot defender",
            ]

        tempo = "normal"
        if play_type in (PlayType.SPEED_OPTION,):
            tempo = "up-tempo — get to the edge before defense sets"
        elif play_type in (PlayType.RPO_BUBBLE, PlayType.RPO_SLANT):
            tempo = "quick — RPOs must be thrown in rhythm on first read"

        return OptionReadProgression(
            play_type=play_type,
            reads=reads,
            pre_snap_keys=pre_snap_keys,
            tempo_recommendation=tempo,
        )

    # ------------------------------------------------------------------
    # Scheme counters
    # ------------------------------------------------------------------

    def get_scheme_counter(self, opponent_scheme: SchemeType) -> CounterScheme:
        """Get counter strategy for opponent's scheme.

        Returns formations, plays, and adjustments to beat the scheme.
        """
        counter = COUNTER_SCHEMES.get(opponent_scheme)
        if counter:
            return counter

        # Generic counter for unknown schemes
        return CounterScheme(
            opponent_scheme=opponent_scheme,
            counter_formations=["Nickel", "Base 3-4"],
            counter_plays=["zone blitz", "man coverage with safety help"],
            key_adjustments=[
                "Disguise coverage pre-snap",
                "Stay disciplined in assignments",
                "Film study to identify tendencies",
            ],
            defensive_keys=["Watch formation tendencies", "Track personnel groupings"],
            confidence=0.40,
        )


# Module-level singleton
scheme_depth_ai = SchemeDepthAI()
