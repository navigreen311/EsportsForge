"""SceneReader — zone position reading, squad location detection, loot tier identification.

Provides game-specific scene understanding by reading zone positions,
detecting squad member locations, and identifying loot/item tiers.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.visionaudio import (
    LootTier,
    LootTierDetection,
    SquadLocation,
    ZonePositionRead,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Zone position rules per title
# ---------------------------------------------------------------------------

_ZONE_TYPES: dict[str, dict[str, Any]] = {
    "madden26": {
        "zones": ["red_zone", "midfield", "backed_up", "neutral", "scoring_position"],
        "position_from_yard_line": True,
    },
    "eafc26": {
        "zones": ["attacking_third", "midfield", "defensive_third", "box", "wide_area"],
        "position_from_coordinates": True,
    },
    "fortnite": {
        "zones": ["storm_safe", "storm_edge", "storm_inside", "high_ground", "low_ground"],
        "position_from_minimap": True,
    },
    "warzone": {
        "zones": ["safe_zone", "edge_zone", "gas", "buy_station_nearby", "loadout_area"],
        "position_from_minimap": True,
    },
}

_LOOT_TIERS: dict[str, dict[str, Any]] = {
    "fortnite": {
        "common": {"color": "gray", "rarity": 1, "value": 0.2},
        "uncommon": {"color": "green", "rarity": 2, "value": 0.4},
        "rare": {"color": "blue", "rarity": 3, "value": 0.6},
        "epic": {"color": "purple", "rarity": 4, "value": 0.8},
        "legendary": {"color": "gold", "rarity": 5, "value": 1.0},
        "mythic": {"color": "gold_shimmer", "rarity": 6, "value": 1.0},
    },
    "warzone": {
        "common": {"color": "white", "rarity": 1, "value": 0.2},
        "uncommon": {"color": "green", "rarity": 2, "value": 0.4},
        "rare": {"color": "blue", "rarity": 3, "value": 0.6},
        "epic": {"color": "purple", "rarity": 4, "value": 0.8},
        "legendary": {"color": "orange", "rarity": 5, "value": 1.0},
    },
}


class SceneReader:
    """Game scene understanding engine.

    Reads zone positions, detects squad member locations, and
    identifies loot tiers from visual data.
    """

    # ------------------------------------------------------------------
    # Zone position reading
    # ------------------------------------------------------------------

    def read_zone_position(
        self,
        title: str,
        position_data: dict[str, Any],
    ) -> ZonePositionRead:
        """Determine the player's zone position from visual position data.

        Expected data varies by title:
        - madden26: yard_line, possession (bool)
        - eafc26: x, y (pitch coordinates)
        - fortnite/warzone: minimap_x, minimap_y, storm_radius, storm_center_x, storm_center_y
        """
        zone_config = _ZONE_TYPES.get(title, {"zones": ["unknown"]})
        zone = "unknown"
        details: dict[str, Any] = {}

        if title == "madden26":
            yard_line = position_data.get("yard_line", 50)
            possession = position_data.get("possession", True)
            if possession:
                if yard_line <= 20:
                    zone = "red_zone"
                elif yard_line <= 50:
                    zone = "midfield"
                else:
                    zone = "backed_up"
            else:
                if yard_line <= 20:
                    zone = "scoring_position"
                else:
                    zone = "neutral"
            details = {"yard_line": yard_line, "possession": possession}

        elif title == "eafc26":
            x = position_data.get("x", 50)
            y = position_data.get("y", 50)
            if x > 66:
                zone = "attacking_third"
            elif x > 33:
                zone = "midfield"
            else:
                zone = "defensive_third"
            if y < 20 or y > 80:
                zone = "wide_area"
            if x > 85 and 20 <= y <= 80:
                zone = "box"
            details = {"x": x, "y": y}

        elif title in ("fortnite", "warzone"):
            mx = position_data.get("minimap_x", 50)
            my = position_data.get("minimap_y", 50)
            storm_r = position_data.get("storm_radius", 100)
            storm_cx = position_data.get("storm_center_x", 50)
            storm_cy = position_data.get("storm_center_y", 50)

            dist_to_center = ((mx - storm_cx) ** 2 + (my - storm_cy) ** 2) ** 0.5
            if dist_to_center < storm_r * 0.5:
                zone = "safe_zone" if title == "warzone" else "storm_safe"
            elif dist_to_center < storm_r:
                zone = "edge_zone" if title == "warzone" else "storm_edge"
            else:
                zone = "gas" if title == "warzone" else "storm_inside"

            elevation = position_data.get("elevation", 0)
            if elevation > 50 and title == "fortnite":
                zone = "high_ground"
            details = {"distance_to_center": round(dist_to_center, 1), "storm_radius": storm_r}

        advice: list[str] = []
        if zone in ("red_zone", "box", "attacking_third"):
            advice.append("In scoring position — capitalize with high-percentage plays.")
        elif zone in ("backed_up", "defensive_third"):
            advice.append("Deep in own territory — play safe, avoid turnovers.")
        elif zone in ("storm_edge", "edge_zone"):
            advice.append("Near the zone edge — plan your rotation now.")
        elif zone in ("storm_inside", "gas"):
            advice.append("OUTSIDE THE ZONE — rotate immediately or you will die to storm/gas.")

        return ZonePositionRead(
            title=title,
            zone=zone,
            available_zones=zone_config.get("zones", []),
            details=details,
            advice=advice,
        )

    # ------------------------------------------------------------------
    # Squad location detection
    # ------------------------------------------------------------------

    def detect_squad_locations(
        self,
        player_markers: list[dict[str, Any]],
        title: str = "warzone",
    ) -> SquadLocation:
        """Detect squad member positions from minimap or HUD markers.

        Each marker: player_id, x, y, health, alive (bool).
        """
        alive = [m for m in player_markers if m.get("alive", True)]
        downed = [m for m in player_markers if not m.get("alive", True)]

        # Calculate squad spread (max distance between any two alive members)
        max_spread = 0.0
        for i, a in enumerate(alive):
            for b in alive[i + 1:]:
                dist = ((a.get("x", 0) - b.get("x", 0)) ** 2 +
                        (a.get("y", 0) - b.get("y", 0)) ** 2) ** 0.5
                max_spread = max(max_spread, dist)

        # Average position (centroid)
        if alive:
            avg_x = sum(m.get("x", 0) for m in alive) / len(alive)
            avg_y = sum(m.get("y", 0) for m in alive) / len(alive)
        else:
            avg_x, avg_y = 0.0, 0.0

        spread_rating = "tight" if max_spread < 15 else (
            "moderate" if max_spread < 40 else "spread_out"
        )

        advice: list[str] = []
        if spread_rating == "spread_out":
            advice.append("Squad is too spread out — regroup before engaging.")
        if downed:
            advice.append(f"{len(downed)} teammate(s) down — prioritize revive if safe.")
        low_health = [m for m in alive if m.get("health", 100) < 40]
        if low_health:
            advice.append(f"{len(low_health)} teammate(s) low health — find cover and heal.")

        return SquadLocation(
            title=title,
            alive_count=len(alive),
            downed_count=len(downed),
            centroid_x=round(avg_x, 1),
            centroid_y=round(avg_y, 1),
            max_spread=round(max_spread, 1),
            spread_rating=spread_rating,
            members=[{
                "player_id": m.get("player_id", "unknown"),
                "x": m.get("x", 0), "y": m.get("y", 0),
                "health": m.get("health", 100),
                "alive": m.get("alive", True),
            } for m in player_markers],
            advice=advice,
        )

    # ------------------------------------------------------------------
    # Loot tier identification
    # ------------------------------------------------------------------

    def identify_loot_tier(
        self,
        detected_color: str,
        title: str = "fortnite",
        item_name: str | None = None,
    ) -> LootTierDetection:
        """Identify loot tier from detected color/visual cues.

        Maps detected colors to game-specific rarity tiers.
        """
        tiers = _LOOT_TIERS.get(title, {})
        matched_tier: str | None = None
        tier_data: dict[str, Any] = {}

        for tier_name, data in tiers.items():
            if data.get("color", "").lower() == detected_color.lower():
                matched_tier = tier_name
                tier_data = data
                break

        if not matched_tier:
            # Fuzzy match on color
            color_map = {
                "gray": "common", "white": "common", "green": "uncommon",
                "blue": "rare", "purple": "epic", "gold": "legendary",
                "orange": "legendary", "gold_shimmer": "mythic",
            }
            matched_tier = color_map.get(detected_color.lower(), "unknown")
            tier_data = tiers.get(matched_tier, {})

        rarity = tier_data.get("rarity", 0)
        value = tier_data.get("value", 0.0)

        advice: list[str] = []
        if rarity >= 4:
            advice.append(f"Epic or higher — definitely pick this up.")
        elif rarity >= 3:
            advice.append("Rare tier — good upgrade if you need this slot.")
        elif rarity <= 1:
            advice.append("Common tier — skip unless you have nothing.")

        return LootTierDetection(
            title=title,
            detected_color=detected_color,
            tier=matched_tier or "unknown",
            rarity=rarity,
            value_score=round(value, 2),
            item_name=item_name,
            advice=advice,
        )


# Module-level singleton
scene_reader = SceneReader()
