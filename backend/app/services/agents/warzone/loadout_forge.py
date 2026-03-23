"""LoadoutForge — weekly meta weapon tier list, loadout optimizer, attachment trade-off calculator.

Provides loadout intelligence for Warzone by analyzing weapon meta,
optimizing builds per playstyle, and evaluating attachment trade-offs.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.warzone.combat import (
    AttachmentTradeOff,
    EngagementRange,
    LoadoutBuild,
    LoadoutOptimizeRequest,
    LoadoutOptimizeResponse,
    MovementStyle,
    WeaponClass,
    WeaponMeta,
    WeaponTier,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Weapon database (simulated meta snapshot)
# ---------------------------------------------------------------------------

_WEAPON_DB: list[dict[str, Any]] = [
    {
        "name": "MCW", "class": WeaponClass.ASSAULT_RIFLE, "tier": WeaponTier.S,
        "pick_rate": 0.18, "win_rate": 0.54, "ttk_ms": 620,
        "range": EngagementRange.MEDIUM, "trend": "stable",
        "strengths": ["Low recoil", "Versatile range", "Fast ADS"],
        "weaknesses": ["Average mobility", "Weak hipfire"],
    },
    {
        "name": "SVA 545", "class": WeaponClass.ASSAULT_RIFLE, "tier": WeaponTier.S,
        "pick_rate": 0.15, "win_rate": 0.52, "ttk_ms": 600,
        "range": EngagementRange.MEDIUM, "trend": "buffed",
        "strengths": ["Fastest AR TTK", "Good iron sights", "Controllable burst"],
        "weaknesses": ["Burst delay punishes misses", "Steep learning curve"],
    },
    {
        "name": "Holger 556", "class": WeaponClass.ASSAULT_RIFLE, "tier": WeaponTier.A,
        "pick_rate": 0.10, "win_rate": 0.50, "ttk_ms": 650,
        "range": EngagementRange.LONG, "trend": "stable",
        "strengths": ["Excellent range", "Large magazine option", "Predictable recoil"],
        "weaknesses": ["Slow ADS", "Below-average mobility"],
    },
    {
        "name": "Striker", "class": WeaponClass.SMG, "tier": WeaponTier.S,
        "pick_rate": 0.20, "win_rate": 0.55, "ttk_ms": 540,
        "range": EngagementRange.SHORT, "trend": "stable",
        "strengths": ["Best CQB TTK", "Great mobility", "Reliable hipfire"],
        "weaknesses": ["Falls off at range", "High vertical recoil"],
    },
    {
        "name": "HRM-9", "class": WeaponClass.SMG, "tier": WeaponTier.A,
        "pick_rate": 0.12, "win_rate": 0.51, "ttk_ms": 560,
        "range": EngagementRange.SHORT, "trend": "nerfed",
        "strengths": ["Fast fire rate", "Good hipfire", "Lightweight"],
        "weaknesses": ["Recent nerf to range", "Small mag"],
    },
    {
        "name": "Superi 46", "class": WeaponClass.SMG, "tier": WeaponTier.A,
        "pick_rate": 0.08, "win_rate": 0.49, "ttk_ms": 580,
        "range": EngagementRange.CQB, "trend": "stable",
        "strengths": ["Excellent mobility", "Fast sprint-to-fire", "Good hipfire"],
        "weaknesses": ["Very short effective range", "Low damage per bullet"],
    },
    {
        "name": "KATT-AMR", "class": WeaponClass.SNIPER, "tier": WeaponTier.A,
        "pick_rate": 0.06, "win_rate": 0.48, "ttk_ms": 0,
        "range": EngagementRange.EXTREME, "trend": "stable",
        "strengths": ["One-shot headshot", "Best bullet velocity", "Long range dominance"],
        "weaknesses": ["Slow rechamber", "Punishing if missed", "No close range"],
    },
    {
        "name": "Pulemyot 762", "class": WeaponClass.LMG, "tier": WeaponTier.B,
        "pick_rate": 0.04, "win_rate": 0.47, "ttk_ms": 640,
        "range": EngagementRange.LONG, "trend": "stable",
        "strengths": ["Huge magazine", "Sustained fire", "Wall penetration"],
        "weaknesses": ["Extremely slow ADS", "Poor mobility", "Long reload"],
    },
    {
        "name": "Lockwood 680", "class": WeaponClass.SHOTGUN, "tier": WeaponTier.C,
        "pick_rate": 0.02, "win_rate": 0.42, "ttk_ms": 200,
        "range": EngagementRange.CQB, "trend": "stable",
        "strengths": ["One-shot potential CQB", "Simple mechanics"],
        "weaknesses": ["Useless past 10m", "Slow pump action", "Niche pick"],
    },
    {
        "name": "MCW 6.8", "class": WeaponClass.MARKSMAN, "tier": WeaponTier.B,
        "pick_rate": 0.03, "win_rate": 0.46, "ttk_ms": 500,
        "range": EngagementRange.LONG, "trend": "buffed",
        "strengths": ["High damage per shot", "Good at range", "Low recoil"],
        "weaknesses": ["Semi-auto limits CQB", "Punishes missed shots"],
    },
]

# Attachment templates per weapon class
_ATTACHMENT_TEMPLATES: dict[WeaponClass, list[dict[str, Any]]] = {
    WeaponClass.ASSAULT_RIFLE: [
        {"slot": "muzzle", "recommended": "VT-7 Spiritfire Suppressor", "alt": "Casus Brake",
         "pros": ["Sound suppression", "Recoil control"], "cons": ["ADS penalty"],
         "stats": {"recoil_control": 8, "ads_speed": -3}},
        {"slot": "barrel", "recommended": "Perdition Long Barrel", "alt": "Dovetail Barrel",
         "pros": ["Range extension", "Bullet velocity"], "cons": ["Mobility loss"],
         "stats": {"range": 12, "mobility": -5}},
        {"slot": "underbarrel", "recommended": "Bruen Heavy Support Grip", "alt": "FTAC SP-10 Angled",
         "pros": ["Recoil stabilization"], "cons": ["Slight ADS penalty"],
         "stats": {"recoil_control": 10, "ads_speed": -2}},
        {"slot": "magazine", "recommended": "60 Round Drum", "alt": "45 Round Mag",
         "pros": ["Extended capacity"], "cons": ["Reload time", "Mobility"],
         "stats": {"mag_size": 20, "reload_speed": -8, "mobility": -3}},
        {"slot": "optic", "recommended": "Corio Eagleseye 2.5x", "alt": "MK.3 Reflector",
         "pros": ["Clean sight picture"], "cons": ["ADS penalty on higher zoom"],
         "stats": {"accuracy": 5, "ads_speed": -2}},
    ],
    WeaponClass.SMG: [
        {"slot": "muzzle", "recommended": "ZEHMN35 Compensated Flash Hider", "alt": "Bruen Pendulum",
         "pros": ["Flash concealment", "Vertical recoil"], "cons": ["Minor range loss"],
         "stats": {"recoil_control": 6, "range": -2}},
        {"slot": "barrel", "recommended": "Short Barrel", "alt": "Thorn-90 Barrel",
         "pros": ["ADS speed", "Sprint-to-fire"], "cons": ["Range reduction"],
         "stats": {"ads_speed": 8, "range": -6}},
        {"slot": "stock", "recommended": "Lachmann MK2 Light Stock", "alt": "No Stock",
         "pros": ["Movement speed", "ADS speed"], "cons": ["Recoil increase"],
         "stats": {"mobility": 10, "recoil_control": -4}},
        {"slot": "rear_grip", "recommended": "Phantom Grip", "alt": "Demo Cleanshot Grip",
         "pros": ["ADS speed", "Sprint-to-fire"], "cons": ["Recoil penalty"],
         "stats": {"ads_speed": 6, "recoil_control": -3}},
        {"slot": "magazine", "recommended": "50 Round Drum", "alt": "40 Round Mag",
         "pros": ["Extended fights"], "cons": ["Mobility penalty"],
         "stats": {"mag_size": 20, "mobility": -4}},
    ],
    WeaponClass.SNIPER: [
        {"slot": "muzzle", "recommended": "Nilsound 90", "alt": "VT-7 Spiritfire Suppressor",
         "pros": ["Sound suppression"], "cons": ["ADS speed"],
         "stats": {"stealth": 10, "ads_speed": -5}},
        {"slot": "barrel", "recommended": "Perdition 24\" Long Barrel", "alt": "KR Sightline Barrel",
         "pros": ["Bullet velocity", "Range"], "cons": ["Handling speed"],
         "stats": {"bullet_velocity": 15, "ads_speed": -6}},
        {"slot": "optic", "recommended": "SP-X 80 6.6x", "alt": "Forge Tac Delta 4",
         "pros": ["Clear magnification"], "cons": ["Glint visible"],
         "stats": {"accuracy": 8, "stealth": -5}},
        {"slot": "ammunition", "recommended": "High Velocity Rounds", "alt": "Explosive Rounds",
         "pros": ["Faster bullet travel"], "cons": ["No extra damage"],
         "stats": {"bullet_velocity": 12, "damage": 0}},
        {"slot": "rear_grip", "recommended": "Crux Response Grip", "alt": "Phantom Grip",
         "pros": ["ADS speed"], "cons": ["Stability loss"],
         "stats": {"ads_speed": 5, "stability": -3}},
    ],
}

# Playstyle -> preferred weapon classes
_PLAYSTYLE_PREFERENCES: dict[MovementStyle, list[WeaponClass]] = {
    MovementStyle.AGGRESSIVE: [WeaponClass.SMG, WeaponClass.SHOTGUN],
    MovementStyle.PASSIVE: [WeaponClass.ASSAULT_RIFLE, WeaponClass.LMG, WeaponClass.SNIPER],
    MovementStyle.BALANCED: [WeaponClass.ASSAULT_RIFLE, WeaponClass.SMG],
    MovementStyle.ROTATION_HEAVY: [WeaponClass.ASSAULT_RIFLE, WeaponClass.MARKSMAN],
    MovementStyle.EDGE_PLAYER: [WeaponClass.SNIPER, WeaponClass.MARKSMAN],
}

# Default perks
_PERK_PACKAGES: dict[MovementStyle, list[str]] = {
    MovementStyle.AGGRESSIVE: ["Double Time", "Sleight of Hand", "Tempered", "High Alert"],
    MovementStyle.PASSIVE: ["Mountaineer", "Bomb Squad", "Tempered", "Ghost"],
    MovementStyle.BALANCED: ["Double Time", "Bomb Squad", "Tempered", "Ghost"],
    MovementStyle.ROTATION_HEAVY: ["Double Time", "Tracker", "Tempered", "Ghost"],
    MovementStyle.EDGE_PLAYER: ["Mountaineer", "Focus", "Tempered", "Ghost"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _weapon_to_meta(w: dict[str, Any]) -> WeaponMeta:
    """Convert internal weapon dict to WeaponMeta schema."""
    wclass = w["class"]
    attachments = _build_attachments(wclass)
    return WeaponMeta(
        weapon_name=w["name"],
        weapon_class=wclass,
        tier=w["tier"],
        pick_rate=w["pick_rate"],
        win_rate=w["win_rate"],
        ttk_ms=w["ttk_ms"],
        effective_range=w["range"],
        best_attachments=attachments,
        strengths=w.get("strengths", []),
        weaknesses=w.get("weaknesses", []),
        patch_trend=w.get("trend", "stable"),
    )


def _build_attachments(wclass: WeaponClass) -> list[AttachmentTradeOff]:
    """Build attachment trade-off list for a weapon class."""
    templates = _ATTACHMENT_TEMPLATES.get(wclass, [])
    return [
        AttachmentTradeOff(
            slot=t["slot"],
            recommended=t["recommended"],
            alternative=t.get("alt"),
            pros=t.get("pros", []),
            cons=t.get("cons", []),
            stat_changes=t.get("stats", {}),
        )
        for t in templates
    ]


# ---------------------------------------------------------------------------
# LoadoutForge
# ---------------------------------------------------------------------------

class LoadoutForge:
    """Warzone loadout optimization and weapon meta analysis engine."""

    # ------------------------------------------------------------------
    # get_meta_tier_list
    # ------------------------------------------------------------------

    def get_meta_tier_list(self) -> list[WeaponMeta]:
        """Return the current weapon meta tier list, sorted by tier then win rate."""
        tier_order = {WeaponTier.S: 0, WeaponTier.A: 1, WeaponTier.B: 2, WeaponTier.C: 3, WeaponTier.D: 4}
        weapons = [_weapon_to_meta(w) for w in _WEAPON_DB]
        return sorted(weapons, key=lambda w: (tier_order[w.tier], -w.win_rate))

    # ------------------------------------------------------------------
    # optimize_loadout
    # ------------------------------------------------------------------

    def optimize_loadout(self, request: LoadoutOptimizeRequest) -> LoadoutOptimizeResponse:
        """Build an optimized loadout based on playstyle and preferences.

        Selects primary + secondary weapons, perks, and equipment tailored
        to the player's engagement range and movement style.
        """
        preferred_classes = _PLAYSTYLE_PREFERENCES.get(
            request.playstyle, [WeaponClass.ASSAULT_RIFLE, WeaponClass.SMG]
        )

        # Filter to preferred class if specified
        if request.preferred_class:
            primary_pool = [w for w in _WEAPON_DB if w["class"] == request.preferred_class]
        else:
            primary_pool = [w for w in _WEAPON_DB if w["class"] in preferred_classes]

        if not primary_pool:
            primary_pool = [w for w in _WEAPON_DB if w["class"] == WeaponClass.ASSAULT_RIFLE]

        # Score weapons for the requested engagement range
        scored = []
        for w in primary_pool:
            score = w["win_rate"] * 50 + w["pick_rate"] * 30
            if w["range"] == request.engagement_range:
                score += 20
            if w["trend"] == "buffed":
                score += 5
            elif w["trend"] == "nerfed":
                score -= 5
            scored.append((score, w))

        scored.sort(key=lambda x: x[0], reverse=True)
        primary_weapon = scored[0][1] if scored else _WEAPON_DB[0]

        # Secondary: complement the primary range
        if primary_weapon["range"] in (EngagementRange.MEDIUM, EngagementRange.LONG, EngagementRange.EXTREME):
            secondary_pool = [w for w in _WEAPON_DB if w["class"] == WeaponClass.SMG]
        else:
            secondary_pool = [w for w in _WEAPON_DB if w["class"] == WeaponClass.ASSAULT_RIFLE]

        secondary_pool = [w for w in secondary_pool if w["name"] != primary_weapon["name"]]
        if not secondary_pool:
            secondary_pool = [w for w in _WEAPON_DB if w["name"] != primary_weapon["name"]]
        secondary_weapon = sorted(secondary_pool, key=lambda w: w["win_rate"], reverse=True)[0]

        primary_meta = _weapon_to_meta(primary_weapon)
        secondary_meta = _weapon_to_meta(secondary_weapon)

        perks = _PERK_PACKAGES.get(request.playstyle, _PERK_PACKAGES[MovementStyle.BALANCED])

        # Effectiveness: weighted average of primary/secondary win rates + playstyle fit
        base_score = (primary_meta.win_rate * 60 + secondary_meta.win_rate * 40)
        if primary_meta.effective_range == request.engagement_range:
            base_score += 10
        effectiveness = min(100.0, base_score)

        # Tactical/lethal based on playstyle
        if request.playstyle == MovementStyle.AGGRESSIVE:
            tactical, lethal = "stim", "semtex"
        elif request.playstyle == MovementStyle.PASSIVE:
            tactical, lethal = "heartbeat_sensor", "claymore"
        else:
            tactical, lethal = "stun_grenade", "semtex"

        loadout = LoadoutBuild(
            primary=primary_meta,
            secondary=secondary_meta,
            perks=perks,
            tactical=tactical,
            lethal=lethal,
            playstyle_fit=request.playstyle.value,
            effectiveness_score=round(effectiveness, 1),
        )

        # Build 2 alternatives with different primary picks
        alternatives: list[LoadoutBuild] = []
        for _, alt_weapon in scored[1:3]:
            alt_meta = _weapon_to_meta(alt_weapon)
            alt_score = (alt_meta.win_rate * 60 + secondary_meta.win_rate * 40)
            alternatives.append(LoadoutBuild(
                primary=alt_meta,
                secondary=secondary_meta,
                perks=perks,
                tactical=tactical,
                lethal=lethal,
                playstyle_fit=request.playstyle.value,
                effectiveness_score=round(min(100.0, alt_score), 1),
            ))

        tier_list = self.get_meta_tier_list()

        summary = (
            f"Recommended: {primary_meta.weapon_name} + {secondary_meta.weapon_name} "
            f"({effectiveness:.0f}/100 effectiveness). "
            f"Optimized for {request.playstyle.value} play at {request.engagement_range.value} range."
        )

        return LoadoutOptimizeResponse(
            recommended_loadout=loadout,
            alternatives=alternatives,
            meta_tier_list=tier_list,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # get_attachment_tradeoffs
    # ------------------------------------------------------------------

    def get_attachment_tradeoffs(self, weapon_class: WeaponClass) -> list[AttachmentTradeOff]:
        """Return attachment trade-off analysis for a weapon class."""
        return _build_attachments(weapon_class)

    # ------------------------------------------------------------------
    # compare_weapons
    # ------------------------------------------------------------------

    def compare_weapons(self, weapon_a: str, weapon_b: str) -> dict[str, Any]:
        """Head-to-head comparison of two weapons across key stats."""
        db_map = {w["name"].lower(): w for w in _WEAPON_DB}

        wa = db_map.get(weapon_a.lower())
        wb = db_map.get(weapon_b.lower())

        if not wa or not wb:
            missing = weapon_a if not wa else weapon_b
            return {"error": f"Weapon '{missing}' not found in database."}

        ttk_diff = wa["ttk_ms"] - wb["ttk_ms"]
        winner_ttk = wa["name"] if ttk_diff < 0 else wb["name"] if ttk_diff > 0 else "Tied"

        wr_diff = wa["win_rate"] - wb["win_rate"]
        winner_wr = wa["name"] if wr_diff > 0 else wb["name"] if wr_diff < 0 else "Tied"

        return {
            "weapon_a": _weapon_to_meta(wa).model_dump(),
            "weapon_b": _weapon_to_meta(wb).model_dump(),
            "ttk_advantage": winner_ttk,
            "ttk_delta_ms": abs(ttk_diff),
            "win_rate_advantage": winner_wr,
            "recommendation": (
                f"{winner_ttk} wins in raw TTK. {winner_wr} has a higher win rate. "
                f"Choose based on your engagement range preference."
            ),
        }
