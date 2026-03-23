"""BuildForge AI — meta build analysis, badge allocation optimizer, attribute thresholds.

Analyzes NBA 2K26 player builds for optimal attribute allocation, badge distribution,
and meta-tier classification. Provides threshold-aware upgrade recommendations and
compares builds against the current competitive meta.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from app.schemas.nba2k26.builds import (
    Archetype,
    Badge,
    BadgeAllocation,
    BadgeCategory,
    BadgeTier,
    Build,
    BuildAnalysisResult,
    BuildAttributes,
    BuildCompareResult,
    AttributeThreshold,
    MetaBuild,
    MetaTier,
    Position,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Attribute threshold breakpoints — where new animations/abilities unlock
# ---------------------------------------------------------------------------

ATTRIBUTE_THRESHOLDS: dict[str, list[tuple[int, list[str]]]] = {
    "ball_handle": [
        (70, ["Basic size-up package"]),
        (75, ["Pro dribble moves", "Quick chain combos"]),
        (80, ["Elite dribble style", "Speed boost eligible"]),
        (85, ["Advanced size-up escape", "Pro combo chains"]),
        (90, ["Unlimited ankle breakers", "All dribble animations"]),
    ],
    "driving_dunk": [
        (70, ["Basic one-hand dunks"]),
        (75, ["Off-one-foot dunks"]),
        (80, ["Contact dunk package (under 6'10)"]),
        (84, ["Pro contact dunks"]),
        (90, ["Elite contact dunks", "Bigman contact dunks (6'10+)"]),
    ],
    "three_point_shot": [
        (70, ["Corner specialist viable"]),
        (75, ["Catch-and-shoot reliable"]),
        (80, ["Pull-up three viable"]),
        (86, ["Limitless range viable"]),
        (92, ["Green machine at high volume"]),
    ],
    "perimeter_defense": [
        (70, ["Basic clamps badge"]),
        (75, ["Improved lateral quickness"]),
        (80, ["Clamps silver viable"]),
        (86, ["Clamps gold viable"]),
        (92, ["Clamps HOF viable", "Lock-take badge"]),
    ],
    "speed_with_ball": [
        (70, ["Basic speed boost on moves"]),
        (75, ["Consistent speed boost triggers"]),
        (80, ["Speed boost on all moves"]),
        (86, ["Elite speed burst"]),
    ],
    "mid_range_shot": [
        (70, ["Post fade viable"]),
        (80, ["Mid-range dead-eye viable"]),
        (86, ["Mismatch expert viable"]),
    ],
    "pass_accuracy": [
        (70, ["Basic bullet pass"]),
        (75, ["Flashy pass reliable"]),
        (80, ["Dimer badge viable"]),
        (86, ["Special delivery viable"]),
        (92, ["Break starter HOF viable"]),
    ],
    "interior_defense": [
        (70, ["Basic rim protection"]),
        (75, ["Anchor badge viable"]),
        (80, ["Paint intimidator"]),
        (86, ["Anchor gold viable"]),
        (92, ["Anchor HOF viable"]),
    ],
}

# ---------------------------------------------------------------------------
# Badge point costs per tier
# ---------------------------------------------------------------------------

BADGE_TIER_COST: dict[BadgeTier, int] = {
    BadgeTier.BRONZE: 1,
    BadgeTier.SILVER: 2,
    BadgeTier.GOLD: 3,
    BadgeTier.HALL_OF_FAME: 4,
    BadgeTier.LEGEND: 5,
}

# ---------------------------------------------------------------------------
# Meta build templates
# ---------------------------------------------------------------------------

META_BUILDS: list[MetaBuild] = [
    MetaBuild(
        name="6-6 Two-Way Slasher",
        position=Position.SG,
        archetype=Archetype.TWO_WAY,
        meta_tier=MetaTier.S_TIER,
        win_rate=0.68,
        pick_rate=0.15,
        attributes=BuildAttributes(
            close_shot=82, driving_layup=90, driving_dunk=92, three_point_shot=78,
            mid_range_shot=75, ball_handle=82, speed_with_ball=85, perimeter_defense=90,
            steal=88, speed=92, acceleration=90, vertical=88, stamina=90,
        ),
        core_badges=[
            Badge(name="Posterizer", category=BadgeCategory.FINISHING, tier=BadgeTier.HALL_OF_FAME,
                  unlock_attribute="driving_dunk", unlock_threshold=90),
            Badge(name="Clamps", category=BadgeCategory.DEFENSE, tier=BadgeTier.GOLD,
                  unlock_attribute="perimeter_defense", unlock_threshold=86),
        ],
        strengths=["Rim finishing", "Perimeter defense", "Transition offense"],
        weaknesses=["Spot-up shooting consistency", "Post play"],
        counter_builds=["Stretch Big", "Sharpshooter"],
    ),
    MetaBuild(
        name="6-9 Stretch Glass Cleaner",
        position=Position.PF,
        archetype=Archetype.STRETCH,
        meta_tier=MetaTier.S_TIER,
        win_rate=0.65,
        pick_rate=0.12,
        attributes=BuildAttributes(
            three_point_shot=88, mid_range_shot=80, standing_dunk=75,
            interior_defense=82, defensive_rebound=92, offensive_rebound=78,
            block=80, strength=85, speed=72, stamina=88,
        ),
        core_badges=[
            Badge(name="Limitless Range", category=BadgeCategory.SHOOTING, tier=BadgeTier.GOLD,
                  unlock_attribute="three_point_shot", unlock_threshold=86),
            Badge(name="Rebound Chaser", category=BadgeCategory.DEFENSE, tier=BadgeTier.HALL_OF_FAME,
                  unlock_attribute="defensive_rebound", unlock_threshold=90),
        ],
        strengths=["Floor spacing", "Rebounding", "Rim protection"],
        weaknesses=["Ball handling", "Perimeter defense"],
        counter_builds=["Slasher", "Playmaker"],
    ),
    MetaBuild(
        name="6-2 Shot-Creating Playmaker",
        position=Position.PG,
        archetype=Archetype.SHOT_CREATOR,
        meta_tier=MetaTier.A_TIER,
        win_rate=0.62,
        pick_rate=0.18,
        attributes=BuildAttributes(
            three_point_shot=85, mid_range_shot=88, ball_handle=92, speed_with_ball=90,
            pass_accuracy=88, driving_layup=80, speed=95, acceleration=94, stamina=90,
        ),
        core_badges=[
            Badge(name="Ankle Breaker", category=BadgeCategory.PLAYMAKING, tier=BadgeTier.HALL_OF_FAME,
                  unlock_attribute="ball_handle", unlock_threshold=90),
            Badge(name="Agent", category=BadgeCategory.SHOOTING, tier=BadgeTier.GOLD,
                  unlock_attribute="mid_range_shot", unlock_threshold=86),
        ],
        strengths=["Ball handling", "Shot creation", "Passing"],
        weaknesses=["Defense against bigs", "Rebounding", "Finishing through contact"],
        counter_builds=["Lockdown", "Two-Way"],
    ),
]


class BuildForge:
    """NBA 2K26 build optimization engine.

    Analyzes builds for meta viability, recommends optimal badge allocation,
    tracks attribute thresholds, and provides head-to-head comparisons.
    """

    def __init__(self) -> None:
        self._user_builds: dict[str, list[Build]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Meta build analysis
    # ------------------------------------------------------------------

    def analyze_build(self, build: Build) -> BuildAnalysisResult:
        """Full analysis of a player build — meta tier, badge optimization, thresholds.

        Evaluates the build against known meta templates, computes optimal badge
        allocation, and identifies the most impactful attribute threshold targets.
        """
        meta_tier = self._classify_meta_tier(build)
        badge_alloc = self.optimize_badges(build)
        thresholds = self.get_attribute_thresholds(build)
        similar = self._find_similar_meta_builds(build)
        tips = self._generate_optimization_tips(build, thresholds, badge_alloc)

        result = BuildAnalysisResult(
            build=build,
            badge_allocation=badge_alloc,
            attribute_thresholds=thresholds,
            meta_tier=meta_tier,
            optimization_tips=tips,
            similar_meta_builds=similar,
        )

        logger.info(
            "Analyzed build: name=%s position=%s tier=%s",
            build.name, build.position.value, meta_tier.value,
        )
        return result

    def _classify_meta_tier(self, build: Build) -> MetaTier:
        """Classify a build into a meta tier based on attribute distribution."""
        attrs = build.attributes
        key_attrs = [
            attrs.three_point_shot, attrs.ball_handle, attrs.speed,
            attrs.perimeter_defense, attrs.driving_dunk, attrs.mid_range_shot,
        ]
        avg_key = sum(key_attrs) / len(key_attrs)

        if avg_key >= 85:
            return MetaTier.S_TIER
        if avg_key >= 78:
            return MetaTier.A_TIER
        if avg_key >= 70:
            return MetaTier.B_TIER
        if avg_key >= 62:
            return MetaTier.C_TIER
        return MetaTier.D_TIER

    def _find_similar_meta_builds(self, build: Build) -> list[MetaBuild]:
        """Find meta builds similar to the user's build."""
        similar = []
        for meta in META_BUILDS:
            if meta.position == build.position or meta.archetype == build.archetype:
                similar.append(meta)
        return similar[:3]

    def _generate_optimization_tips(
        self,
        build: Build,
        thresholds: list[AttributeThreshold],
        badge_alloc: BadgeAllocation,
    ) -> list[str]:
        """Generate actionable optimization tips for a build."""
        tips: list[str] = []

        # Check for close-to-threshold attributes
        high_priority = [t for t in thresholds if t.priority >= 0.8]
        for t in high_priority[:3]:
            gap = t.next_threshold - t.current_value
            tips.append(
                f"Invest {gap} more points in {t.attribute_name} to unlock: "
                f"{', '.join(t.unlocks_at_threshold)}"
            )

        # Check badge optimization
        if badge_alloc.optimization_score < 0.6:
            tips.append(
                "Badge allocation is sub-optimal — consider redistributing badge points "
                "to maximize your archetype strengths."
            )

        # Position-specific tips
        if build.position in (Position.PG, Position.SG):
            if build.attributes.ball_handle < 80:
                tips.append(
                    "Guards need 80+ ball handle for speed boost — "
                    "prioritize this threshold."
                )
        elif build.position in (Position.PF, Position.C):
            if build.attributes.interior_defense < 75:
                tips.append(
                    "Bigs need 75+ interior defense for Anchor badge — "
                    "critical for paint protection."
                )

        if not tips:
            tips.append("Build is well-optimized for the current meta.")

        return tips

    # ------------------------------------------------------------------
    # Badge allocation optimizer
    # ------------------------------------------------------------------

    def optimize_badges(self, build: Build) -> BadgeAllocation:
        """Compute optimal badge allocation for a build's attributes.

        Assigns badges based on which attributes exceed unlock thresholds,
        prioritizing the highest-impact badges for the build's archetype.
        """
        finishing: list[Badge] = []
        shooting: list[Badge] = []
        playmaking: list[Badge] = []
        defense: list[Badge] = []

        attrs = build.attributes

        # Finishing badges
        if attrs.driving_dunk >= 84:
            finishing.append(Badge(
                name="Posterizer", category=BadgeCategory.FINISHING,
                tier=BadgeTier.GOLD if attrs.driving_dunk >= 90 else BadgeTier.SILVER,
                unlock_attribute="driving_dunk", unlock_threshold=84,
            ))
        if attrs.driving_layup >= 80:
            finishing.append(Badge(
                name="Acrobat", category=BadgeCategory.FINISHING,
                tier=BadgeTier.GOLD if attrs.driving_layup >= 88 else BadgeTier.SILVER,
                unlock_attribute="driving_layup", unlock_threshold=80,
            ))
        if attrs.close_shot >= 75:
            finishing.append(Badge(
                name="Pro Touch", category=BadgeCategory.FINISHING,
                tier=BadgeTier.SILVER, unlock_attribute="close_shot", unlock_threshold=75,
            ))

        # Shooting badges
        if attrs.three_point_shot >= 80:
            tier = BadgeTier.HALL_OF_FAME if attrs.three_point_shot >= 92 else (
                BadgeTier.GOLD if attrs.three_point_shot >= 86 else BadgeTier.SILVER
            )
            shooting.append(Badge(
                name="Limitless Range", category=BadgeCategory.SHOOTING,
                tier=tier, unlock_attribute="three_point_shot", unlock_threshold=80,
            ))
        if attrs.mid_range_shot >= 80:
            shooting.append(Badge(
                name="Agent", category=BadgeCategory.SHOOTING,
                tier=BadgeTier.GOLD if attrs.mid_range_shot >= 86 else BadgeTier.SILVER,
                unlock_attribute="mid_range_shot", unlock_threshold=80,
            ))
        if attrs.three_point_shot >= 75:
            shooting.append(Badge(
                name="Catch & Shoot", category=BadgeCategory.SHOOTING,
                tier=BadgeTier.SILVER, unlock_attribute="three_point_shot", unlock_threshold=75,
            ))

        # Playmaking badges
        if attrs.ball_handle >= 85:
            playmaking.append(Badge(
                name="Ankle Breaker", category=BadgeCategory.PLAYMAKING,
                tier=BadgeTier.HALL_OF_FAME if attrs.ball_handle >= 90 else BadgeTier.GOLD,
                unlock_attribute="ball_handle", unlock_threshold=85,
            ))
        if attrs.pass_accuracy >= 80:
            playmaking.append(Badge(
                name="Dimer", category=BadgeCategory.PLAYMAKING,
                tier=BadgeTier.GOLD if attrs.pass_accuracy >= 86 else BadgeTier.SILVER,
                unlock_attribute="pass_accuracy", unlock_threshold=80,
            ))
        if attrs.speed_with_ball >= 80:
            playmaking.append(Badge(
                name="Quick First Step", category=BadgeCategory.PLAYMAKING,
                tier=BadgeTier.GOLD, unlock_attribute="speed_with_ball", unlock_threshold=80,
            ))

        # Defense badges
        if attrs.perimeter_defense >= 80:
            defense.append(Badge(
                name="Clamps", category=BadgeCategory.DEFENSE,
                tier=BadgeTier.HALL_OF_FAME if attrs.perimeter_defense >= 92 else (
                    BadgeTier.GOLD if attrs.perimeter_defense >= 86 else BadgeTier.SILVER
                ),
                unlock_attribute="perimeter_defense", unlock_threshold=80,
            ))
        if attrs.interior_defense >= 75:
            defense.append(Badge(
                name="Anchor", category=BadgeCategory.DEFENSE,
                tier=BadgeTier.GOLD if attrs.interior_defense >= 86 else BadgeTier.SILVER,
                unlock_attribute="interior_defense", unlock_threshold=75,
            ))
        if attrs.steal >= 80:
            defense.append(Badge(
                name="Glove", category=BadgeCategory.DEFENSE,
                tier=BadgeTier.GOLD if attrs.steal >= 88 else BadgeTier.SILVER,
                unlock_attribute="steal", unlock_threshold=80,
            ))

        all_badges = finishing + shooting + playmaking + defense
        total_used = sum(BADGE_TIER_COST[b.tier] for b in all_badges)
        total_available = self._compute_badge_points(build)
        opt_score = min(total_used / max(total_available, 1), 1.0)

        return BadgeAllocation(
            build_id=build.id,
            finishing_badges=finishing,
            shooting_badges=shooting,
            playmaking_badges=playmaking,
            defense_badges=defense,
            total_badge_points_used=total_used,
            total_badge_points_available=total_available,
            optimization_score=round(opt_score, 3),
        )

    def _compute_badge_points(self, build: Build) -> int:
        """Estimate total badge points available based on overall rating."""
        ovr = build.overall_rating
        if ovr >= 95:
            return 60
        if ovr >= 90:
            return 50
        if ovr >= 85:
            return 40
        if ovr >= 80:
            return 30
        return 20

    # ------------------------------------------------------------------
    # Attribute threshold tracker
    # ------------------------------------------------------------------

    def get_attribute_thresholds(self, build: Build) -> list[AttributeThreshold]:
        """Identify the most impactful attribute thresholds the build is near.

        Returns thresholds sorted by priority — closest and most impactful first.
        """
        attrs = build.attributes
        attr_dict = attrs.model_dump()
        results: list[AttributeThreshold] = []

        for attr_name, breakpoints in ATTRIBUTE_THRESHOLDS.items():
            current_val = attr_dict.get(attr_name, 25)
            for threshold_val, unlocks in breakpoints:
                if current_val < threshold_val:
                    gap = threshold_val - current_val
                    # Priority: closer thresholds and more unlocks = higher priority
                    priority = max(0.0, 1.0 - (gap / 30.0)) * (0.5 + 0.1 * len(unlocks))
                    priority = min(priority, 1.0)
                    results.append(AttributeThreshold(
                        attribute_name=attr_name,
                        current_value=current_val,
                        next_threshold=threshold_val,
                        unlocks_at_threshold=unlocks,
                        priority=round(priority, 3),
                    ))
                    break  # Only report the next threshold per attribute

        results.sort(key=lambda t: t.priority, reverse=True)
        return results

    # ------------------------------------------------------------------
    # Build comparison
    # ------------------------------------------------------------------

    def compare_builds(self, build_a: Build, build_b: Build) -> BuildCompareResult:
        """Head-to-head comparison of two builds.

        Evaluates attribute advantages, badge quality, and predicts
        the matchup winner based on positional context.
        """
        attrs_a = build_a.attributes.model_dump()
        attrs_b = build_b.attributes.model_dump()

        advantages_a: dict[str, int] = {}
        advantages_b: dict[str, int] = {}

        for key in attrs_a:
            diff = attrs_a[key] - attrs_b[key]
            if diff > 0:
                advantages_a[key] = diff
            elif diff < 0:
                advantages_b[key] = abs(diff)

        # Badge advantage
        badges_a = self.optimize_badges(build_a)
        badges_b = self.optimize_badges(build_b)
        badge_adv = "even"
        if badges_a.total_badge_points_used > badges_b.total_badge_points_used + 5:
            badge_adv = "build_a"
        elif badges_b.total_badge_points_used > badges_a.total_badge_points_used + 5:
            badge_adv = "build_b"

        # Simple matchup prediction based on total advantages
        total_adv_a = sum(advantages_a.values())
        total_adv_b = sum(advantages_b.values())
        total = total_adv_a + total_adv_b or 1
        confidence = abs(total_adv_a - total_adv_b) / total
        prediction = (
            f"{build_a.name} wins" if total_adv_a > total_adv_b
            else f"{build_b.name} wins" if total_adv_b > total_adv_a
            else "Even matchup"
        )

        return BuildCompareResult(
            build_a=build_a,
            build_b=build_b,
            attribute_advantages_a=advantages_a,
            attribute_advantages_b=advantages_b,
            badge_advantage=badge_adv,
            matchup_prediction=prediction,
            confidence=round(min(confidence, 1.0), 3),
        )

    # ------------------------------------------------------------------
    # Meta build database
    # ------------------------------------------------------------------

    def get_meta_builds(
        self,
        position: Position | None = None,
        tier: MetaTier | None = None,
    ) -> list[MetaBuild]:
        """Retrieve current meta builds, optionally filtered by position/tier."""
        results = META_BUILDS[:]
        if position:
            results = [b for b in results if b.position == position]
        if tier:
            results = [b for b in results if b.meta_tier == tier]
        return results

    def get_counter_builds(self, archetype: Archetype) -> list[MetaBuild]:
        """Find meta builds that counter a given archetype."""
        counters: list[MetaBuild] = []
        for meta in META_BUILDS:
            if archetype.value in [c.lower().replace("-", "_").replace(" ", "_")
                                   for c in meta.counter_builds]:
                counters.append(meta)
        # Also return builds that are strong against the archetype's weaknesses
        if not counters:
            for meta in META_BUILDS:
                if meta.archetype != archetype:
                    counters.append(meta)
        return counters[:3]


# Module-level singleton
build_forge = BuildForge()
