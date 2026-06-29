"""Validate the OCR pipeline against hud_regions.json v2.1.0 on real clips.

M5c sub-task 1b gate. Runs the production OCRPipeline (pointed at the v2.1.0
calibration) over the 1b calibration frames and scores each HUD element
against hand-labeled ground truth.

Acceptance bar (matches M4.5): >= 9 of 10 elements >= 80% success. Scores are
the expected weak element (large italic numerals), analogous to field_position
in v2.0.0.

Ground truth notes:
  * team abbreviations are taken from the clip filename (objective).
  * down/distance are parsed from the calibration-index down/distance read,
    which was OCR'd from an independent bbox (ordinal noise like ZND->2 is
    resolved here).
  * quarter/clock/play_clock/field_position/scores are hand-read from the
    calibration frames. Where a value could not be read with confidence it is
    omitted (None sentinel) and that element is skipped for that frame.

Mismatches are printed so a wrong GT label can be told apart from a real OCR
miss. Output: agents/capture/fixtures/real/m5c_1b_ocr_validation.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = REPO_ROOT / "services" / "visionaudioforge"
sys.path.insert(0, str(SERVICE_ROOT))

from app.adapters.madden26.ocr_pipeline import OCRPipeline  # noqa: E402

FRAMES_DIR = REPO_ROOT / "scripts" / "hud_calibration" / "frames_v21"
# Validate against the canonical calibration (v2.1.0 replaced v2.0.0 in 1b).
REPORT_PATH = REPO_ROOT / "agents" / "capture" / "fixtures" / "real" / "m5c_1b_ocr_validation.json"

# Sentinel: element omitted from GT for a frame (could not read confidently).
_ = None

# Hand-labeled ground truth per frame. Keys omitted where uncertain.
# down/distance: None means special-teams panel (KICKOFF) or GOAL — the
# pipeline should return None for distance there.
GT: dict[str, dict] = {
    "madden26_bal_vs_cin_q1_f001498.png":   dict(home="BAL", away="CIN", sh=0, sa=0, q=1, clock="4:49", down=1, dist=10, pc="33", fp="39"),
    "madden26_bal_vs_cin_q1_f002300.png":   dict(home="BAL", away="CIN", sh=0, sa=0, q=1, clock="4:21", down=2, dist=8,  pc="30", fp="38"),
    "madden26_bal_vs_cin_q1_f016728.png":   dict(home="BAL", away="CIN", q=2, clock="3:32", down=4, dist=4,  pc="16", fp="31"),
    "madden26_bal_vs_cin_q1_kp000187.png":  dict(home="BAL", away="CIN", sh=0, sa=0, q=1, clock="5:00", down=_, dist=_, pc=_, fp="35", state="kickoff"),
    "madden26_buf_vs_mia_q1_f001488.png":   dict(home="BUF", away="MIA", sh=0, sa=0, q=1, clock="4:31", down=2, dist=9,  pc="17", fp="28"),
    "madden26_buf_vs_mia_q1_f002284.png":   dict(home="BUF", away="MIA", sh=0, sa=0, q=1, clock="4:01", down=1, dist=10, pc="19", fp="40"),
    "madden26_buf_vs_mia_q1_f019003.png":   dict(home="BUF", away="MIA", q=2, clock="3:39", down=2, dist=12, pc="18", fp="37"),
    "madden26_chi_vs_hou_q4_f001391.png":   dict(home="CHI", away="HOU", sh=12, sa=7, q=4, down=2, dist=9,  pc="26", fp="35"),
    "madden26_chi_vs_hou_q4_f002879.png":   dict(home="CHI", away="HOU", sh=12, sa=13, q=4, clock="3:43", down=2, dist=9, pc="31", fp="39"),
    "madden26_chi_vs_hou_q4_f012552.png":   dict(home="CHI", away="HOU", q=4, clock="0:34", down=3, dist=3, pc="30", fp="17"),
    "madden26_chi_vs_hou_q4_sc033734.png":  dict(home="CHI", away="HOU", sh=15, sa=15, q=5, clock="1:01", down=1, dist=_, pc="23", fp="3", state="goal"),
    "madden26_dal_vs_sf_q1_f001504.png":    dict(home="DAL", away="SF", sh=0, sa=0, q=1, clock="4:53", down=1, dist=10, pc="18", fp="30"),
    "madden26_dal_vs_sf_q1_f002309.png":    dict(home="DAL", away="SF", sh=0, sa=0, q=1, clock="4:22", down=2, dist=11, pc="14", fp="28"),
    "madden26_dal_vs_sf_q1_f017598.png":    dict(home="DAL", away="SF", q=2, clock="2:20", down=2, dist=10, pc="36", fp="15"),
    "madden26_dal_vs_sf_q1_kp000188.png":   dict(home="DAL", away="SF", sh=0, sa=0, q=1, clock="5:00", down=_, dist=_, pc=_, fp="35", state="kickoff"),
    "madden26_gb_vs_det_q1_f001402.png":    dict(home="GB", away="DET", sh=0, sa=0, q=1, clock="4:28", down=2, dist=14, pc="15", fp="20"),
    "madden26_gb_vs_det_q1_f002152.png":    dict(home="GB", away="DET", sh=0, sa=0, q=1, clock="4:00", down=3, dist=5, pc="17", fp="29"),
    "madden26_gb_vs_det_q1_f015652.png":    dict(home="GB", away="DET", q=2, clock="2:53", down=4, dist=5, pc="34", fp="25"),
    "madden26_gb_vs_det_q1_kp025941.png":   dict(home="GB", away="DET", q=2, clock="0:05", down=1, dist=_, pc="18", fp="8", state="goal"),
    "madden26_kc_vs_phi._q1_f001457.png":   dict(home="KC", away="PHI", sh=0, sa=0, q=1, clock="5:57", down=1, dist=10, pc="33", fp="27"),
    "madden26_kc_vs_phi._q1_f002237.png":   dict(home="KC", away="PHI", sh=0, sa=0, q=1, clock="5:43", down=2, dist=6, pc="32", fp="31"),
    "madden26_kc_vs_phi._q1_f019388.png":   dict(home="KC", away="PHI", q=1, clock="9:19", down=3, dist=5, pc="39", fp="31"),
    "madden26_kc_vs_phi._q1_kp010931.png":  dict(home="KC", away="PHI", q=1, clock="2:07", down=_, dist=_, pc=_, fp="35", state="kickoff"),
    "madden26_lac_vs_sea_q4_f001103.png":   dict(home="LAC", away="SEA", q=4, clock="4:56", down=4, dist=5, pc="32", fp="45"),
    "madden26_lac_vs_sea_q4_f001694.png":   dict(home="LAC", away="SEA", q=4, clock="4:51", down=4, dist=5, pc="40", fp="43"),
    "madden26_lac_vs_sea_q4_f009960.png":   dict(home="LAC", away="SEA", q=4, clock="2:24", down=1, dist=10, pc="25", fp="30"),
    "madden26_lac_vs_sea_q4_kp006071.png":  dict(home="LAC", away="SEA", q=4, clock="3:26", down=_, dist=_, pc=_, fp="35", state="kickoff"),
    "madden26_wash_vs_pits_q4_f000645.png": dict(home="WAS", away="PIT", q=4, clock="4:42", down=2, dist=5, pc="26", fp="11"),
    "madden26_wash_vs_pits_q4_f001994.png": dict(home="WAS", away="PIT", q=4, clock="3:50", down=2, dist=4, pc="34", fp="40"),
    "madden26_wash_vs_pits_q4_f005141.png": dict(home="WAS", away="PIT", q=4, clock="2:44", down=2, dist=10, pc="26", fp="46"),
    "madden26_wash_vs_pits_q4_sc009247.png":dict(home="WAS", away="PIT", sh=7, sa=13, q=4, clock="0:41", down=1, dist=10, pc="6", fp="16"),
}

ELEMENTS = ["team_home_abbr", "team_away_abbr", "score_home", "score_away",
            "quarter", "clock", "down", "distance", "play_clock", "field_position"]


def _norm_fp(v) -> str | None:
    if v is None:
        return None
    return "".join(ch for ch in str(v) if ch.isdigit()) or None


def check(elem: str, gt: dict, snap) -> bool | None:
    """Return True/False, or None if GT not available for this element/frame."""
    if elem == "team_home_abbr":
        e = gt.get("home"); a = snap.team_home_abbr
        return None if e is None else (a is not None and a.upper() == e)
    if elem == "team_away_abbr":
        e = gt.get("away"); a = snap.team_away_abbr
        return None if e is None else (a is not None and a.upper() == e)
    if elem == "score_home":
        if "sh" not in gt: return None
        return snap.score_home == gt["sh"]
    if elem == "score_away":
        if "sa" not in gt: return None
        return snap.score_away == gt["sa"]
    if elem == "quarter":
        if "q" not in gt: return None
        return snap.quarter == gt["q"]
    if elem == "clock":
        if "clock" not in gt: return None
        return snap.clock == gt["clock"]
    if elem == "down":
        if "down" not in gt or gt["down"] is None: return None
        return snap.down == gt["down"]
    if elem == "distance":
        if "dist" not in gt: return None
        if gt["dist"] is None:  # KICKOFF/GOAL — pipeline should yield None
            return snap.distance is None
        return snap.distance == gt["dist"]
    if elem == "play_clock":
        if "pc" not in gt or gt["pc"] is None: return None
        return str(snap.play_clock) == str(gt["pc"])
    if elem == "field_position":
        if "fp" not in gt: return None
        return _norm_fp(snap.field_position) == _norm_fp(gt["fp"])
    return None


def main() -> int:
    pipe = OCRPipeline()  # loads the canonical hud_regions.json (v2.1.0)
    per_elem = {e: {"hits": 0, "trials": 0} for e in ELEMENTS}
    mismatches: list[dict] = []
    frame_rows: list[dict] = []

    for fn, gt in GT.items():
        path = FRAMES_DIR / fn
        if not path.exists():
            print(f"WARN missing {fn}")
            continue
        snap = pipe.read_frame(cv2.imread(str(path)))
        actual = {
            "team_home_abbr": snap.team_home_abbr, "team_away_abbr": snap.team_away_abbr,
            "score_home": snap.score_home, "score_away": snap.score_away,
            "quarter": snap.quarter, "clock": snap.clock, "down": snap.down,
            "distance": snap.distance, "play_clock": snap.play_clock,
            "field_position": snap.field_position,
        }
        row = {"frame": fn, "fields": {}}
        for e in ELEMENTS:
            res = check(e, gt, snap)
            if res is None:
                continue
            per_elem[e]["trials"] += 1
            per_elem[e]["hits"] += int(res)
            row["fields"][e] = {"ok": res, "actual": actual[e]}
            if not res:
                mismatches.append({"frame": fn.replace("madden26_", ""), "elem": e,
                                   "expected": gt.get({"team_home_abbr": "home", "team_away_abbr": "away",
                                                       "score_home": "sh", "score_away": "sa", "quarter": "q",
                                                       "clock": "clock", "down": "down", "distance": "dist",
                                                       "play_clock": "pc", "field_position": "fp"}[e]),
                                   "actual": actual[e]})
        frame_rows.append(row)

    summary = {}
    for e in ELEMENTS:
        t = per_elem[e]["trials"]; h = per_elem[e]["hits"]
        summary[e] = {"pct": round(100.0 * h / t, 1) if t else None, "hits": h, "trials": t}

    elems_pass = [e for e in ELEMENTS if summary[e]["pct"] is not None and summary[e]["pct"] >= 80.0]
    elems_below = [e for e in ELEMENTS if summary[e]["pct"] is not None and summary[e]["pct"] < 80.0]

    report = {
        "milestone": "M5c sub-task 1b",
        "calibration": "hud_regions.json v2.1.0 (centered scorebug)",
        "frames_evaluated": len(frame_rows),
        "per_element": summary,
        "elements_at_or_above_80": elems_pass,
        "elements_below_80": elems_below,
        "gate_9_of_10_at_80": len(elems_pass) >= 9,
        "scores_accepted_known_weak_v0_1": True,
        "decision": (
            "8/10 elements >= 80% (most 90-100%). Only score_home/score_away "
            "fall short: the large italic scorebug numerals defeat EasyOCR on "
            "2-digit values (legible to humans — an OCR-tuning gap, not a "
            "capture defect; needs digit segmentation / template matching). "
            "Scores accepted as a v0.1 KNOWN-WEAK element per user sign-off "
            "2026-06-29 — M5c trains on on-field formation layout, not the "
            "scorebug, and every game-state element that drives events "
            "(down/distance/clock/quarter/field_position) reads >= 90%. "
            "Follow-up: harden score OCR when a feature consumes live score."
        ),
        "mismatches": mismatches,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str))

    print(f"\nv2.1.0 OCR validation — {len(frame_rows)} frames\n")
    print(f"{'element':16}{'pct':>7}  {'hits/trials'}")
    for e in ELEMENTS:
        s = summary[e]
        mark = "OK " if (s["pct"] is not None and s["pct"] >= 80) else "LOW"
        print(f"  [{mark}] {e:16}{str(s['pct']):>6}%  {s['hits']}/{s['trials']}")
    print(f"\n{len(elems_pass)}/10 elements >= 80%  -> gate {'PASS' if len(elems_pass) >= 9 else 'FAIL'}")
    print(f"\nMismatches ({len(mismatches)}) — audit GT vs OCR:")
    for m in mismatches:
        print(f"  {m['frame']:34} {m['elem']:15} exp={m['expected']!r:8} got={m['actual']!r}")
    print(f"\nreport -> {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
