"""ArchetypeAI — Opponent archetype classification and counter strategies.

Clusters opponents into archetypes even with minimal data, provides
counter packages, and refines classifications mid-game as new signals arrive.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.schemas.opponent import (
    Archetype,
    ArchetypeLabel,
    CounterPackage,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Archetype library — title-agnostic base definitions
# ---------------------------------------------------------------------------

_ARCHETYPE_DEFINITIONS: dict[ArchetypeLabel, dict[str, Any]] = {
    ArchetypeLabel.AGGRESSOR: {
        "traits": ["high tempo", "risk-taking", "blitz-heavy", "deep shots"],
        "description": "Relentless attacker who pressures early and often.",
    },
    ArchetypeLabel.TURTLE: {
        "traits": ["conservative", "clock-management", "run-heavy", "bend-don't-break"],
        "description": "Patient defender who minimises mistakes and grinds you down.",
    },
    ArchetypeLabel.COUNTER_PUNCHER: {
        "traits": ["reactive", "exploit-mistakes", "big-play-hunter", "patient"],
        "description": "Waits for your errors then strikes with explosive plays.",
    },
    ArchetypeLabel.CHAOS_AGENT: {
        "traits": ["unpredictable", "trick-plays", "no-huddle", "high-variance"],
        "description": "Maximises randomness to prevent opponents from reading them.",
    },
    ArchetypeLabel.META_SLAVE: {
        "traits": ["meta-optimal", "scheme-heavy", "community-plays", "predictable"],
        "description": "Runs the established meta playbook with high efficiency.",
    },
    ArchetypeLabel.ADAPTIVE: {
        "traits": ["flexible", "counter-adjusting", "game-plan-shifts", "reads-opponent"],
        "description": "Adjusts strategy dynamically based on what the opponent shows.",
    },
    ArchetypeLabel.ONE_TRICK: {
        "traits": ["repetitive", "one-scheme", "comfort-zone", "narrow-playbook"],
        "description": "Leans heavily on a single scheme or small set of plays.",
    },
}

_COUNTER_PACKAGES: dict[ArchetypeLabel, dict[str, Any]] = {
    ArchetypeLabel.AGGRESSOR: {
        "strategies": [
            "Slow the pace — use clock and short passes",
            "Punish over-aggression with screens and draws",
            "Force them into long drives",
        ],
        "key_adjustments": ["Max protect against blitz", "Quick-release passing game"],
        "plays_to_exploit": ["HB Screen", "Slant routes", "Draw plays"],
        "mental_notes": ["They tilt when the game slows down", "Bait the blitz"],
    },
    ArchetypeLabel.TURTLE: {
        "strategies": [
            "Force them out of their comfort zone with tempo",
            "Attack the secondary with vertical shots",
            "Go for it on 4th down in their territory",
        ],
        "key_adjustments": ["Spread formations", "Aggressive play-calling"],
        "plays_to_exploit": ["4-Verts", "Deep crossers", "Play-action bombs"],
        "mental_notes": ["They panic when forced to play from behind"],
    },
    ArchetypeLabel.COUNTER_PUNCHER: {
        "strategies": [
            "Limit turnovers — conservative but efficient",
            "Control possession and field position",
            "Don't give them explosive play opportunities",
        ],
        "key_adjustments": ["Ball security emphasis", "Underneath routes"],
        "plays_to_exploit": ["Mesh concepts", "RPOs", "Zone runs"],
        "mental_notes": ["Starve them of big plays and they get impatient"],
    },
    ArchetypeLabel.CHAOS_AGENT: {
        "strategies": [
            "Stay disciplined — don't chase the shiny object",
            "Assign gap integrity, contain the edges",
            "Stick to your game plan regardless of their tricks",
        ],
        "key_adjustments": ["Conservative defense", "Spy mobile QBs"],
        "plays_to_exploit": ["Base defense with spy", "Zone coverage"],
        "mental_notes": ["Chaos agents beat themselves if you stay patient"],
    },
    ArchetypeLabel.META_SLAVE: {
        "strategies": [
            "Study the current meta counters and apply them",
            "Force off-script situations",
            "Attack their secondary reads",
        ],
        "key_adjustments": ["Anti-meta adjustments", "Disguise coverages"],
        "plays_to_exploit": ["Meta-counter schemes", "Uncommon formations"],
        "mental_notes": ["They struggle when the meta counter is applied correctly"],
    },
    ArchetypeLabel.ADAPTIVE: {
        "strategies": [
            "Change your own look frequently",
            "Don't reveal your full playbook early",
            "Win the adjustment battle with deeper counters",
        ],
        "key_adjustments": ["Multiple scheme packages", "In-game audibles"],
        "plays_to_exploit": ["Diverse playbook", "Constraint plays"],
        "mental_notes": ["Hardest archetype — outprepare with deeper schemes"],
    },
    ArchetypeLabel.ONE_TRICK: {
        "strategies": [
            "Identify their one trick quickly and hard-counter it",
            "Force them into their weak hand",
            "Double-team their comfort route/concept",
        ],
        "key_adjustments": ["Overload their primary concept", "Take away #1 option"],
        "plays_to_exploit": ["Bracket coverage on key route", "Run-fit adjustments"],
        "mental_notes": ["Once you remove their trick they have nothing"],
    },
}


# ---------------------------------------------------------------------------
# Trait-matching heuristic
# ---------------------------------------------------------------------------

def _match_traits(signals: list[str], archetype_traits: list[str]) -> float:
    """Score 0-1 how well *signals* match *archetype_traits*."""
    if not signals or not archetype_traits:
        return 0.0
    signal_set = {s.lower() for s in signals}
    trait_set = {t.lower() for t in archetype_traits}
    overlap = signal_set & trait_set
    return len(overlap) / max(len(trait_set), 1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_opponent(limited_data: dict[str, Any]) -> Archetype:
    """Classify an opponent into an archetype, even with minimal history.

    ``limited_data`` should contain at least ``signals`` (list of trait
    strings) and optionally ``title``.  With zero useful signals the
    archetype defaults to UNKNOWN.
    """
    signals: list[str] = limited_data.get("signals", [])
    title: str = limited_data.get("title", "")

    if not signals:
        return Archetype(label=ArchetypeLabel.UNKNOWN, confidence=0.0, title=title)

    best_label = ArchetypeLabel.UNKNOWN
    best_score = 0.0

    for label, definition in _ARCHETYPE_DEFINITIONS.items():
        score = _match_traits(signals, definition["traits"])
        if score > best_score:
            best_score = score
            best_label = label

    if best_score < 0.15:
        return Archetype(label=ArchetypeLabel.UNKNOWN, confidence=round(best_score, 3), title=title)

    defn = _ARCHETYPE_DEFINITIONS[best_label]
    return Archetype(
        label=best_label,
        confidence=round(min(1.0, best_score), 3),
        traits=defn["traits"],
        description=defn["description"],
        title=title,
    )


def get_counter_package(archetype: Archetype) -> CounterPackage:
    """Return a full counter strategy package for the given archetype."""
    pkg = _COUNTER_PACKAGES.get(archetype.label)
    if pkg is None:
        return CounterPackage(
            target_archetype=archetype.label,
            strategies=["Gather more data before committing to a counter plan."],
            confidence=0.0,
        )

    return CounterPackage(
        target_archetype=archetype.label,
        strategies=pkg["strategies"],
        key_adjustments=pkg["key_adjustments"],
        plays_to_exploit=pkg["plays_to_exploit"],
        mental_notes=pkg["mental_notes"],
        confidence=archetype.confidence,
    )


def update_mid_game(archetype: Archetype, new_signals: list[str]) -> Archetype:
    """Refine an archetype classification as the opponent reveals more.

    Merges *new_signals* with the current trait set and re-classifies.
    """
    merged_signals = list(set(archetype.traits + new_signals))
    data = {"signals": merged_signals, "title": archetype.title}
    updated = classify_opponent(data)
    updated.updated_at = datetime.utcnow()
    return updated


def get_archetype_library(title: str) -> list[Archetype]:
    """Return all known archetypes for a given title.

    Currently title-agnostic; returns the full base library with
    title metadata attached.
    """
    archetypes: list[Archetype] = []
    for label, defn in _ARCHETYPE_DEFINITIONS.items():
        archetypes.append(
            Archetype(
                label=label,
                confidence=1.0,
                traits=defn["traits"],
                description=defn["description"],
                title=title,
            )
        )
    return archetypes
