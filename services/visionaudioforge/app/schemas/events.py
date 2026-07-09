"""Event-bus contract — universal envelope + sport-archetype payloads.

Locked surface per docs/integrations/visionaudioforge/03-event-bus-contract.md.
Phase 0 ships the football payload (Madden 26 + CFB 26 share the
FootballPayload base). Other archetypes added when their adapters land.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from .enums import EventType, TitleEnum

# ---------------------------------------------------------------------------
# Sport-archetype base classes
# ---------------------------------------------------------------------------


class FootballPayload(BaseModel):
    """Shared shape between Madden 26 and CFB 26."""

    model_config = ConfigDict(extra="forbid")

    # Nullable so an unreadable/degraded frame (menu, replay, mis-region, or a HUD
    # element OCR can't resolve) emits null rather than a fabricated value. A
    # partial read degrades field-by-field; a fully-blank read is skipped upstream
    # (state_assembler). Broadcast/overlay frames read null by design. (v2.3.0-live)
    score_home: int | None = None
    score_away: int | None = None
    quarter: int | None = None
    clock: str | None = None  # "MM:SS" or None when unreadable
    down: int | None = None
    distance: int | None = None
    field_position: str | None = None  # "OWN_35", "OPP_22", "MIDFIELD"
    possession: Literal["home", "away"] | None = None
    offensive_formation: str | None = None  # full play-call name, e.g. "Trips TE Offset"
    offensive_formation_family: str | None = None  # canonical-8 tag, e.g. "shotgun_trips" (ADR 0014)
    defensive_formation: str | None = None  # None until v0.3 ships


class Madden26Payload(FootballPayload):
    """Madden 26 — extends FootballPayload."""

    title: Literal[TitleEnum.MADDEN26] = TitleEnum.MADDEN26


class CFB26Payload(FootballPayload):
    """CFB 26 — extends FootballPayload. Phase 2 adapter target."""

    title: Literal[TitleEnum.CFB26] = TitleEnum.CFB26


# Other archetypes (Basketball/Soccer/Baseball/BR/Combat/Golf/Card)
# are added as their adapter phases ship. Phase 0 = football only.


GameStatePayload = Annotated[
    Union[Madden26Payload, CFB26Payload],
    Field(discriminator="title"),
]


# ---------------------------------------------------------------------------
# Event envelope
# ---------------------------------------------------------------------------


class EventEnvelope(BaseModel):
    """Universal envelope for every event published to the bus.

    Envelope is title-discriminated via the `title` field; consumers
    pattern-match against it to get a typed payload.
    """

    model_config = ConfigDict(extra="forbid")

    event_id: str
    session_id: str
    user_id_hash: str  # one-way hash; raw user_id never leaves the core
    title: TitleEnum
    timestamp: datetime
    captured_at: datetime
    confidence: float = Field(ge=0.0, le=1.0)
    adapter_version: str  # "madden26@0.0.1"
    event_type: EventType
    payload: GameStatePayload
