"""WarzoneTwin — movement style, engagement tendency, clutch closing rates, loot efficiency.

Builds a digital twin profile of a Warzone player by analyzing match history
to classify playstyle, identify strengths/weaknesses, and provide coaching tips.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.warzone.combat import (
    ClutchProfile,
    EngagementRange,
    EngagementTendency,
    LootEfficiency,
    MovementStyle,
    WarzoneTwinProfile,
    WarzoneTwinRequest,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Grade thresholds for loot efficiency
_LOOT_GRADE_THRESHOLDS = [
    (95, "A+"), (90, "A"), (85, "A-"),
    (80, "B+"), (75, "B"), (70, "B-"),
    (65, "C+"), (60, "C"), (55, "C-"),
    (50, "D+"), (45, "D"), (40, "D-"),
    (0, "F"),
]

# Movement style classification thresholds
_MOVEMENT_THRESHOLDS = {
    "hot_drop_rate": 0.5,
    "avg_kills_high": 8.0,
    "avg_kills_low": 3.0,
    "avg_placement_campy": 15.0,
    "rotations_per_game_high": 4.0,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _score_to_grade(score: float) -> str:
    for threshold, grade in _LOOT_GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def _classify_movement(
    avg_kills: float,
    avg_placement: float,
    hot_drop_rate: float,
    rotations_per_game: float,
) -> MovementStyle:
    """Classify movement style based on aggregate stats."""
    if hot_drop_rate > 0.6 and avg_kills > _MOVEMENT_THRESHOLDS["avg_kills_high"]:
        return MovementStyle.AGGRESSIVE
    if avg_placement < _MOVEMENT_THRESHOLDS["avg_placement_campy"] and avg_kills < _MOVEMENT_THRESHOLDS["avg_kills_low"]:
        return MovementStyle.PASSIVE
    if rotations_per_game > _MOVEMENT_THRESHOLDS["rotations_per_game_high"]:
        return MovementStyle.ROTATION_HEAVY
    if avg_placement < 20 and hot_drop_rate < 0.3:
        return MovementStyle.EDGE_PLAYER
    return MovementStyle.BALANCED


def _classify_engagement(
    first_shot_rate: float,
    avg_engagement_distance: float,
    fight_initiation_rate: float,
) -> EngagementTendency:
    """Classify how a player typically enters fights."""
    if fight_initiation_rate > 0.6 and first_shot_rate > 0.55:
        return EngagementTendency.FIRST_MOVER
    if fight_initiation_rate < 0.3:
        return EngagementTendency.AVOIDANT
    if first_shot_rate < 0.4:
        return EngagementTendency.REACTIVE
    return EngagementTendency.OPPORTUNISTIC


def _extract_match_stats(match_history: list[dict[str, Any]]) -> dict[str, float]:
    """Extract aggregate statistics from raw match data.

    Expected match dict keys: kills, deaths, damage, placement,
    loot_time_seconds, cash_earned, loadout_acquired (bool),
    rotations, hot_drop (bool), first_shot_taken (bool),
    fight_initiated (bool), avg_engagement_distance_m,
    clutch_kills, clutch_rounds.
    """
    if not match_history:
        return {
            "avg_kills": 0.0,
            "avg_deaths": 0.0,
            "avg_damage": 0.0,
            "avg_placement": 50.0,
            "kd_ratio": 0.0,
            "hot_drop_rate": 0.0,
            "avg_loot_time": 120.0,
            "loadout_rate": 0.0,
            "cash_per_minute": 0.0,
            "avg_rotations": 0.0,
            "first_shot_rate": 0.5,
            "fight_init_rate": 0.5,
            "avg_engagement_dist": 30.0,
            "clutch_rate": 0.0,
            "avg_clutch_kills": 0.0,
        }

    n = len(match_history)
    total_kills = sum(m.get("kills", 0) for m in match_history)
    total_deaths = sum(m.get("deaths", 0) for m in match_history)
    total_damage = sum(m.get("damage", 0) for m in match_history)
    total_placement = sum(m.get("placement", 50) for m in match_history)
    total_loot_time = sum(m.get("loot_time_seconds", 120) for m in match_history)
    total_cash = sum(m.get("cash_earned", 0) for m in match_history)
    loadouts_acquired = sum(1 for m in match_history if m.get("loadout_acquired", False))
    hot_drops = sum(1 for m in match_history if m.get("hot_drop", False))
    total_rotations = sum(m.get("rotations", 0) for m in match_history)
    first_shots = sum(1 for m in match_history if m.get("first_shot_taken", False))
    fights_initiated = sum(1 for m in match_history if m.get("fight_initiated", False))
    avg_eng_dist = sum(m.get("avg_engagement_distance_m", 30) for m in match_history) / n
    clutch_kills = sum(m.get("clutch_kills", 0) for m in match_history)
    clutch_rounds = sum(m.get("clutch_rounds", 0) for m in match_history)

    kd = total_kills / max(total_deaths, 1)

    # Loot efficiency score: normalized combination of speed and economy
    avg_loot = total_loot_time / n
    loot_speed_score = max(0, 100 - avg_loot / 1.5)  # Lower is better
    loadout_score = (loadouts_acquired / n) * 50
    cash_score = min(50, (total_cash / n) / 20)
    loot_eff_score = min(100, loot_speed_score * 0.4 + loadout_score * 0.4 + cash_score * 0.2)

    return {
        "avg_kills": total_kills / n,
        "avg_deaths": total_deaths / n,
        "avg_damage": total_damage / n,
        "avg_placement": total_placement / n,
        "kd_ratio": round(kd, 2),
        "hot_drop_rate": hot_drops / n,
        "avg_loot_time": avg_loot,
        "loadout_rate": loadouts_acquired / n,
        "cash_per_minute": (total_cash / n) / max(avg_loot / 60, 1),
        "avg_rotations": total_rotations / n,
        "first_shot_rate": first_shots / n,
        "fight_init_rate": fights_initiated / n,
        "avg_engagement_dist": avg_eng_dist,
        "clutch_rate": clutch_kills / max(clutch_rounds, 1),
        "avg_clutch_kills": clutch_kills / max(n, 1),
        "loot_eff_score": loot_eff_score,
    }


def _identify_strengths_weaknesses(stats: dict[str, float]) -> tuple[list[str], list[str]]:
    """Identify player strengths and weaknesses from aggregated stats."""
    strengths: list[str] = []
    weaknesses: list[str] = []

    if stats["kd_ratio"] >= 2.0:
        strengths.append(f"Elite K/D ratio ({stats['kd_ratio']:.2f})")
    elif stats["kd_ratio"] < 1.0:
        weaknesses.append(f"Below-average K/D ({stats['kd_ratio']:.2f}) — dying too frequently")

    if stats["avg_damage"] >= 1500:
        strengths.append(f"High damage output ({stats['avg_damage']:.0f} avg)")
    elif stats["avg_damage"] < 500:
        weaknesses.append(f"Low damage ({stats['avg_damage']:.0f} avg) — not finding enough fights")

    if stats["avg_placement"] <= 10:
        strengths.append(f"Consistent top-10 finisher (avg #{stats['avg_placement']:.0f})")
    elif stats["avg_placement"] > 40:
        weaknesses.append(f"Poor placement (avg #{stats['avg_placement']:.0f}) — dying early")

    if stats["clutch_rate"] >= 0.4:
        strengths.append(f"Clutch performer ({stats['clutch_rate']:.0%} clutch rate)")
    elif stats["clutch_rate"] < 0.15:
        weaknesses.append(f"Struggles in clutch situations ({stats['clutch_rate']:.0%})")

    if stats["loadout_rate"] >= 0.85:
        strengths.append("Efficient looting — almost always gets loadout")
    elif stats["loadout_rate"] < 0.5:
        weaknesses.append("Poor loot pathing — missing loadout drops too often")

    return strengths, weaknesses


def _generate_coaching_tips(
    stats: dict[str, float],
    movement: MovementStyle,
    engagement: EngagementTendency,
) -> list[str]:
    """Generate personalized coaching tips."""
    tips: list[str] = []

    if stats["kd_ratio"] < 1.0:
        tips.append("Focus on positioning over aggression — pick fights you can win.")
    if stats["avg_placement"] > 30:
        tips.append("Practice rotation timing — use ZoneForge predictions to move early.")
    if stats["clutch_rate"] < 0.2:
        tips.append("Run GunfightAI drills to improve 1vN composure and accuracy.")
    if movement == MovementStyle.PASSIVE:
        tips.append("Try increasing engagement frequency — passive play caps your ceiling.")
    if engagement == EngagementTendency.AVOIDANT:
        tips.append("Practice taking more fights mid-game to build confidence.")
    if stats["loadout_rate"] < 0.6:
        tips.append("Optimize your early-game loot path — prioritize cash for loadout.")
    if stats["first_shot_rate"] < 0.4:
        tips.append("Work on crosshair placement — you're getting shot first too often.")
    if not tips:
        tips.append("Strong overall performance — focus on late-game execution and zone control.")

    return tips[:5]


# ---------------------------------------------------------------------------
# WarzoneTwin
# ---------------------------------------------------------------------------

class WarzoneTwin:
    """Digital twin builder for Warzone players."""

    # ------------------------------------------------------------------
    # build_profile
    # ------------------------------------------------------------------

    def build_profile(self, request: WarzoneTwinRequest) -> WarzoneTwinProfile:
        """Build a complete digital twin from match history.

        Analyzes movement patterns, engagement habits, clutch performance,
        loot efficiency, and generates coaching recommendations.
        """
        stats = _extract_match_stats(request.match_history)

        movement = _classify_movement(
            avg_kills=stats["avg_kills"],
            avg_placement=stats["avg_placement"],
            hot_drop_rate=stats["hot_drop_rate"],
            rotations_per_game=stats["avg_rotations"],
        )

        engagement = _classify_engagement(
            first_shot_rate=stats["first_shot_rate"],
            avg_engagement_distance=stats["avg_engagement_dist"],
            fight_initiation_rate=stats["fight_init_rate"],
        )

        # Determine best clutch range from engagement distance
        avg_dist = stats["avg_engagement_dist"]
        if avg_dist < 10:
            best_clutch_range = EngagementRange.CQB
        elif avg_dist < 25:
            best_clutch_range = EngagementRange.SHORT
        elif avg_dist < 50:
            best_clutch_range = EngagementRange.MEDIUM
        elif avg_dist < 100:
            best_clutch_range = EngagementRange.LONG
        else:
            best_clutch_range = EngagementRange.EXTREME

        clutch = ClutchProfile(
            clutch_rate=stats["clutch_rate"],
            avg_kills_in_clutch=stats["avg_clutch_kills"],
            composure_rating=round(min(10.0, stats["clutch_rate"] * 10 + stats["kd_ratio"]), 1),
            best_clutch_range=best_clutch_range,
        )

        loot_eff_score = stats.get("loot_eff_score", 50.0)
        loot = LootEfficiency(
            avg_loot_time_seconds=stats["avg_loot_time"],
            loadout_acquisition_rate=stats["loadout_rate"],
            cash_per_minute=round(stats["cash_per_minute"], 1),
            efficiency_grade=_score_to_grade(loot_eff_score),
        )

        # Extract preferred weapons from match data
        weapon_counts: dict[str, int] = {}
        for match in request.match_history:
            for w in match.get("weapons_used", []):
                weapon_counts[w] = weapon_counts.get(w, 0) + 1
        preferred_weapons = sorted(weapon_counts, key=weapon_counts.get, reverse=True)[:3]

        strengths, weaknesses = _identify_strengths_weaknesses(stats)
        coaching = _generate_coaching_tips(stats, movement, engagement)

        summary = (
            f"{request.gamertag}: {movement.value} {engagement.value} player. "
            f"K/D: {stats['kd_ratio']:.2f}, Avg placement: #{stats['avg_placement']:.0f}. "
            f"Clutch rate: {stats['clutch_rate']:.0%}. "
            f"Loot grade: {loot.efficiency_grade}. "
            f"{len(strengths)} strength(s), {len(weaknesses)} area(s) to improve."
        )

        return WarzoneTwinProfile(
            player_id=request.player_id,
            gamertag=request.gamertag,
            movement_style=movement,
            engagement_tendency=engagement,
            clutch_profile=clutch,
            loot_efficiency=loot,
            avg_placement=round(stats["avg_placement"], 1),
            avg_kills=round(stats["avg_kills"], 1),
            kd_ratio=stats["kd_ratio"],
            preferred_weapons=preferred_weapons,
            hot_drop_rate=round(stats["hot_drop_rate"], 2),
            strengths=strengths,
            weaknesses=weaknesses,
            coaching_tips=coaching,
            summary=summary,
        )
