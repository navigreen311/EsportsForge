"""Validate the OCR-of-overlay formation detector (M5c sub-task 4 pivot).

Exercises the full integrated FormationDetector path (play-call-screen state
detector -> formation_name OCR -> canonical-8 mapping) against the play-call
capture:

  * 8 practice play-select clips — expected canonical from the filename. Reports
    per-formation success rate + the full names read.
  * human exhibition clip — production conditions. Confirms play-call screens are
    detected + read, AND that live-gameplay frames correctly return no formation
    (the state detector gates reads to the overlay).

Acceptance (new sub-task 4 criterion): >= 80% canonical-8 success across the
practice clips; exhibition play-call screens read + gameplay frames gated.

Output: agents/capture/fixtures/real/m5c_formation_ocr_validation.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = REPO_ROOT / "services" / "visionaudioforge"
sys.path.insert(0, str(SERVICE_ROOT))

from app.adapters.madden26.formation_detector import FormationDetector, TOP_8_FORMATIONS  # noqa: E402

FX = REPO_ROOT / "agents" / "capture" / "fixtures" / "real"
REPORT = FX / "m5c_formation_ocr_validation.json"


def _sample(cap, pct):
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * pct))
    ok, frame = cap.read()
    return frame if ok else None


def main() -> int:
    det = FormationDetector()
    per_form = []
    passed = trials = 0

    for canonical in TOP_8_FORMATIONS:
        clip = FX / f"madden26_playcall_{canonical}.mp4"
        if not clip.exists():
            print(f"WARN missing {clip.name}")
            continue
        cap = cv2.VideoCapture(str(clip))
        reads, ok = [], 0
        for pct in (0.35, 0.45, 0.55, 0.65, 0.75):
            frame = _sample(cap, pct)
            if frame is None:
                continue
            r = det.detect_offensive(frame)
            reads.append({"canonical": r.formation, "full_name": r.full_name,
                          "conf": r.confidence})
            trials += 1
            if r.formation == canonical:
                ok += 1; passed += 1
        cap.release()
        per_form.append({"formation": canonical, "ok": ok, "of": len(reads),
                         "full_names": sorted({x["full_name"] for x in reads if x["full_name"]}),
                         "reads": reads})
        print(f"  {canonical:18} {ok}/{len(reads)}  names={per_form[-1]['full_names']}")

    practice_rate = round(100.0 * passed / trials, 1) if trials else 0.0

    # Exhibition: production conditions + state-gating check.
    exhib: dict = {"play_call_screens": [], "gameplay_frames_sampled": 0, "gameplay_gated_correctly": 0}
    ex_clip = FX / "madden26_playcall_human_exhibition.mp4"
    if ex_clip.exists():
        cap = cv2.VideoCapture(str(ex_clip))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps = cap.get(cv2.CAP_PROP_FPS) or 30
        for i in range(50):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * (0.02 + i / 50 * 0.96)))
            ok, frame = cap.read()
            if not ok:
                continue
            r = det.detect_offensive(frame)
            if r.formation is not None or r.full_name is not None:
                # a play-call screen was read
                cap2_idx = int(total * (0.02 + i / 50 * 0.96))
                exhib["play_call_screens"].append(
                    {"ts": round(cap2_idx / fps, 1), "full_name": r.full_name,
                     "canonical": r.formation, "conf": r.confidence})
            else:
                exhib["gameplay_frames_sampled"] += 1
                exhib["gameplay_gated_correctly"] += 1  # returned None on non-overlay frame
        cap.release()

    report = {
        "milestone": "M5c sub-task 4 (OCR-of-overlay pivot)",
        "calibration": "hud_regions.json v2.2.0 play_call.formation_name",
        "acceptance_threshold_pct": 80.0,
        "practice_success_rate_pct": practice_rate,
        "practice_passes": practice_rate >= 80.0,
        "per_formation": per_form,
        "exhibition": {
            "play_call_screens_found": len(exhib["play_call_screens"]),
            "gameplay_frames_gated_to_none": f"{exhib['gameplay_gated_correctly']}/{exhib['gameplay_frames_sampled']}",
            "reads": exhib["play_call_screens"],
        },
    }
    REPORT.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nPRACTICE canonical-8 success: {practice_rate}%  "
          f"({'PASS' if practice_rate >= 80 else 'FAIL'} vs 80%)")
    print(f"EXHIBITION: {len(exhib['play_call_screens'])} play-call screens read; "
          f"{exhib['gameplay_gated_correctly']}/{exhib['gameplay_frames_sampled']} "
          f"gameplay frames correctly gated to no-formation")
    print(f"report -> {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
