"""TitleAdapter protocol — every adapter implements this contract.

ADR 0006 governs `max_processing_ms`: 80 for v0.1 (offensive formation
only), 100 for v0.2 (+ pre-snap defensive front), 120 for v0.3
(+ post-snap coverage). Each adapter declares its own per-version value.

ADR 0005 governs `preferred_base_fps` / `preferred_max_fps`: 12/24 for
football is the default; FPS/BR adapters declare 20/30, golf 4/12, etc.
The capture agent reads these from the session_open handshake.

Hard requirements (from docs/specs/02-visionaudioforge-core.md §2):
- Pure function semantics. No I/O.
- State lives in session.adapter_state.
- ML models lazy-load in __init__, never in process_frame.
- max_processing_ms is enforced; budget breaches drop the frame.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import numpy as np

from app.core.session import SessionContext
from app.schemas.enums import EventType, TitleEnum


# ---------------------------------------------------------------------------
# Per-adapter integrity policy (declared by the adapter, applied by the core)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IntegrityPolicy:
    """What an adapter declares the core should do under each integrity mode.

    Three knobs:
      - no_processing: skip this adapter entirely (frames drop upstream).
      - disable_event_types: emit everything except these.
      - opponent_data_redacted: assemble events but flag for redaction.
    """

    no_processing: bool = False
    disable_event_types: frozenset[EventType] = field(default_factory=frozenset)
    opponent_data_redacted: bool = False

    @classmethod
    def unrestricted(cls) -> "IntegrityPolicy":
        return cls()


# ---------------------------------------------------------------------------
# Cadence profile (ADR 0005)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CadenceProfile:
    """How the adapter wants frames sampled and the queue to behave.

    Declared by each adapter; the capture agent reads preferred_base_fps
    + preferred_max_fps from the session_open handshake.
    """

    name: str  # "football" | "basketball" | "fps" | "br" | "combat" | "golf" | "card"
    preferred_base_fps: int
    preferred_max_fps: int
    snap_interruption_rule: str = "duck_only"  # see Madden language profile


# ---------------------------------------------------------------------------
# Adapter contract
# ---------------------------------------------------------------------------


@runtime_checkable
class TitleAdapter(Protocol):
    """Every adapter implements this. Adapters live under
    services/visionaudioforge/app/adapters/<title>/."""

    title: TitleEnum
    version: str  # "madden26@0.0.1-phase-0"
    max_processing_ms: int  # ADR 0006 — per-version budget
    cadence: CadenceProfile  # ADR 0005 — per-archetype cadence
    integrity_rules: dict  # IntegrityMode -> IntegrityPolicy

    def process_frame(
        self,
        frame: np.ndarray,
        session: SessionContext,
    ) -> list:  # list[EventEnvelope] but Protocol can't import that cleanly
        ...
