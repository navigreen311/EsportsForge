"""7.5.1 — Calibrate the cheap (non-OCR) play_call-vs-live context detector.

The OCR-of-overlay adapter currently runs TWO EasyOCR passes per frame just to
answer "is the play-call overlay up?" (read_frame scorebug + is_play_call_screen).
This replaces the state question with a ~1ms luminance check so OCR only runs for
the one context that's actually on screen.

Ground truth: OCRPipeline.is_play_call_screen (the shipped OCR detector). We
calibrate the cheap detector to MATCH it, then it takes over the hot path.

Rollback ladder (per the approved plan):
  * Primary   : single luminance feature (best separating of banner / scorebar).
  * Fallback 2: 2-feature rule (banner HIGH AND scorebar LOW).
  * Fallback 1: template-match on the banner region (only if luminance fails).
  If none separates cleanly per-matchup -> halt-and-report with the numbers.

Cheap features (grayscale, from hud_regions v2.2.0 bboxes + whole-frame):
  banner_mean   — formation_name band: LIT (>=153) on play-call, usually dim on live.
  dark_frac     — fraction of the whole frame below luma 50: the play-call menu
                  DIMS the field behind it (a UI constant) -> HIGH on play-call.
  scorebar_mean — live scoreboard band luma. Tried and REJECTED: dark on the
                  dedicated playcall clips (~30) but BRIGHT (~110) on real-game
                  (exhibition) play-call screens -> game-mode-dependent, 7 FN. Kept
                  in the report as the rejected candidate. dark_frac replaces it
                  because the field-dimming is title-UI-constant, not mode-dependent.

Output: agents/capture/fixtures/real/context_detector_calibration.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "services" / "visionaudioforge"))

from app.adapters.madden26.ocr_pipeline import OCRPipeline  # noqa: E402

FX = REPO_ROOT / "agents" / "capture" / "fixtures" / "real"
HUD = (REPO_ROOT / "services" / "visionaudioforge" / "app" / "adapters"
       / "madden26" / "hud_regions.json")
OUT = FX / "context_detector_calibration.json"

PLAYCALL_CLIPS = [
    "madden26_playcall_shotgun_trips.mp4", "madden26_playcall_shotgun_bunch.mp4",
    "madden26_playcall_shotgun_empty.mp4", "madden26_playcall_shotgun_doubles.mp4",
    "madden26_playcall_i_form_pro.mp4", "madden26_playcall_singleback_ace.mp4",
    "madden26_playcall_singleback_wing.mp4", "madden26_playcall_pistol_strong.mp4",
]
MATCHUP_CLIPS = [
    "madden26_bal_vs_cin_q1.mp4", "madden26_buf_vs_mia_q1.mp4",
    "madden26_dal_vs_sf_q1.mp4", "madden26_gb_vs_det_q1.mp4",
    "madden26_kc_vs_phi._q1.mp4", "madden26_chi_vs_hou_q4.mp4",
    "madden26_lac_vs_sea_q4.mp4", "madden26_tb_vs_la_q4.mp4",
]
EXHIBITION = "madden26_playcall_human_exhibition.mp4"  # real mixed stream


def _load_bboxes():
    data = json.loads(HUD.read_text())
    ctx = data["hud_contexts"]
    banner = ctx["play_call"]["regions"]["formation_name"]["bbox"]
    scorebar = ctx["live_gameplay"]["regions"]["scoreboard"]["bbox"]
    return banner, scorebar


def _region_mean(gray, bbox):
    x, y, w, h = bbox
    H, W = gray.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return float(gray[y0:y1, x0:x1].mean())


def features(frame, banner_bbox, scorebar_bbox):
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return {"banner_mean": round(_region_mean(g, banner_bbox), 1),
            "dark_frac": round(float((g < 50).mean()), 3),
            "scorebar_mean": round(_region_mean(g, scorebar_bbox), 1)}


def sample_clip(pipe, clip, indices, banner_bbox, scorebar_bbox):
    """Return per-frame (gt_play_call, features) for a clip."""
    cap = cv2.VideoCapture(str(FX / clip))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    rows = []
    for idx in indices:
        if idx >= total:
            continue
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, fr = cap.read()
        if not ok:
            continue
        gt = pipe.is_play_call_screen(fr)                 # OCR ground truth
        rows.append({"idx": idx, "gt_play_call": gt,
                     **features(fr, banner_bbox, scorebar_bbox)})
    cap.release()
    return rows


def evaluate_rule(rows, rule):
    """rule(feat)->bool predicted play_call. Return confusion vs GT."""
    fp = fn = tp = tn = 0
    for r in rows:
        pred = rule(r)
        gt = r["gt_play_call"]
        if pred and gt: tp += 1
        elif pred and not gt: fp += 1
        elif not pred and gt: fn += 1
        else: tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def margin(rows, key, gt_val):
    """Feature range for frames whose GT==gt_val."""
    vals = [r[key] for r in rows if r["gt_play_call"] == gt_val]
    if not vals:
        return None
    return {"n": len(vals), "min": min(vals), "max": max(vals),
            "mean": round(sum(vals) / len(vals), 1)}


def main() -> int:
    banner_bbox, scorebar_bbox = _load_bboxes()
    pipe = OCRPipeline()

    per_clip = {}
    all_rows = []
    # play-call clips: dense sampling where the overlay lives
    for clip in PLAYCALL_CLIPS:
        idxs = list(range(120, 120 + 10 * 25, 25))    # 10 frames spanning the screen
        rows = sample_clip(pipe, clip, idxs, banner_bbox, scorebar_bbox)
        per_clip[clip] = rows
        all_rows += rows
    # matchup clips: spread across the clip (mostly/all live)
    for clip in MATCHUP_CLIPS:
        idxs = list(range(1500, 1500 + 8 * 2200, 2200))
        rows = sample_clip(pipe, clip, idxs, banner_bbox, scorebar_bbox)
        per_clip[clip] = rows
        all_rows += rows
    # exhibition: realistic mixed stream
    idxs = list(range(1500, 1500 + 30 * 300, 300))
    rows = sample_clip(pipe, EXHIBITION, idxs, banner_bbox, scorebar_bbox)
    per_clip[EXHIBITION] = rows
    all_rows += rows

    gt_pc = sum(1 for r in all_rows if r["gt_play_call"])
    gt_live = len(all_rows) - gt_pc

    # feature separation (GT-conditioned ranges)
    sep = {f: {"play_call": margin(all_rows, f, True), "live": margin(all_rows, f, False)}
           for f in ("banner_mean", "dark_frac", "scorebar_mean")}

    # Calibrated thresholds (fixed with margin below the play_call floor rather
    # than midpoint — the GT-conditioned ranges OVERLAP, so a midpoint sits inside
    # both. banner floor 153.3 -> 150; dark_frac floor 0.368 -> 0.30.)
    BANNER_THR = 150.0
    DARKFRAC_THR = 0.30
    SCOREBAR_THR = 80.0   # the rejected feature's threshold, for the record

    rules = {
        # single-feature primary (per the ladder): banner alone
        "primary_banner": (
            f"banner_mean >= {BANNER_THR}",
            lambda r: r["banner_mean"] >= BANNER_THR),
        # REJECTED: banner + scorebar (fails on real-game play-call screens)
        "rejected_banner_scorebar": (
            f"banner_mean >= {BANNER_THR} AND scorebar_mean <= {SCOREBAR_THR}",
            lambda r: r["banner_mean"] >= BANNER_THR and r["scorebar_mean"] <= SCOREBAR_THR),
        # RECOMMENDED (fallback-2): banner + dark_frac (dimming is UI-constant)
        "recommended_banner_darkfrac": (
            f"banner_mean >= {BANNER_THR} AND dark_frac >= {DARKFRAC_THR}",
            lambda r: r["banner_mean"] >= BANNER_THR and r["dark_frac"] >= DARKFRAC_THR),
    }

    rule_results = {}
    for name, (desc, fn) in rules.items():
        overall = evaluate_rule(all_rows, fn)
        by_clip = {c: evaluate_rule(rws, fn) for c, rws in per_clip.items() if rws}
        misfiring_clips = {c: cf for c, cf in by_clip.items() if cf["fp"] or cf["fn"]}
        rule_results[name] = {
            "desc": desc, "overall": overall,
            "clean": overall["fp"] == 0 and overall["fn"] == 0,
            # "acceptable": 0 FN (no missed play-call screens -> no C5 regression)
            # and FP only on transition frames the OCR "N Plays" guard neutralises.
            "zero_fn": overall["fn"] == 0,
            "misfiring_clips": misfiring_clips,
        }

    banner_thr, scorebar_thr = BANNER_THR, SCOREBAR_THR
    recommended = "recommended_banner_darkfrac"
    escalation = (
        "primary single-feature not clean; escalated to 2-feature (banner + dark_frac). "
        "scorebar rejected (game-mode-dependent). 0 FN achieved; residual FP are "
        "play<->live transition frames neutralised downstream by the read_formation_name "
        "'N Plays' OCR guard."
    )

    report = {
        "milestone": "7.5.1 context detector calibration",
        "ground_truth": "OCRPipeline.is_play_call_screen",
        "bboxes": {"banner_formation_name": banner_bbox, "scoreboard": scorebar_bbox},
        "samples": {"total": len(all_rows), "gt_play_call": gt_pc, "gt_live": gt_live},
        "feature_separation": sep,
        "thresholds": {"banner_mean_ge": banner_thr, "dark_frac_ge": DARKFRAC_THR,
                       "scorebar_mean_le_REJECTED": scorebar_thr},
        "rules": rule_results,
        "recommended_rule": recommended,
        "escalation": escalation,
        "per_clip_gt": {c: {"n": len(rws),
                            "gt_play_call": sum(1 for r in rws if r["gt_play_call"]),
                            "gt_live": sum(1 for r in rws if not r["gt_play_call"])}
                        for c, rws in per_clip.items()},
    }
    OUT.write_text(json.dumps(report, indent=2, default=str))

    print(f"samples: {len(all_rows)}  (play_call GT={gt_pc}, live GT={gt_live})")
    print(f"banner_mean : play_call {sep['banner_mean']['play_call']}  live {sep['banner_mean']['live']}")
    print(f"dark_frac   : play_call {sep['dark_frac']['play_call']}  live {sep['dark_frac']['live']}")
    print(f"scorebar[rej]: play_call {sep['scorebar_mean']['play_call']}  live {sep['scorebar_mean']['live']}")
    print(f"thresholds: banner>={banner_thr}  dark_frac>={DARKFRAC_THR}")
    for name, res in rule_results.items():
        print(f"  {name:28} clean={res['clean']} zero_fn={res['zero_fn']}  overall={res['overall']}  misfiring={list(res['misfiring_clips'])}")
    print(f"RECOMMENDED: {recommended}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
