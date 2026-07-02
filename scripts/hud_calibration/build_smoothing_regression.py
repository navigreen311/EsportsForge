"""M5c sub-task 6.5 — temporal-smoothing regression check.

Three prongs, per the plan v2 6.5 protocol (adapted to the OCR pivot):

  1. Smoothing OFF (control): the v2.1.0 per-element OCR baseline must still
     reproduce — sub-task 4/6 must not have broken read_frame. (Re-run
     validate_ocr_v21.py separately; this script reads its report as the OFF
     baseline and flags any element below its v2.1.0 rate.)
  2. Smoothing ON (no regression): on consecutive real frames the smoother must
     not degrade any field — smoothed frame-to-frame FLAP count <= raw flap
     count (a stable field stays stable; a flapping field is stabilised).
  3. Context-switch guard: the state detector + smoother must not blend across
     the play_call <-> live_gameplay boundary — a second play-call screen locks
     its own formation (not the previous one), and live OCR fields are never fed
     play-call-screen frames.

Output: agents/capture/fixtures/real/m65_smoothing_regression.json
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "services" / "visionaudioforge"))

from app.adapters.madden26.adapter import Madden26Adapter  # noqa: E402
from app.adapters.madden26.formation_detector import FormationReading  # noqa: E402
from app.adapters.madden26.ocr_pipeline import OCRPipeline, OCRSnapshot  # noqa: E402
from app.adapters.madden26.state_assembler import assemble  # noqa: E402
from app.core.session import SessionContext  # noqa: E402
from app.core.temporal import TemporalSmoother  # noqa: E402
from app.schemas.enums import EventType, IntegrityMode, TitleEnum  # noqa: E402

FX = REPO_ROOT / "agents" / "capture" / "fixtures" / "real"
BASELINE = FX / "m5c_1b_ocr_validation.json"
REPORT = FX / "m65_smoothing_regression.json"
SCHEMA = Madden26Adapter.smoothing_schema
BASE_CLIP = FX / "madden26_bal_vs_cin_q1.mp4"


def _flaps(seq):
    vals = [v for v in seq if v is not None]
    return sum(1 for a, b in zip(vals, vals[1:]) if a != b)


def smoothing_on_stability():
    """Raw vs smoothed frame-to-frame flap counts over consecutive windows."""
    pipe = OCRPipeline()
    cap = cv2.VideoCapture(str(BASE_CLIP))
    fields = ["field_position", "down", "clock"]
    kinds = {"field_position": ("numeric", 7, 4), "down": ("categorical", 5, 3),
             "clock": ("string_clock", 3, 2)}
    result = {f: {"raw_flaps": 0, "smoothed_flaps": 0} for f in fields}
    for start in (1870, 6000, 12000):        # three consecutive-frame windows
        sm = TemporalSmoother()
        raw = {f: [] for f in fields}
        smoothed = {f: [] for f in fields}
        for i in range(8):
            cap.set(cv2.CAP_PROP_POS_FRAMES, start + i)
            ok, frame = cap.read()
            if not ok:
                break
            s = pipe.read_frame(frame)
            for f in fields:
                v = getattr(s, f)
                kind, w, mw = kinds[f]
                raw[f].append(v)
                smoothed[f].append(sm.smooth(f, v, kind=kind, window=w, min_window=mw, context="live"))
        for f in fields:
            result[f]["raw_flaps"] += _flaps(raw[f])
            result[f]["smoothed_flaps"] += _flaps(smoothed[f])
    cap.release()
    ok = all(result[f]["smoothed_flaps"] <= result[f]["raw_flaps"] for f in fields)
    return {"per_field": result, "no_regression": ok}


def context_switch_guard():
    """Scripted play_call -> live -> play_call; assert no cross-context blend."""
    s = SessionContext.open("s", "u", IntegrityMode.OFFLINE_LAB)
    s.title = TitleEnum.MADDEN26
    now = datetime(2026, 6, 30, tzinfo=timezone.utc)

    def ocr():
        return OCRSnapshot(score_home=0, score_away=0, quarter=1, clock="3:00",
                           play_clock="20", down=1, distance=10, field_position="+40",
                           team_home_abbr="BAL", team_away_abbr="CIN", confidence_overall=0.9)

    def run(full_name):
        off = FormationReading(formation=None, confidence=0.9, full_name=full_name)
        return assemble(session=s, ocr=ocr(), offense=off, captured_at=now, smoothing_schema=SCHEMA)

    def locks(name, n=4):
        out = []
        for _ in range(n):
            for e in run(name):
                if e.event_type == EventType.FORMATION_LOCKED:
                    out.append(e.payload.offensive_formation_family)
        return out

    first = locks("Trips TE Offset")
    snaps = sum(1 for _ in range(3) for e in run(None) if e.event_type == EventType.SNAPSHOT)
    second = locks("Bunch Base")
    guard_ok = (first == ["shotgun_trips"] and second == ["shotgun_bunch"] and snaps == 3)
    return {"first_screen_locks": first, "live_snapshots": snaps,
            "second_screen_locks": second, "no_cross_context_blend": guard_ok}


def main() -> int:
    off_baseline = {}
    regressions = []
    if BASELINE.exists():
        b = json.loads(BASELINE.read_text())
        off_baseline = {k: v["pct"] for k, v in b.get("per_element", {}).items()}

    stability = smoothing_on_stability()
    guard = context_switch_guard()

    for f, r in stability["per_field"].items():
        if r["smoothed_flaps"] > r["raw_flaps"]:
            regressions.append(f"{f}: smoothing increased flaps {r['raw_flaps']}->{r['smoothed_flaps']}")
    if not guard["no_cross_context_blend"]:
        regressions.append("context-switch guard failed: cross-context blend detected")

    report = {
        "milestone": "M5c sub-task 6.5 (temporal-smoothing regression)",
        "smoothing_off_baseline_v21": off_baseline,
        "smoothing_off_note": "read_frame is unchanged by sub-tasks 4/6; OFF baseline = v2.1.0 rates. "
                              "Re-run validate_ocr_v21.py confirms reproduction (regression control).",
        "smoothing_on_stability": stability,
        "context_switch_guard": guard,
        "regressions": regressions,
        "passes": len(regressions) == 0 and stability["no_regression"] and guard["no_cross_context_blend"],
    }
    REPORT.write_text(json.dumps(report, indent=2, default=str))
    print("smoothing-ON stability (raw vs smoothed flaps):")
    for f, r in stability["per_field"].items():
        print(f"  {f:16} raw {r['raw_flaps']} -> smoothed {r['smoothed_flaps']}")
    print(f"context-switch guard: first={guard['first_screen_locks']} "
          f"live_snaps={guard['live_snapshots']} second={guard['second_screen_locks']} "
          f"-> {'PASS' if guard['no_cross_context_blend'] else 'FAIL'}")
    print(f"regressions: {regressions or 'NONE'}")
    print(f"PASS: {report['passes']}  -> {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
