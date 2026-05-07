"""Per-session integrity-mode gating.

Frame-level + event-level gating per docs/specs/02-visionaudioforge-core.md §6.
The agent is untrusted; the core enforces.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.schemas.enums import IntegrityMode, TitleEnum

logger = logging.getLogger("vaf.integrity_gate")


# Titles whose anti-cheat systems flag screen-capture in ranked play.
# (Doc #07 of the integrity-gating spec — Warzone, Fortnite, Valorant.)
RANKED_BLOCKED_TITLES: set[TitleEnum] = {
    TitleEnum.WARZONE,
    TitleEnum.FORTNITE,
    # Valorant not in the EsportsForge title roster; entry kept here as
    # a documentation hook in case it joins.
}


@dataclass
class FrameGateDecision:
    process: bool
    reason: str = ""
    redact_opponent: bool = False


def evaluate_frame(
    integrity_mode: IntegrityMode,
    title: TitleEnum | None,
) -> FrameGateDecision:
    """Decide whether to dispatch this frame to the adapter."""

    if integrity_mode == IntegrityMode.TOURNAMENT:
        return FrameGateDecision(
            process=False,
            reason="integrity_tournament_blocks_capture",
        )

    if integrity_mode == IntegrityMode.RANKED and title in RANKED_BLOCKED_TITLES:
        return FrameGateDecision(
            process=False,
            reason="ranked_blocks_anti_cheat_titles",
        )

    if integrity_mode == IntegrityMode.BROADCAST:
        return FrameGateDecision(
            process=True,
            redact_opponent=True,
        )

    # OFFLINE_LAB and unrestricted RANKED titles
    return FrameGateDecision(process=True)
