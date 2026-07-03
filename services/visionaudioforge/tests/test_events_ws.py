"""Tests for the Phase 1a Day 1 WS event subscriber surface.

Unit tests (deterministic, no OCR) exercise `/ws/events/{session_id}` +
`event_hub`: auth, unknown-session rejection, fan-out to one/many
subscribers, event-display-only pass-through, and unsubscribe-on-disconnect.

The integration test drives a REAL play-call OVERLAY clip through the
dispatcher (real OCR) and asserts a real `FORMATION_LOCKED` (non-null
formation name) streams to a connected subscriber. It runs only where the
clip + OCR deps are present; otherwise it skips.

FIXTURE CLASSES (ADR 0014 §3 — one architectural boundary, not a bug):
- **Overlay clips** (`madden26_playcall_*.mp4`) show the play-call /
  formation-select overlay. ADR 0014 reads the formation off that overlay,
  so ONLY these clips validate formation extraction.
- **Gameplay / broadcast clips** (`madden26_practice_*`, `madden26_yt_*`
  incl. ravens) have no overlay on screen, so they read formation NULL
  BY DESIGN — they validate transport only, never formation extraction.

Run (in the VAF core venv):
    cd services/visionaudioforge
    ESF_OVERLAY_CLIP=/abs/path/madden26_playcall_shotgun_trips.mp4 \
      python -m pytest tests/test_events_ws.py -v
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

# conftest.py puts the service root on sys.path.
from app.core.event_hub import hub
from app.core.session import registry
from app.main import app
from app.schemas.enums import IntegrityMode, TitleEnum

AUTH = {"authorization": "Bearer test-token"}


def _open_session(client: TestClient, sid: str) -> None:
    client.portal.call(registry.open, sid, "user-x", IntegrityMode.OFFLINE_LAB)


# ---------------------------------------------------------------------------
# Unit — auth / rejection
# ---------------------------------------------------------------------------


def test_ws_rejects_missing_auth():
    with TestClient(app) as client:
        _open_session(client, "sid-auth")
        with pytest.raises(WebSocketDisconnect) as ei:
            with client.websocket_connect("/ws/events/sid-auth") as ws:  # no auth header
                ws.receive_json()
        assert ei.value.code == 1008


def test_ws_rejects_unknown_session():
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as ei:
            with client.websocket_connect("/ws/events/no-such-session", headers=AUTH) as ws:
                ws.receive_json()
        assert ei.value.code == 1008


# ---------------------------------------------------------------------------
# Unit — fan-out / streaming
# ---------------------------------------------------------------------------


def test_ws_streams_published_event_as_is():
    """Event is streamed verbatim — event-display-only, no coaching fields added."""
    with TestClient(app) as client:
        sid = "sid-stream"
        _open_session(client, sid)
        with client.websocket_connect(f"/ws/events/{sid}", headers=AUTH) as ws:
            event = {"event_type": "SNAPSHOT", "session_id": sid,
                     "payload": {"offensive_formation": None}}
            delivered = client.portal.call(hub.publish, sid, event)
            assert delivered == 1
            assert ws.receive_json() == event  # byte-for-byte, nothing added


def test_ws_multiple_subscribers_both_receive():
    with TestClient(app) as client:
        sid = "sid-multi"
        _open_session(client, sid)
        with client.websocket_connect(f"/ws/events/{sid}", headers=AUTH) as ws1, \
             client.websocket_connect(f"/ws/events/{sid}", headers=AUTH) as ws2:
            event = {"event_type": "FORMATION_LOCKED", "session_id": sid}
            assert client.portal.call(hub.publish, sid, event) == 2
            assert ws1.receive_json() == event
            assert ws2.receive_json() == event


def test_hub_publish_no_subscribers_returns_zero():
    with TestClient(app) as client:
        assert client.portal.call(hub.publish, "ghost-session", {"event_type": "SNAPSHOT"}) == 0


def test_ws_unsubscribes_on_disconnect():
    with TestClient(app) as client:
        sid = "sid-unsub"
        _open_session(client, sid)
        with client.websocket_connect(f"/ws/events/{sid}", headers=AUTH):
            deadline = time.monotonic() + 2.0
            while hub.subscriber_count(sid) < 1 and time.monotonic() < deadline:
                time.sleep(0.02)
            assert hub.subscriber_count(sid) == 1
        # After the client disconnects, the server must unsubscribe.
        deadline = time.monotonic() + 2.0
        while hub.subscriber_count(sid) > 0 and time.monotonic() < deadline:
            time.sleep(0.02)
        assert hub.subscriber_count(sid) == 0


# ---------------------------------------------------------------------------
# Integration — real events from a real processed clip → subscriber
# ---------------------------------------------------------------------------

# REQUIRED: a play-call OVERLAY capture (madden26_playcall_*.mp4), NOT
# gameplay footage. ADR 0014 reads the formation off the on-screen play-call
# overlay; gameplay/broadcast clips (madden26_practice_*, madden26_yt_*,
# ravens) have no overlay on screen and read formation NULL BY DESIGN — they
# would fail this test for a non-code reason and validate transport only.
# This is one architectural boundary (ADR 0014 §3 "capture mode is a
# first-class requirement"), not a per-clip bug.
OVERLAY_CLIP = os.environ.get(
    "ESF_OVERLAY_CLIP",
    str(Path(__file__).resolve().parents[2] / "agents" / "capture" / "fixtures"
        / "real" / "madden26_playcall_shotgun_trips.mp4"),
)


def test_integration_overlay_clip_streams_real_formation_locked():
    """A real FORMATION_LOCKED from a play-call OVERLAY clip reaches a WS subscriber.

    REQUIRES an overlay capture (`madden26_playcall_*.mp4`). Gameplay/broadcast
    clips (practice_*, yt_*/ravens) yield 0 FORMATION_LOCKED by design — no
    overlay on screen, ADR 0014 §3 — and validate transport only, not
    formation extraction.
    """
    clip = Path(OVERLAY_CLIP)
    if not clip.exists():
        pytest.skip(
            f"overlay clip not present: {clip} "
            "(set ESF_OVERLAY_CLIP to a madden26_playcall_*.mp4)"
        )

    import cv2  # noqa: PLC0415 — heavy dep, import only when the test runs

    from app.core.dispatcher import Dispatcher
    from app.core.session import SessionContext

    # 1) Produce real events from the real clip via the dispatcher (real OCR).
    session = SessionContext.open(
        "integ-src", "user-x", IntegrityMode.OFFLINE_LAB, active_title_hint=TitleEnum.MADDEN26
    )
    disp = Dispatcher(session)
    cap = cv2.VideoCapture(str(clip))
    assert cap.isOpened(), f"could not open practice clip: {clip}"

    real_formation = None
    idx, dispatched = -1, 0
    while dispatched < 2000 and real_formation is None:
        ok, frame = cap.read()
        if not ok:
            break
        idx += 1
        if idx % 5 != 0:  # ~12 fps from 60 fps, matching the harness
            continue
        dispatched += 1
        for ev in (disp.process_frame(frame) or []):
            d = ev.model_dump(mode="json")
            if d.get("event_type") == "FORMATION_LOCKED" and d.get("payload", {}).get("offensive_formation"):
                real_formation = d
                break
    cap.release()

    assert real_formation is not None, (
        "expected >=1 real FORMATION_LOCKED with non-null formation name from the practice clip"
    )

    # 2) Prove that real event streams through the WS surface to a subscriber.
    with TestClient(app) as client:
        sid = "integ-ws"
        client.portal.call(registry.open, sid, "user-x", IntegrityMode.OFFLINE_LAB)
        with client.websocket_connect(f"/ws/events/{sid}", headers=AUTH) as ws:
            assert client.portal.call(hub.publish, sid, real_formation) == 1
            got = ws.receive_json()

    assert got["event_type"] == "FORMATION_LOCKED"
    assert got["payload"]["offensive_formation"], "streamed event lost its formation name"
    print(
        f"\n[integration] streamed via WS subscriber: event_type={got['event_type']} "
        f"formation={got['payload']['offensive_formation']!r} "
        f"family={got['payload'].get('offensive_formation_family')!r}"
    )
