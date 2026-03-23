"""GunfightAI — recoil pattern trainer, first bullet accuracy trainer, engagement range decision engine.

Provides combat training intelligence for Warzone by analyzing recoil patterns,
generating aim drills, and making tactical engagement decisions.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.warzone.combat import (
    EngagementDecision,
    EngagementRange,
    FirstBulletDrill,
    GunfightAnalysis,
    RecoilPattern,
    WeaponClass,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Recoil database
# ---------------------------------------------------------------------------

_RECOIL_DB: dict[str, dict[str, Any]] = {
    "MCW": {
        "class": WeaponClass.ASSAULT_RIFLE,
        "vertical": 3.2, "horizontal": 1.1,
        "shape": "vertical_climb",
        "compensation": "Pull down steadily — minimal horizontal correction needed.",
        "difficulty": 3.0, "first_5_acc": 0.88,
    },
    "SVA 545": {
        "class": WeaponClass.ASSAULT_RIFLE,
        "vertical": 4.5, "horizontal": 0.8,
        "shape": "burst_kick",
        "compensation": "Counter initial burst kick, then reset between bursts.",
        "difficulty": 5.5, "first_5_acc": 0.82,
    },
    "Holger 556": {
        "class": WeaponClass.ASSAULT_RIFLE,
        "vertical": 3.8, "horizontal": 1.5,
        "shape": "S_curve",
        "compensation": "Pull down-left for first 10 rounds, then shift down-right.",
        "difficulty": 4.5, "first_5_acc": 0.85,
    },
    "Striker": {
        "class": WeaponClass.SMG,
        "vertical": 5.0, "horizontal": 2.0,
        "shape": "vertical_climb",
        "compensation": "Strong downward pull — recoil is vertical-dominant.",
        "difficulty": 4.0, "first_5_acc": 0.80,
    },
    "HRM-9": {
        "class": WeaponClass.SMG,
        "vertical": 3.5, "horizontal": 2.5,
        "shape": "left_pull",
        "compensation": "Pull down-right to counter leftward horizontal drift.",
        "difficulty": 5.0, "first_5_acc": 0.78,
    },
    "Superi 46": {
        "class": WeaponClass.SMG,
        "vertical": 2.8, "horizontal": 1.8,
        "shape": "random_spread",
        "compensation": "Low recoil overall — focus on tracking rather than countering.",
        "difficulty": 2.5, "first_5_acc": 0.90,
    },
    "KATT-AMR": {
        "class": WeaponClass.SNIPER,
        "vertical": 8.0, "horizontal": 0.5,
        "shape": "single_kick",
        "compensation": "Recenter after each shot — bolt-action recoil resets between rounds.",
        "difficulty": 2.0, "first_5_acc": 0.95,
    },
    "Pulemyot 762": {
        "class": WeaponClass.LMG,
        "vertical": 4.2, "horizontal": 2.8,
        "shape": "widening_cone",
        "compensation": "Pull down firmly. After 20 rounds, horizontal spread widens — burst fire.",
        "difficulty": 6.0, "first_5_acc": 0.75,
    },
}

# TTK reference per weapon at different ranges (ms)
_TTK_TABLE: dict[str, dict[EngagementRange, int]] = {
    "MCW": {EngagementRange.CQB: 680, EngagementRange.SHORT: 640, EngagementRange.MEDIUM: 620, EngagementRange.LONG: 700, EngagementRange.EXTREME: 850},
    "SVA 545": {EngagementRange.CQB: 650, EngagementRange.SHORT: 610, EngagementRange.MEDIUM: 600, EngagementRange.LONG: 680, EngagementRange.EXTREME: 820},
    "Striker": {EngagementRange.CQB: 520, EngagementRange.SHORT: 540, EngagementRange.MEDIUM: 640, EngagementRange.LONG: 900, EngagementRange.EXTREME: 1200},
    "HRM-9": {EngagementRange.CQB: 540, EngagementRange.SHORT: 560, EngagementRange.MEDIUM: 680, EngagementRange.LONG: 950, EngagementRange.EXTREME: 1300},
    "KATT-AMR": {EngagementRange.CQB: 1500, EngagementRange.SHORT: 1200, EngagementRange.MEDIUM: 800, EngagementRange.LONG: 300, EngagementRange.EXTREME: 250},
}

# Drill templates
_DRILLS: list[dict[str, Any]] = [
    {
        "name": "Centering Snap Drill",
        "description": "Place crosshair on a wall mark, look away 90 degrees, snap back to the mark. "
                       "Repeat 20 times. Goal: land within 5px of center each snap.",
        "target_accuracy": 0.90,
        "sens": {"horizontal": 6.0, "vertical": 6.0, "ads_multiplier": 1.0},
        "reps": 20,
        "focus": ["Crosshair placement", "Snap aim", "Muscle memory"],
    },
    {
        "name": "Tracking Carousel",
        "description": "Track a moving target in a circle pattern for 30 seconds. "
                       "Maintain beam on center mass. Measure time-on-target percentage.",
        "target_accuracy": 0.75,
        "sens": {"horizontal": 5.5, "vertical": 5.5, "ads_multiplier": 0.9},
        "reps": 10,
        "focus": ["Smooth tracking", "Sustained aim", "Micro-adjustments"],
    },
    {
        "name": "First Bullet Flick",
        "description": "Three targets at varying distances appear sequentially. "
                       "Fire one bullet at each — only first shot counts. Reset and repeat.",
        "target_accuracy": 0.85,
        "sens": {"horizontal": 6.0, "vertical": 6.0, "ads_multiplier": 1.0},
        "reps": 15,
        "focus": ["First bullet accuracy", "Target acquisition", "Flick precision"],
    },
    {
        "name": "Strafe & Shoot",
        "description": "Strafe left-right while keeping crosshair on a stationary target. "
                       "Fire in 3-round bursts. Goal: all rounds hit center mass.",
        "target_accuracy": 0.80,
        "sens": {"horizontal": 5.0, "vertical": 5.0, "ads_multiplier": 1.0},
        "reps": 15,
        "focus": ["Movement + aim separation", "Burst discipline", "Counter-strafing"],
    },
    {
        "name": "Long Range Holds",
        "description": "Hold an angle at 80m+ distance. Target peeks for 0.5s intervals. "
                       "Fire on peek — measure reaction time and hit rate.",
        "target_accuracy": 0.70,
        "sens": {"horizontal": 4.5, "vertical": 4.5, "ads_multiplier": 0.8},
        "reps": 12,
        "focus": ["Reaction time", "Angle holding", "Trigger discipline"],
    },
]


# ---------------------------------------------------------------------------
# GunfightAI
# ---------------------------------------------------------------------------

class GunfightAI:
    """Combat mechanics training and engagement decision engine."""

    # ------------------------------------------------------------------
    # get_recoil_patterns
    # ------------------------------------------------------------------

    def get_recoil_patterns(
        self,
        weapon_names: list[str] | None = None,
        weapon_class: WeaponClass | None = None,
    ) -> list[RecoilPattern]:
        """Return recoil pattern analysis for specified weapons or class."""
        results: list[RecoilPattern] = []

        for name, data in _RECOIL_DB.items():
            if weapon_names and name not in weapon_names:
                continue
            if weapon_class and data["class"] != weapon_class:
                continue
            results.append(RecoilPattern(
                weapon_name=name,
                weapon_class=data["class"],
                vertical_pull=data["vertical"],
                horizontal_drift=data["horizontal"],
                pattern_shape=data["shape"],
                compensation_instruction=data["compensation"],
                difficulty_rating=data["difficulty"],
                first_5_bullets_accuracy=data["first_5_acc"],
            ))

        return sorted(results, key=lambda r: r.difficulty_rating)

    # ------------------------------------------------------------------
    # get_first_bullet_drills
    # ------------------------------------------------------------------

    def get_first_bullet_drills(self, skill_level: str = "intermediate") -> list[FirstBulletDrill]:
        """Return aim training drills for first bullet accuracy.

        Adjusts target accuracy thresholds based on skill level.
        """
        level_multiplier = {"beginner": 0.85, "intermediate": 1.0, "advanced": 1.1}
        mult = level_multiplier.get(skill_level, 1.0)

        drills: list[FirstBulletDrill] = []
        for d in _DRILLS:
            adjusted_target = min(1.0, d["target_accuracy"] * mult)
            drills.append(FirstBulletDrill(
                drill_name=d["name"],
                description=d["description"],
                target_accuracy=round(adjusted_target, 2),
                recommended_sensitivity=d["sens"],
                warmup_reps=d["reps"],
                focus_areas=d["focus"],
            ))

        return drills

    # ------------------------------------------------------------------
    # evaluate_engagement
    # ------------------------------------------------------------------

    def evaluate_engagement(
        self,
        your_weapon: str,
        enemy_weapon: str,
        engagement_range: EngagementRange,
        your_health: int = 250,
        enemy_health: int = 250,
        your_plates: int = 3,
        enemy_plates: int = 3,
    ) -> EngagementDecision:
        """Decision engine: should you take this fight?

        Compares TTK at the given range, factors in health/armor state,
        and recommends engagement approach.
        """
        your_ttk_table = _TTK_TABLE.get(your_weapon, {})
        enemy_ttk_table = _TTK_TABLE.get(enemy_weapon, {})

        your_ttk = your_ttk_table.get(engagement_range, 800)
        enemy_ttk = enemy_ttk_table.get(engagement_range, 800)

        # Adjust TTK for health/plates
        your_effective_hp = your_health + your_plates * 50
        enemy_effective_hp = enemy_health + enemy_plates * 50
        hp_ratio = enemy_effective_hp / max(your_effective_hp, 1)

        adjusted_your_ttk = int(your_ttk * hp_ratio)
        adjusted_enemy_ttk = int(enemy_ttk * (your_effective_hp / max(enemy_effective_hp, 1)))

        ttk_advantage = adjusted_enemy_ttk - adjusted_your_ttk

        # Determine optimal range for your weapon
        if your_ttk_table:
            optimal_range = min(your_ttk_table, key=your_ttk_table.get)
        else:
            optimal_range = EngagementRange.MEDIUM

        # Decision logic
        if ttk_advantage > 100:
            should_engage = True
            confidence = min(1.0, 0.6 + ttk_advantage / 500)
            approach = "push"
            reasoning = (
                f"You have a {ttk_advantage}ms TTK advantage with {your_weapon} "
                f"at {engagement_range.value} range. Push aggressively."
            )
        elif ttk_advantage > 0:
            should_engage = True
            confidence = 0.5 + ttk_advantage / 400
            approach = "hold"
            reasoning = (
                f"Slight TTK edge ({ttk_advantage}ms) with {your_weapon}. "
                f"Hold position and let them push into your crosshair."
            )
        elif ttk_advantage > -100:
            should_engage = False
            confidence = 0.4
            approach = "reposition"
            reasoning = (
                f"Nearly even fight ({abs(ttk_advantage)}ms disadvantage). "
                f"Reposition to your optimal range ({optimal_range.value}) before engaging."
            )
        else:
            should_engage = False
            confidence = min(1.0, 0.6 + abs(ttk_advantage) / 500)
            approach = "disengage"
            reasoning = (
                f"Significant TTK disadvantage ({abs(ttk_advantage)}ms) against {enemy_weapon} "
                f"at {engagement_range.value}. Disengage and reposition."
            )

        return EngagementDecision(
            should_engage=should_engage,
            confidence=round(min(1.0, confidence), 2),
            reasoning=reasoning,
            optimal_range=optimal_range,
            recommended_approach=approach,
            ttk_advantage_ms=ttk_advantage,
        )

    # ------------------------------------------------------------------
    # full_gunfight_analysis
    # ------------------------------------------------------------------

    def full_gunfight_analysis(
        self,
        weapon_names: list[str] | None = None,
        your_weapon: str | None = None,
        enemy_weapon: str | None = None,
        engagement_range: EngagementRange = EngagementRange.MEDIUM,
        skill_level: str = "intermediate",
    ) -> GunfightAnalysis:
        """Complete gunfight intelligence: recoil data, drills, and engagement decision."""
        patterns = self.get_recoil_patterns(weapon_names=weapon_names)
        drills = self.get_first_bullet_drills(skill_level=skill_level)

        decision = None
        if your_weapon and enemy_weapon:
            decision = self.evaluate_engagement(
                your_weapon=your_weapon,
                enemy_weapon=enemy_weapon,
                engagement_range=engagement_range,
            )

        weapons_str = ", ".join(p.weapon_name for p in patterns) if patterns else "all weapons"
        summary = f"Gunfight analysis for {weapons_str}. "
        if decision:
            summary += (
                f"Engagement verdict: {'ENGAGE' if decision.should_engage else 'AVOID'} "
                f"({decision.recommended_approach}). "
            )
        summary += f"{len(drills)} training drills recommended for {skill_level} level."

        return GunfightAnalysis(
            recoil_patterns=patterns,
            first_bullet_drills=drills,
            engagement_decision=decision,
            summary=summary,
        )
