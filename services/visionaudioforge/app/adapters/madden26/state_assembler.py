"""Madden 26 state assembler — diff prior state against new readings,
emit events on the universal contract.

Phase 0: assembles a plausible Madden26Payload from OCR + formation
reads. Emits SNAPSHOT events at 1Hz once title is locked. Real logic
(SCORE_CHANGE / DOWN_AND_DISTANCE / FORMATION_LOCKED diffing against
prior state in session.adapter_state) lands in Phase 1 M6.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.envelope import make_envelope
from app.core.session import SessionContext
from app.schemas.enums import EventType
from app.schemas.events import EventEnvelope, Madden26Payload

from .formation_detector import FormationReading
from .ocr_pipeline import OCRSnapshot

ADAPTER_VERSION = "madden26@0.0.1-phase-0"

# Map raw formation slug → spoken / display name.
FORMATION_DISPLAY = {
    "shotgun_trips": "Shotgun Trips",
    "shotgun_bunch": "Shotgun Bunch",
    "shotgun_empty": "Shotgun Empty",
    "i_form_pro": "I-Form Pro",
    "singleback_ace": "Singleback Ace",
    "pistol_strong": "Pistol Strong",
    "shotgun_doubles": "Shotgun Doubles",
    "singleback_wing": "Singleback Wing",
}


def assemble(
    session: SessionContext,
    ocr: OCRSnapshot,
    offense: FormationReading,
    captured_at: datetime,
) -> list[EventEnvelope]:
    """Build event(s) for one frame.

    Phase 0: emits a single SNAPSHOT event per call (1 Hz cadence is
    handled upstream by the dispatcher; for now every frame produces
    a snapshot — fine because Phase 0 frame rate from the test-video
    capture source is low).
    """

    # Defensive: skip entirely if title not locked yet.
    if session.title is None:
        return []

    # Build payload. Fields that OCR couldn't read confidently fall
    # back to the prior session value; for Phase 0 we just use the
    # OCR snapshot directly.
    payload = Madden26Payload(
        score_home=ocr.score_home or 0,
        score_away=ocr.score_away or 0,
        quarter=ocr.quarter or 1,
        clock=ocr.clock or "0:00",
        down=ocr.down,
        distance=ocr.distance,
        field_position=ocr.field_position,
        possession="home",  # Phase 0 placeholder; real logic uses scoreboard cue
        offensive_formation=FORMATION_DISPLAY.get(offense.formation or "")
        or offense.formation,
        defensive_formation=None,  # v0.2/v0.3 wires this
    )

    # Confidence: average of OCR + formation. Real logic would weight by
    # event type (score/down derived from OCR; formation from CNN).
    confidence = round((ocr.confidence_overall + offense.confidence) / 2, 3)

    return [
        make_envelope(
            session=session,
            event_type=EventType.SNAPSHOT,
            payload=payload,
            confidence=confidence,
            adapter_version=ADAPTER_VERSION,
            captured_at=captured_at,
        )
    ]
