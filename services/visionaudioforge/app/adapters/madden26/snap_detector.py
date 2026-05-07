"""Madden 26 snap detector — pre-snap / post-snap state machine.

Phase 0 stub. Real implementation: frame-difference + play-clock OCR
disappearance, per docs/integrations/visionaudioforge/04-madden26-adapter-spec.md.

State machine: PRE_SNAP → SNAP_PENDING → POST_SNAP → BETWEEN_PLAYS.
Acceptable error: ±200 ms snap-time accuracy, ≥95% recall.
"""

from __future__ import annotations

from enum import Enum


class SnapState(str, Enum):
    PRE_SNAP = "PRE_SNAP"
    POST_SNAP = "POST_SNAP"
    BETWEEN_PLAYS = "BETWEEN_PLAYS"


class SnapDetector:
    """Per-session detector — state lives in session.adapter_state."""

    def update(self, frame, prior_state: SnapState | None) -> SnapState:
        """Phase 0 stub: returns prior state unchanged.

        TODO(phase-1-m5b): implement the real state machine.
        """
        return prior_state or SnapState.BETWEEN_PLAYS
