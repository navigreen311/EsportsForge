"""PlayerTwin AI Service — manages the digital player model.

Provides update, recalibrate, reset, and correct operations on the
player's digital twin. Uses a weighted-update approach:
  20% new session data, 80% existing profile.
"""

from __future__ import annotations

import logging
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Blend weights for profile updates
NEW_DATA_WEIGHT = 0.20
EXISTING_WEIGHT = 0.80


class PlayerTwinService:
    """AI-powered player twin management.

    Maintains an in-memory store of player twin profiles, each keyed
    by ``(user_id, title)``.  Real persistence is handled at the API
    layer via the DB — this service owns the computation logic.
    """

    def __init__(self) -> None:
        # In-memory store: user_id -> title -> profile dict
        self._store: dict[str, dict[str, dict[str, Any]]] = {}

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_twin_profile(self, user_id: str, title: str | None = None) -> dict[str, Any]:
        """Return the full twin profile for a user (optionally per-title).

        If ``title`` is None, returns all title profiles merged into a
        single response.
        """
        user_profiles = self._store.get(user_id, {})

        if title:
            profile = user_profiles.get(title, self._default_profile(user_id, title))
            return profile

        if not user_profiles:
            return {
                "user_id": user_id,
                "profiles": {},
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        return {
            "user_id": user_id,
            "profiles": {t: p for t, p in user_profiles.items()},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Update from session (called after LoopAI processes a session)
    # ------------------------------------------------------------------

    def update_from_session(
        self,
        user_id: str,
        title: str,
        session_updates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Apply learning-loop updates to the twin profile.

        Uses weighted blending: 80% existing state + 20% new session data.

        Parameters
        ----------
        user_id : str
        title : str
        session_updates : list[dict]
            Each dict has ``type``, ``recommendation_name``, ``weight_delta``,
            and ``reason`` as produced by LoopAIService.process_session_end.

        Returns
        -------
        Updated twin profile dict.
        """
        profile = self._ensure_profile(user_id, title)

        for update in session_updates:
            update_type = update.get("type", "unknown")
            rec_name = update.get("recommendation_name", "unknown")
            weight_delta = update.get("weight_delta", 0.0)

            # Apply weighted blend to skill beliefs
            beliefs = profile.setdefault("skill_beliefs", {})
            current_value = beliefs.get(rec_name, 0.5)

            # 80% existing + 20% new signal
            new_signal = current_value + weight_delta
            blended = (EXISTING_WEIGHT * current_value) + (NEW_DATA_WEIGHT * new_signal)
            beliefs[rec_name] = round(max(0.0, min(1.0, blended)), 4)

            # Track update history
            history_entry = {
                "type": update_type,
                "recommendation": rec_name,
                "old_value": current_value,
                "new_value": beliefs[rec_name],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": update.get("reason", ""),
            }
            profile.setdefault("update_history", []).append(history_entry)

        profile["sessions_analyzed"] = profile.get("sessions_analyzed", 0) + 1
        profile["updated_at"] = datetime.now(timezone.utc).isoformat()
        profile["confidence"] = min(
            1.0, round(profile["sessions_analyzed"] / 10, 4)
        )

        logger.info(
            "PlayerTwin updated user=%s title=%s sessions=%d updates=%d",
            user_id, title, profile["sessions_analyzed"], len(session_updates),
        )

        return deepcopy(profile)

    # ------------------------------------------------------------------
    # Recalibrate — full re-evaluation of twin beliefs
    # ------------------------------------------------------------------

    def recalibrate(self, user_id: str, title: str | None = None) -> dict[str, Any]:
        """Force a recalibration of the twin profile.

        Resets confidence and smooths all belief values toward 0.5
        (neutral). The profile remains but becomes less opinionated
        so future sessions have stronger influence.
        """
        user_profiles = self._store.get(user_id, {})
        titles_to_recalibrate = [title] if title else list(user_profiles.keys())

        recalibrated: list[str] = []

        for t in titles_to_recalibrate:
            if t not in user_profiles:
                continue

            profile = user_profiles[t]
            beliefs = profile.get("skill_beliefs", {})

            # Smooth all beliefs toward 0.5
            for key in beliefs:
                beliefs[key] = round(beliefs[key] * 0.6 + 0.5 * 0.4, 4)

            # Reduce confidence to encourage re-learning
            profile["confidence"] = max(0.1, round(profile.get("confidence", 0.5) * 0.5, 4))
            profile["updated_at"] = datetime.now(timezone.utc).isoformat()
            profile.setdefault("update_history", []).append({
                "type": "recalibrate",
                "recommendation": "*",
                "old_value": None,
                "new_value": None,
                "timestamp": profile["updated_at"],
                "reason": "Manual recalibration triggered.",
            })

            recalibrated.append(t)

        logger.info(
            "PlayerTwin recalibrated user=%s titles=%s",
            user_id, recalibrated,
        )

        return {
            "user_id": user_id,
            "recalibrated_titles": recalibrated,
            "message": f"Recalibrated {len(recalibrated)} title(s).",
        }

    # ------------------------------------------------------------------
    # Reset — wipe profile for a user (optionally per-title)
    # ------------------------------------------------------------------

    def reset(self, user_id: str, title: str | None = None) -> dict[str, Any]:
        """Reset the twin profile. If ``title`` is given, only that title
        is reset; otherwise all titles for the user are wiped.
        """
        if title:
            if user_id in self._store and title in self._store[user_id]:
                del self._store[user_id][title]
            return {
                "user_id": user_id,
                "reset_titles": [title],
                "message": f"Twin profile for {title} has been reset.",
            }

        if user_id in self._store:
            titles_reset = list(self._store[user_id].keys())
            del self._store[user_id]
        else:
            titles_reset = []

        return {
            "user_id": user_id,
            "reset_titles": titles_reset,
            "message": f"All twin profiles reset ({len(titles_reset)} title(s)).",
        }

    # ------------------------------------------------------------------
    # Correct — manual player override of a twin belief
    # ------------------------------------------------------------------

    def correct(
        self,
        user_id: str,
        title: str,
        corrections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Apply player-supplied corrections to the twin.

        Each correction dict has:
        - skill: str — the skill/recommendation name
        - value: float — the corrected belief value (0-1)
        - reason: str — optional player note
        """
        profile = self._ensure_profile(user_id, title)
        beliefs = profile.setdefault("skill_beliefs", {})
        applied: list[str] = []

        for correction in corrections:
            skill = correction.get("skill", "")
            value = correction.get("value", 0.5)
            reason = correction.get("reason", "Player override")

            if not skill:
                continue

            old_value = beliefs.get(skill)
            beliefs[skill] = round(max(0.0, min(1.0, value)), 4)
            applied.append(skill)

            profile.setdefault("update_history", []).append({
                "type": "player_correction",
                "recommendation": skill,
                "old_value": old_value,
                "new_value": beliefs[skill],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": reason,
            })

        profile["updated_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(
            "PlayerTwin corrected user=%s title=%s skills=%s",
            user_id, title, applied,
        )

        return {
            "user_id": user_id,
            "title": title,
            "corrected_skills": applied,
            "profile": deepcopy(profile),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_profile(self, user_id: str, title: str) -> dict[str, Any]:
        self._store.setdefault(user_id, {})
        if title not in self._store[user_id]:
            self._store[user_id][title] = self._default_profile(user_id, title)
        return self._store[user_id][title]

    @staticmethod
    def _default_profile(user_id: str, title: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "user_id": user_id,
            "title": title,
            "skill_beliefs": {},
            "sessions_analyzed": 0,
            "confidence": 0.0,
            "update_history": [],
            "created_at": now,
            "updated_at": now,
        }
