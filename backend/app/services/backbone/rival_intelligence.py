"""Rival Intelligence System — Deep dossiers for repeat opponents.

Tracks head-to-head history, auto-detects rival status after 2+ matchups,
maintains a kill sheet of effective/ineffective strategies, and deepens
the dossier after every encounter.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.schemas.opponent import (
    EncounterRecord,
    KillSheet,
    RivalDossier,
    Tendency,
    TendencyType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory store (will be replaced with DB)
# ---------------------------------------------------------------------------

# Key: "{user_id}:{opponent_id}"
_rival_store: dict[str, RivalDossier] = {}


def _key(user_id: str, opponent_id: str) -> str:
    return f"{user_id}:{opponent_id}"


def _reset_store() -> None:
    """Clear the store (test helper)."""
    _rival_store.clear()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

RIVAL_THRESHOLD = 2  # encounters needed to trigger rival status


def get_rival_dossier(user_id: str, opponent_id: str) -> RivalDossier:
    """Return the deep dossier for *user_id* vs *opponent_id*.

    If no dossier exists yet, returns a fresh (empty) one.
    """
    k = _key(user_id, opponent_id)
    if k in _rival_store:
        return _rival_store[k]

    dossier = RivalDossier(user_id=user_id, opponent_id=opponent_id)
    _rival_store[k] = dossier
    return dossier


def deepen_dossier(dossier: RivalDossier, new_encounter: dict[str, Any]) -> RivalDossier:
    """Deepen an existing dossier with a new encounter.

    Parameters
    ----------
    new_encounter:
        ``{"game_id", "result", "score", "key_moments", "opponent_adjustments",
          "effective_strategies", "ineffective_strategies"}``
    """
    record = EncounterRecord(
        game_id=new_encounter.get("game_id", ""),
        result=new_encounter.get("result", "unknown"),
        score=new_encounter.get("score", ""),
        key_moments=new_encounter.get("key_moments", []),
        opponent_adjustments=new_encounter.get("opponent_adjustments", []),
    )

    dossier.encounters.append(record)
    dossier.encounter_count = len(dossier.encounters)
    dossier.last_encountered = record.timestamp

    # Update head-to-head record
    if record.result == "win":
        dossier.head_to_head["wins"] = dossier.head_to_head.get("wins", 0) + 1
    elif record.result == "loss":
        dossier.head_to_head["losses"] = dossier.head_to_head.get("losses", 0) + 1
    else:
        dossier.head_to_head["draws"] = dossier.head_to_head.get("draws", 0) + 1

    # Check rival status
    dossier.is_rival = dossier.encounter_count >= RIVAL_THRESHOLD

    # Update kill sheet with new intel
    ks = dossier.kill_sheet
    for strat in new_encounter.get("effective_strategies", []):
        if strat not in ks.effective_strategies:
            ks.effective_strategies.append(strat)
    for strat in new_encounter.get("ineffective_strategies", []):
        if strat not in ks.ineffective_strategies:
            ks.ineffective_strategies.append(strat)
    ks.last_updated = datetime.utcnow()

    # Update threat trend
    dossier.threat_trend = _compute_threat_trend(dossier)

    # Persist
    k = _key(dossier.user_id, dossier.opponent_id)
    _rival_store[k] = dossier

    return dossier


def auto_update_kill_sheet(rival_id: str, user_id: str = "") -> KillSheet | None:
    """Auto-update the kill sheet for a rival based on accumulated encounters.

    Scans all encounters for patterns of success / failure and consolidates
    the kill sheet.  If *user_id* is empty, searches all dossiers for
    *rival_id* as opponent.
    """
    target_dossier: RivalDossier | None = None

    if user_id:
        target_dossier = _rival_store.get(_key(user_id, rival_id))
    else:
        for k, d in _rival_store.items():
            if d.opponent_id == rival_id:
                target_dossier = d
                break

    if target_dossier is None:
        return None

    ks = target_dossier.kill_sheet

    # Derive exploits from encounters
    win_moments: list[str] = []
    for enc in target_dossier.encounters:
        if enc.result == "win":
            win_moments.extend(enc.key_moments)

    for moment in win_moments:
        if moment and moment not in ks.exploits:
            ks.exploits.append(moment)

    ks.last_updated = datetime.utcnow()
    return ks


def check_is_rival(user_id: str, opponent_id: str) -> bool:
    """Return True if *opponent_id* qualifies as a rival (2+ matchups)."""
    k = _key(user_id, opponent_id)
    dossier = _rival_store.get(k)
    if dossier is None:
        return False
    return dossier.encounter_count >= RIVAL_THRESHOLD


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_threat_trend(dossier: RivalDossier) -> str:
    """Compute whether the rival is getting better/worse against the user.

    Looks at the last 3 encounters and compares results.
    """
    recent = dossier.encounters[-3:]
    if len(recent) < 2:
        return "stable"

    results = [e.result for e in recent]
    wins = results.count("win")
    losses = results.count("loss")

    if losses > wins:
        return "rising"  # rival is beating us more = rising threat
    if wins > losses:
        return "falling"  # we're beating them more = falling threat
    return "stable"
