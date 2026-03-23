"""FortniteMeta AI — loot pool meta, augment priority selector, mobility item optimization.

Tracks current season weapon tiers, recommends augment picks based on playstyle,
and optimizes mobility item carry decisions.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.fortnite.gameplay import (
    AugmentPriority,
    AugmentRarity,
    MetaSnapshot,
    MobilityItem,
    WeaponMeta,
    ZonePhase,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default weapon meta (example Season data — would be loaded from DB/config)
# ---------------------------------------------------------------------------

DEFAULT_WEAPON_META: list[dict[str, Any]] = [
    {"weapon_name": "Nemesis AR", "weapon_class": "AR", "tier": "S", "dps": 198.0,
     "pick_rate": 0.72, "win_rate_correlation": 0.15, "best_range": "medium"},
    {"weapon_name": "Thunder Burst SMG", "weapon_class": "SMG", "tier": "S", "dps": 228.0,
     "pick_rate": 0.68, "win_rate_correlation": 0.12, "best_range": "close"},
    {"weapon_name": "Sovereign Shotgun", "weapon_class": "Shotgun", "tier": "A", "dps": 140.0,
     "pick_rate": 0.85, "win_rate_correlation": 0.18, "best_range": "close"},
    {"weapon_name": "Ranger Pistol", "weapon_class": "Pistol", "tier": "B", "dps": 155.0,
     "pick_rate": 0.25, "win_rate_correlation": 0.02, "best_range": "medium"},
    {"weapon_name": "Reaper Sniper", "weapon_class": "Sniper", "tier": "A", "dps": 75.0,
     "pick_rate": 0.35, "win_rate_correlation": 0.08, "best_range": "long"},
    {"weapon_name": "Boom Bolt", "weapon_class": "Explosive", "tier": "A", "dps": 95.0,
     "pick_rate": 0.30, "win_rate_correlation": 0.10, "best_range": "medium"},
    {"weapon_name": "Gatekeeper Shotgun", "weapon_class": "Shotgun", "tier": "B", "dps": 120.0,
     "pick_rate": 0.40, "win_rate_correlation": 0.05, "best_range": "close"},
    {"weapon_name": "Hyper SMG", "weapon_class": "SMG", "tier": "B", "dps": 195.0,
     "pick_rate": 0.30, "win_rate_correlation": 0.04, "best_range": "close"},
]

DEFAULT_AUGMENTS: list[dict[str, Any]] = [
    {"augment_name": "Aerialist", "rarity": "rare", "priority_rank": 1,
     "synergy_score": 0.9, "playstyle_fit": "aggressive", "take_rate": 0.85,
     "reasoning": "Redeploy glider on jump — top-tier mobility for high-ground retakes."},
    {"augment_name": "Bloodhound", "rarity": "epic", "priority_rank": 2,
     "synergy_score": 0.85, "playstyle_fit": "aggressive", "take_rate": 0.78,
     "reasoning": "Mark enemies on damage — invaluable for tracking in build fights."},
    {"augment_name": "Jelly Angler", "rarity": "uncommon", "priority_rank": 3,
     "synergy_score": 0.7, "playstyle_fit": "balanced", "take_rate": 0.65,
     "reasoning": "Fishing gives shield fish — strong for sustain in mid-game."},
    {"augment_name": "Storm Mark", "rarity": "rare", "priority_rank": 4,
     "synergy_score": 0.75, "playstyle_fit": "passive", "take_rate": 0.60,
     "reasoning": "Marks enemies in storm — excellent for late-game awareness."},
    {"augment_name": "First Assault", "rarity": "epic", "priority_rank": 5,
     "synergy_score": 0.8, "playstyle_fit": "aggressive", "take_rate": 0.72,
     "reasoning": "First bullet of each magazine does bonus damage — rewards accuracy."},
    {"augment_name": "Rarity Check", "rarity": "common", "priority_rank": 6,
     "synergy_score": 0.5, "playstyle_fit": "balanced", "take_rate": 0.40,
     "reasoning": "Chance to upgrade weapon on elimination — snowball potential."},
]

DEFAULT_MOBILITY_ITEMS: list[dict[str, Any]] = [
    {"item_name": "Launch Pad", "availability": "floor_loot",
     "rotation_value": 1.0, "combat_value": 0.7, "carry_priority": 1,
     "best_use_phase": "moving_zone"},
    {"item_name": "Shockwave Grenade", "availability": "chest",
     "rotation_value": 0.8, "combat_value": 0.6, "carry_priority": 2,
     "best_use_phase": "fourth_zone"},
    {"item_name": "Grapple Blade", "availability": "floor_loot",
     "rotation_value": 0.7, "combat_value": 0.8, "carry_priority": 2,
     "best_use_phase": "third_zone"},
    {"item_name": "Shield Bubble", "availability": "chest",
     "rotation_value": 0.5, "combat_value": 0.4, "carry_priority": 3,
     "best_use_phase": "moving_zone"},
]


class FortniteMetaAI:
    """Loot pool meta analyzer, augment selector, and mobility optimizer.

    Provides tier lists, augment priority rankings based on playstyle,
    and mobility item carry optimization.
    """

    def __init__(self) -> None:
        self._weapon_meta = [WeaponMeta(**w) for w in DEFAULT_WEAPON_META]
        self._augments = [AugmentPriority(**a) for a in DEFAULT_AUGMENTS]
        self._mobility_items = [MobilityItem(**m) for m in DEFAULT_MOBILITY_ITEMS]

    # ------------------------------------------------------------------
    # Weapon tier list
    # ------------------------------------------------------------------

    def get_weapon_tier_list(self, weapon_class: str | None = None) -> list[WeaponMeta]:
        """Return the current weapon tier list, optionally filtered by class."""
        weapons = self._weapon_meta
        if weapon_class:
            weapons = [w for w in weapons if w.weapon_class.lower() == weapon_class.lower()]
        return sorted(weapons, key=lambda w: ("SABCD".index(w.tier), -w.dps))

    # ------------------------------------------------------------------
    # Augment priority
    # ------------------------------------------------------------------

    def get_augment_priorities(
        self,
        playstyle: str | None = None,
        top_n: int = 5,
    ) -> list[AugmentPriority]:
        """Return augment priorities, optionally filtered by playstyle.

        Args:
            playstyle: Filter to 'aggressive', 'passive', or 'balanced'.
            top_n: Number of top augments to return.
        """
        augments = self._augments
        if playstyle:
            augments = [
                a for a in augments
                if a.playstyle_fit.lower() == playstyle.lower()
                or a.playstyle_fit.lower() == "balanced"
            ]
        return sorted(augments, key=lambda a: a.priority_rank)[:top_n]

    def select_augment(
        self,
        options: list[str],
        playstyle: str = "balanced",
    ) -> AugmentPriority | None:
        """Select the best augment from a set of offered options.

        Args:
            options: List of augment names offered in-game.
            playstyle: Player's playstyle preference.
        """
        priorities = {a.augment_name.lower(): a for a in self._augments}

        best: AugmentPriority | None = None
        best_rank = 999

        for name in options:
            aug = priorities.get(name.lower())
            if aug is None:
                continue
            # Weight by playstyle fit
            effective_rank = aug.priority_rank
            if aug.playstyle_fit.lower() == playstyle.lower():
                effective_rank -= 1  # Boost matching playstyle
            if effective_rank < best_rank:
                best_rank = effective_rank
                best = aug

        return best

    # ------------------------------------------------------------------
    # Mobility item optimization
    # ------------------------------------------------------------------

    def get_mobility_items(
        self,
        zone_phase: ZonePhase | None = None,
    ) -> list[MobilityItem]:
        """Return mobility items, optionally filtered by best use phase."""
        items = self._mobility_items
        if zone_phase:
            items = [i for i in items if i.best_use_phase == zone_phase]
        return sorted(items, key=lambda i: i.carry_priority)

    def should_carry_mobility(
        self,
        current_zone: ZonePhase,
        has_heals: bool,
        inventory_slots_free: int,
    ) -> dict[str, Any]:
        """Advise whether to carry a mobility item given game state.

        Returns recommendation with reasoning.
        """
        late_game = current_zone in (
            ZonePhase.MOVING_ZONE, ZonePhase.HALF_HALF, ZonePhase.ENDGAME,
            ZonePhase.FOURTH_ZONE,
        )

        if inventory_slots_free <= 0:
            return {
                "carry": late_game,
                "drop_candidate": "least effective heal" if late_game else None,
                "reasoning": (
                    "Inventory full. In late game, mobility is worth more than "
                    "an extra heal stack." if late_game
                    else "Keep your current loadout — mobility is less critical early."
                ),
            }

        if late_game:
            return {
                "carry": True,
                "drop_candidate": None,
                "reasoning": (
                    "Late game — launch pads and shockwaves can save your game. "
                    "Always carry at least one mobility item."
                ),
            }

        return {
            "carry": inventory_slots_free >= 2,
            "drop_candidate": None,
            "reasoning": (
                "Mid-game: carry mobility if you have the slot. "
                "Prioritize weapons and heals first."
            ),
        }

    # ------------------------------------------------------------------
    # Full meta snapshot
    # ------------------------------------------------------------------

    def get_meta_snapshot(
        self,
        patch_version: str = "32.10",
        season: str = "Chapter 6 Season 2",
    ) -> MetaSnapshot:
        """Generate a full meta snapshot for the current patch."""
        return MetaSnapshot(
            patch_version=patch_version,
            season=season,
            weapon_tier_list=self.get_weapon_tier_list(),
            augment_priorities=self.get_augment_priorities(),
            mobility_items=self.get_mobility_items(),
            loot_pool_notes=[
                "Nemesis AR dominates mid-range — must-carry in competitive.",
                "Sovereign Shotgun is consistent but lower DPS than previous metas.",
                "Boom Bolt is the best explosive option for breaking builds.",
                "Launch Pads are the highest-value mobility item this season.",
            ],
            meta_shift_summary=(
                "Current meta favors aggressive piece-control with Nemesis AR "
                "for chip damage and Sovereign Shotgun for box fights. "
                "Mobility items are premium due to reduced spawn rates."
            ),
        )
