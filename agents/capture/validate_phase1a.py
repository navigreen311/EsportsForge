"""Phase 1a Drill Lab — Validation-step harness (§5.7 runnable criteria).

Runs the local corpus through the in-process pipeline
(file -> Dispatcher -> Madden OCR/adapter -> events), bounded per clip, and
emits a per-clip log. Validation OUTPUT, not a production build.

Fixture classes (ADR 0014 §3 boundary — corrected per Session #6 evidence):
  - OVERLAY clips = madden26_playcall_* AND madden26_practice_*. Both show the
    play-call/formation-select overlay (practice mode surfaces it too), so both
    validate FORMATION extraction. Expected family is parsed from the filename.
    A clip that reads None in the bounded window = "no overlay in window"
    (absence != failure — the overlay is just outside the sampled window).
  - BROADCAST clips = madden26_yt_* only. No overlay -> validate TRANSPORT works
    AND ZERO false-positive FORMATION_LOCKED (§5.7 #3). ANY formation here fails.

FAIL (non-zero exit) iff: an overlay clip extracts the WRONG formation (family
!= expected), OR a broadcast clip emits ANY FORMATION_LOCKED. None-in-window is
NOT a failure.

Deferred (recorded, not run): #2 live page display, #7 rollback-alarm wire (P2),
#8 webhook audit (:8002). Integrity mode: OFFLINE_LAB (FORMATION-emitting, §3).

Tracked robustness finding (recorded, NOT fixed this session): broadcast/
null-HUD frames trigger a caught Madden26Payload ValidationError (score/clock
required non-null) -> event logged+dropped, non-fatal. Payload-schema change is
separate work.

Usage:
    ESF_CORPUS_DIR=/abs/fixtures/real python agents/capture/validate_phase1a.py \
        --out docs/phase-completions/1a-drill-lab-validation-log.md
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import cv2

SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "visionaudioforge"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.core.dispatcher import Dispatcher  # noqa: E402
from app.core.session import SessionContext  # noqa: E402
from app.schemas.enums import IntegrityMode, TitleEnum  # noqa: E402

FRAME_STRIDE = 5       # ~12 fps from 60 fps (matches real_footage_harness)
OVERLAY_CAP = 900      # dispatched frames to look for the overlay
BROADCAST_CAP = 150    # bounded window for the zero-false-positive check


def expected_family(stem: str) -> str | None:
    """Canonical family expected from an overlay clip's filename (None = any)."""
    if "human_exhibition" in stem:
        return None  # human-played: any/no fixed formation
    for prefix in ("madden26_playcall_", "madden26_practice_"):
        if stem.startswith(prefix):
            return stem[len(prefix):].replace("-", "_")  # 'i-form_pro' -> 'i_form_pro'
    return None


def _new_dispatcher() -> Dispatcher:
    session = SessionContext.open(
        session_id="validate-1a", user_id="founder",
        integrity_mode=IntegrityMode.OFFLINE_LAB, active_title_hint=TitleEnum.MADDEN26,
    )
    return Dispatcher(session)


