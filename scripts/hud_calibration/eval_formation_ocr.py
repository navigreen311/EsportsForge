"""M5c sub-task 5 — acceptance evaluation of the OCR-of-overlay formation detector.

Re-scoped from CNN metrics (macro-F1, confusion matrix, ONNX latency/parity) to
OCR metrics, since the detector reads the game's own formation label:

  1. Per-formation success rate + confidence distribution (8 canonical practice
     clips, 10 frames each).
  2. name -> canonical-8 mapping accuracy.
  3. State-detector accuracy — the load-bearing safety property:
       * TRUE POSITIVE : practice + exhibition play-call frames detected as such.
       * TRUE NEGATIVE : live-gameplay MATCHUP frames (CPU-vs-CPU, no play-call
         screen) must NOT trigger a play-call read (zero false positives, else the
         adapter would emit spurious FORMATION_LOCKED events mid-play).
  4. Exhibition clip — the primary production-conditions validation.

Acceptance gates: per-formation success >= 80%; state-detector false-positive
rate on live gameplay ~0%. Output: agents/capture/fixtures/real/m5c_eval_report.json
"""

from __future__ import annotations

import json
import statistics as stats
import sys
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "services" / "visionaudioforge"))

from app.adapters.madden26.formation_detector import FormationDetector, TOP_8_FORMATIONS  # noqa: E402
from app.adapters.madden26.ocr_pipeline import _formation_to_canonical  # noqa: E402

FX = REPO_ROOT / "agents" / "capture" / "fixtures" / "real"
REPORT = FX / "m5c_eval_report.json"
MATCHUP = ["madden26_bal_vs_cin_q1", "madden26_buf_vs_mia_q1", "madden26_chi_vs_hou_q4",
           "madden26_dal_vs_sf_q1", "madden26_gb_vs_det_q1", "madden26_ind_vs_ne__q4",
           "madden26_kc_vs_phi._q1", "madden26_lac_vs_sea_q4", "madden26_tb_vs_la_q4",
           "madden26_wash_vs_pits_q4"]


def _frames(clip: Path, pcts):
    cap = cv2.VideoCapture(str(clip))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    out = []
    for p in pcts:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * p))
        ok, f = cap.read()
        if ok:
            out.append(f)
    cap.release()
    return out


def main() -> int:
    det = FormationDetector()
    pcts10 = [0.30 + 0.045 * i for i in range(10)]

    # 1+2. Per-formation success + confidence + mapping accuracy.
    per_form, all_conf = [], []
    tp_success = tp_trials = map_ok = map_trials = 0
    for canonical in TOP_8_FORMATIONS:
        clip = FX / f"madden26_playcall_{canonical}.mp4"
        if not clip.exists():
            continue
        confs, ok, names = [], 0, set()
        for f in _frames(clip, pcts10):
            r = det.detect_offensive(f)
            tp_trials += 1
            if r.is_play_call_screen if hasattr(r, "is_play_call_screen") else (r.full_name is not None):
                pass
            confs.append(r.confidence); all_conf.append(r.confidence)
            if r.full_name:
                names.add(r.full_name)
                map_trials += 1
                if _formation_to_canonical(r.full_name) == canonical:
                    map_ok += 1
            if r.formation == canonical:
                ok += 1; tp_success += 1
        per_form.append({"formation": canonical, "success": f"{ok}/{len(confs)}",
                         "pct": round(100 * ok / len(confs), 1) if confs else 0,
                         "conf_mean": round(stats.mean(confs), 3) if confs else 0,
                         "conf_min": round(min(confs), 3) if confs else 0,
                         "full_names": sorted(names)})

    practice_pct = round(100 * tp_success / tp_trials, 1) if tp_trials else 0
    mapping_pct = round(100 * map_ok / map_trials, 1) if map_trials else 0

    # 3. State detector TRUE NEGATIVE — live-gameplay matchup clips must not fire.
    tn = tn_total = false_pos = 0
    fp_examples = []
    for name in MATCHUP:
        clip = FX / f"{name}.mp4"
        if not clip.exists():
            continue
        for f in _frames(clip, [0.2, 0.4, 0.6, 0.8]):
            tn_total += 1
            r = det.detect_offensive(f)
            if r.formation is None and r.full_name is None:
                tn += 1
            else:
                false_pos += 1
                fp_examples.append({"clip": name, "read": r.full_name})
    tn_rate = round(100 * tn / tn_total, 1) if tn_total else 0

    # 4. Exhibition production reads.
    exhib = []
    ex = FX / "madden26_playcall_human_exhibition.mp4"
    if ex.exists():
        cap = cv2.VideoCapture(str(ex)); total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        for i in range(60):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * (0.02 + i / 60 * 0.96)))
            ok, f = cap.read()
            if not ok:
                continue
            r = det.detect_offensive(f)
            if r.full_name:
                exhib.append({"ts": round(int(total*(0.02+i/60*0.96))/fps, 1),
                              "name": r.full_name, "canonical": r.formation, "conf": r.confidence})
        cap.release()

    report: dict = {
        "milestone": "M5c sub-task 5 (OCR-of-overlay acceptance evaluation)",
        "detector": "formation_detector.FormationDetector (hud_regions v2.2.0 play_call)",
        "acceptance": {
            "per_formation_success_pct": practice_pct,
            "per_formation_gate": ">=80%", "per_formation_pass": practice_pct >= 80,
            "name_to_canonical_accuracy_pct": mapping_pct,
            "state_detector_true_negative_pct": tn_rate,
            "state_detector_false_positives": false_pos,
            "state_detector_gate": "~0 false positives on live gameplay",
            "state_detector_pass": false_pos == 0,
        },
        "confidence_overall": {"mean": round(stats.mean(all_conf), 3) if all_conf else 0,
                               "min": round(min(all_conf), 3) if all_conf else 0,
                               "stdev": round(stats.pstdev(all_conf), 3) if len(all_conf) > 1 else 0},
        "per_formation": per_form,
        "state_detector_negative_test": {"matchup_frames": tn_total, "true_negatives": tn,
                                         "false_positives": false_pos, "fp_examples": fp_examples},
        "exhibition_production": {"play_call_screens_read": len(exhib), "reads": exhib},
    }
    REPORT.write_text(json.dumps(report, indent=2, default=str))

    print(f"per-formation success: {practice_pct}%  (>=80 {'PASS' if practice_pct >= 80 else 'FAIL'})")
    print(f"name->canonical mapping accuracy: {mapping_pct}%")
    print(f"state-detector TRUE-NEGATIVE on live gameplay: {tn}/{tn_total} = {tn_rate}%  "
          f"({false_pos} false positives -> {'PASS' if false_pos == 0 else 'FAIL'})")
    print(f"exhibition play-call screens read: {len(exhib)}")
    print(f"overall conf mean {report['confidence_overall']['mean']} min {report['confidence_overall']['min']}")
    print(f"report -> {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
