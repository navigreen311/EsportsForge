"""Phase 1a Live-path E2E — Tier 1 proof (real WS delivery).

Proves a REAL FORMATION_LOCKED travels the live socket end-to-end:
  overlay clip -> agent modules (FilePlaybackSource + WSClient) -> core /ws/ingest
  -> dispatcher -> OCR -> event_hub -> a real WS subscriber on /ws/events/{sid}.

Not narrated, not mocked: uses the actual capture-agent transport + source
modules to drive core over a real WebSocket, and a real `websockets` client to
receive. Requires VAF core already running (uvicorn :8100) and an OVERLAY clip
(broadcast reads null by design).

Usage (VAF venv):
    VAF_CORE_URL=http://127.0.0.1:8100 \
    ESF_OVERLAY_CLIP=/abs/madden26_playcall_shotgun_trips.mp4 \
    python agents/capture/e2e_live_path.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
import websockets

sys.path.insert(0, str(Path(__file__).resolve().parent))  # capture_agent importable
from capture_agent.capture.file_playback import FilePlaybackSource  # noqa: E402
from capture_agent.transport.ws_client import WSClient  # noqa: E402

CORE = os.environ.get("VAF_CORE_URL", "http://127.0.0.1:8100")
CORE_WS = CORE.replace("http://", "ws://").replace("https://", "wss://")
CLIP = os.environ["ESF_OVERLAY_CLIP"]
TOKEN = os.environ.get("ESF_CAPTURE_TOKEN", "esf-cap-dev-placeholder")


async def main() -> int:
    # 1. Session: use a broker-provisioned session_id if given (Tier 2), else
    #    open one directly on core (Tier 1 standalone).
    sid = os.environ.get("ESF_SESSION_ID")
    if sid:
        print(f"session (broker-provisioned): {sid}")
    else:
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{CORE}/api/v1/sessions/open",
                json={"user_id": "founder", "integrity_mode": "offline_lab", "active_title": "madden26"},
            )
            r.raise_for_status()
            sid = r.json()["session_id"]
        print(f"session (direct): {sid}")

    got: list[dict] = []
    sub_ready = asyncio.Event()

    async def subscribe() -> None:
        async with websockets.connect(f"{CORE_WS}/ws/events/{sid}?token={TOKEN}") as ws:
            sub_ready.set()
            async for raw in ws:
                ev = json.loads(raw)
                if ev.get("event_type") == "FORMATION_LOCKED":
                    got.append(ev)
                    return

    sub_task = asyncio.create_task(subscribe())
    await asyncio.wait_for(sub_ready.wait(), timeout=10)
    await asyncio.sleep(0.3)  # ensure the subscriber is registered before frames flow

    # 2. Drive the overlay clip through the REAL agent transport (WSClient + source).
    ws = WSClient(endpoint=f"{CORE_WS}/ws/ingest", api_key=TOKEN, session_id=sid)
    await ws.connect()
    src = FilePlaybackSource(CLIP, target_fps=12, playback_mode="max")
    src.open()
    batch, sent = [], 0
    for fr in src.frames():
        batch.append(fr)
        sent += 1
        if len(batch) >= 4:
            await ws.send_frame_batch(batch, 75)
            batch = []
            await asyncio.sleep(0.02)  # yield so the subscriber can drain
        if got or sent >= 200:
            break
    if batch:
        await ws.send_frame_batch(batch, 75)
    await ws.close()
    src.close()

    # 3. Await the real event on the subscriber.
    try:
        await asyncio.wait_for(asyncio.shield(sub_task), timeout=30)
    except asyncio.TimeoutError:
        sub_task.cancel()

    if got:
        ev = got[0]
        p = ev.get("payload", {})
        print("TIER1 PASS: real FORMATION_LOCKED received over /ws/events")
        print(f"  session_id : {ev.get('session_id')}")
        print(f"  event_type : {ev.get('event_type')}")
        print(f"  formation  : {p.get('offensive_formation')!r}")
        print(f"  family     : {p.get('offensive_formation_family')!r}")
        print(f"  frames_sent: {sent}")
        return 0
    print(f"TIER1 FAIL: no FORMATION_LOCKED received (sent {sent} frames)")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