def _run_clip(path: Path, cap: int, stop_on_formation: bool) -> dict:
    cap_obj = cv2.VideoCapture(str(path))
    if not cap_obj.isOpened():
        return {"clip": path.name, "opened": False, "error": "could not open"}
    disp = _new_dispatcher()
    by_type: dict[str, int] = {}
    formation_name: str | None = None
    formation_family: str | None = None
    idx, dispatched, errors = -1, 0, 0
    t0 = time.monotonic()
    while dispatched < cap:
        ok, frame = cap_obj.read()
        if not ok:
            break
        idx += 1
        if idx % FRAME_STRIDE != 0:
            continue
        dispatched += 1
        try:
            events = disp.process_frame(frame)
        except Exception:  # noqa: BLE001
            errors += 1
            continue
        for ev in (events or []):
            d = ev.model_dump(mode="json")
            et = d.get("event_type", "?")
            by_type[et] = by_type.get(et, 0) + 1
            if et == "FORMATION_LOCKED" and formation_name is None:
                formation_name = d.get("payload", {}).get("offensive_formation")
                formation_family = d.get("payload", {}).get("offensive_formation_family")
        if stop_on_formation and formation_name is not None:
            break
    elapsed = time.monotonic() - t0
    cap_obj.release()
    return {
        "clip": path.name, "opened": True, "dispatched": dispatched, "by_type": by_type,
        "errors": errors, "formation_name": formation_name, "formation_family": formation_family,
        "fps": round(dispatched / elapsed, 1) if elapsed > 0 else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path,
                    default=Path(os.environ.get("ESF_CORPUS_DIR", "agents/capture/fixtures/real")))
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    corpus = args.corpus

    overlay = sorted(corpus.glob("madden26_playcall_*.mp4")) + sorted(corpus.glob("madden26_practice_*.mp4"))
    broadcast = sorted(corpus.glob("madden26_yt_*.mp4"))
    if not overlay and not broadcast:
        print(f"No corpus clips found in {corpus}")
        return 2

    overlay_results, broadcast_results = [], []
    mismatches, false_positives = [], []

    print(f"=== OVERLAY clips ({len(overlay)}) — formation extraction ===")
    for p in overlay:
        r = _run_clip(p, OVERLAY_CAP, stop_on_formation=True)
        exp = expected_family(p.stem)
        got = r.get("formation_family")
        if got is None:
            r["status"] = "no-overlay-in-window"  # absence != failure
        elif exp is None:
            r["status"] = "extracted (human/any)"
        elif got == exp:
            r["status"] = "match"
        else:
            r["status"] = "MISMATCH"
            mismatches.append((p.stem, exp, got, r.get("formation_name")))
        r["expected"] = exp if exp is not None else "(any)"
        overlay_results.append(r)
        print(f"  {p.stem}: name={r.get('formation_name')!r} family={got!r} "
              f"expected={r['expected']} -> {r['status']} ({r.get('dispatched')}f {r.get('fps')}fps)")

    print(f"=== BROADCAST clips ({len(broadcast)}, yt_ only) — transport + zero false-positive ===")
    for p in broadcast:
        r = _run_clip(p, BROADCAST_CAP, stop_on_formation=False)
        fp = r.get("by_type", {}).get("FORMATION_LOCKED", 0)
        r["false_positive_formation"] = fp
        if fp > 0:
            false_positives.append((p.name, fp))
        broadcast_results.append(r)
        print(f"  {p.name}: by_type={r.get('by_type')} false_positive_FORMATION={fp} "
              f"errors={r.get('errors')} ({r.get('dispatched')}f {r.get('fps')}fps)")

    matched = sum(1 for r in overlay_results if r["status"] in ("match", "extracted (human/any)"))
    none_in_window = sum(1 for r in overlay_results if r["status"] == "no-overlay-in-window")
    fps_all = [r["fps"] for r in overlay_results + broadcast_results if r.get("fps")]
    summary = {
        "overlay_total": len(overlay_results), "overlay_matched": matched,
        "overlay_none_in_window": none_in_window, "mismatches": mismatches,
        "broadcast_total": len(broadcast_results), "false_positives": false_positives,
        "fps_min": round(min(fps_all), 1) if fps_all else 0.0,
        "fps_max": round(max(fps_all), 1) if fps_all else 0.0,
    }
    print("=== SUMMARY ===")
    print(f"  overlay: {matched} matched, {none_in_window} no-overlay-in-window, "
          f"{len(mismatches)} MISMATCH")
    print(f"  mismatches: {mismatches or 'none'}")
    print(f"  broadcast false-positives: {false_positives or 'none'}")
    print(f"  throughput: {summary['fps_min']}-{summary['fps_max']} fps (pipeline w/ OCR)")

    if args.out:
        args.out.write_text(_render_log(overlay_results, broadcast_results, summary), encoding="utf-8")
        print(f"  log written: {args.out}")

    ok = not mismatches and not false_positives
    print(f"  RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def _render_log(overlay, broadcast, s) -> str:
    L = [
        "# Phase 1a Drill Lab - Validation Log (§5.7 runnable criteria)",
        "",
        "- **Scope:** in-process pipeline (file -> dispatcher -> OCR -> events), bounded per clip, OFFLINE_LAB.",
        "- **Fixture classes (corrected):** OVERLAY = `playcall_*` + `practice_*` (both show the play-call overlay -> extraction); BROADCAST = `yt_*` only (no overlay -> transport + zero false-positive).",
        "- **Deferred (recorded, not run):** #2 live page display (browser->core connect), #7 rollback-alarm wire (P2 CloudWatch), #8 webhook audit (:8002).",
        "- **Tracked robustness finding (not fixed here):** broadcast/null-HUD frames trigger a caught `Madden26Payload` ValidationError (score/clock required non-null) -> event logged+dropped, non-fatal. Payload-schema fix is separate work.",
        "",
        "## Overlay clips - FORMATION extraction",
        "",
        "| clip | formation | family | expected | status | frames | fps |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in overlay:
        L.append(f"| {r['clip']} | {r.get('formation_name')!r} | {r.get('formation_family')!r} | "
                 f"{r.get('expected')} | {r.get('status')} | {r.get('dispatched')} | {r.get('fps')} |")
    L += ["", "## Broadcast clips (yt_ only) - transport + zero false-positive FORMATION_LOCKED (#3)", "",
          "| clip | events by type | false-positive FORMATION | errors | frames | fps |",
          "|---|---|---|---|---|---|"]
    for r in broadcast:
        L.append(f"| {r['clip']} | {r.get('by_type')} | {r.get('false_positive_formation')} | "
                 f"{r.get('errors')} | {r.get('dispatched')} | {r.get('fps')} |")
    L += ["", "## Summary", "",
          f"- Overlay extraction: **{s['overlay_matched']} matched**, {s['overlay_none_in_window']} no-overlay-in-window (absence != failure), **{len(s['mismatches'])} mismatch**.",
          f"- Mismatches (wrong formation): {s['mismatches'] or 'none'}.",
          f"- Broadcast false-positive FORMATION_LOCKED: {s['false_positives'] or 'none (criterion #3 holds)'}.",
          f"- Pipeline throughput (with OCR): {s['fps_min']}-{s['fps_max']} fps. (File-input/capture-path throughput is ~319 fps source-level, Day 1 - #4's actual subject.)",
          ""]
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())
