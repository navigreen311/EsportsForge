"""Select pre-snap candidate frames from the Madden 26 capture batch.

M5c sub-task 2, step 1 (candidate selection — runs before the labeling tool).
Scans each clip and emits the frame indices that look like a LOCKED pre-snap
moment: two consecutive near-zero motion samples (the offense is set, not mid-
play or post-snap drifting), field-green dominance (rejects coach close-ups /
replay graphics / sideline cuts), and — for matchup clips — a live gameplay
scorebug. Gate-passing frames are then OCR-checked and kickoff/punt/extra-point
plays dropped (special teams is outside the canonical-8 offensive taxonomy).

Selector v2 (M5c sub-task 2 revision): the v1 single-frame low-motion rule
caught mid-play lulls the labeling agent could not classify from Madden's
elevated ball-following camera; v2's locked-pre-snap requirement + tighter
gates produce a cleaner, smaller human-labeling pool. See
docs/integrations/visionaudioforge/training-data-labeling-protocol.md.

Two clip kinds, two roles:

  * PRACTICE clips render one known formation each (encoded in the filename),
    so their pre-snap candidates are AUTO-LABELLED here — no human pass needed.
    This is the balanced per-class backbone of the training set.
  * MATCHUP clips contain mixed formations and no model exists yet to label
    them, so their candidates are emitted UNLABELLED for the human pass via
    label_formations.py.

Efficiency: frames are decoded with grab()/retrieve() so only every Nth frame
pays the decode cost (seeking multi-GB files frame-by-frame is far slower).

Motion threshold is per-clip adaptive (a percentile of the clip's own motion
distribution) so it is robust to clip-to-clip exposure / camera differences.
Within each run of consecutive low-motion frames (one pre-snap window) only a
spread few frames are kept, so the set favours DISTINCT plays over near-
duplicate frames of the same snap.

Run (from repo root, with services/visionaudioforge/.venv active):

    python scripts/hud_calibration/sample_pre_snap_candidates.py \
        --out agents/capture/fixtures/real/formation_candidates.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = REPO_ROOT / "services" / "visionaudioforge"
sys.path.insert(0, str(SERVICE_ROOT))

from app.adapters.madden26.formation_detector import TOP_8_FORMATIONS  # noqa: E402

FIXTURES_DIR = REPO_ROOT / "agents" / "capture" / "fixtures" / "real"

# v2.1.0 centered-scorebug band — HUD-presence proxy for matchup clips.
SCOREBOARD_BAND = [700, 988, 600, 78]
# Gates tightened in the M5c sub-task-2 selector revision (v2): the v1 single-
# frame low-motion rule caught mid-play lulls and post-snap static moments, so
# the agent could not classify the resulting pool (Madden's elevated ball-
# following camera doesn't expose a clean formation in a developing frame). v2
# requires the offense to be LOCKED (two consecutive near-zero motion samples)
# and raises the field/HUD gates to reject coach close-ups, replay graphics and
# sideline cuts. See docs/.../training-data-labeling-protocol.md.
HUD_CSTD_MIN = 55.0   # was 45 — confirm a live gameplay scorebug, not menu/replay
GREEN_MIN = 0.55      # was 0.45 — reject coach close-ups / replay graphics / sideline cuts
# Down/distance region (v2.1.0 layout) read to drop kickoff/punt/XP frames —
# special-teams plays are not in the canonical-8 offensive taxonomy.
DND_REGION = [742, 1033, 128, 28]
_SPECIAL_TEAMS_RE = re.compile(r"KICK|PUNT|PVNT|P0NT|XTRA|XHA|XPA|EXTRA", re.IGNORECASE)

# Practice-clip filename token -> canonical formation. shotgun_tight is the
# bonus clip (not in TOP_8) and is excluded from the training candidate set.
def _practice_formation(stem: str) -> str | None:
    m = re.match(r"madden26_practice_(.+)", stem)
    if not m:
        return None
    token = m.group(1).replace("-", "_")  # i-form_pro -> i_form_pro
    return token if token in TOP_8_FORMATIONS else None  # excludes shotgun_tight


def _clip_kind(stem: str) -> str:
    return "practice" if stem.startswith("madden26_practice") else "matchup"


def _central_std(frame: np.ndarray, bbox) -> float:
    x, y, w, h = bbox
    h_full, w_full = frame.shape[:2]
    if (h_full, w_full) != (1080, 1920):
        sx, sy = w_full / 1920.0, h_full / 1080.0
        x, y, w, h = int(x * sx), int(y * sy), int(w * sx), int(h * sy)
    crop = frame[y:y + h, x:x + w]
    if crop.size == 0:
        return 0.0
    return float(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY).std())


def _green_fraction(small_bgr: np.ndarray) -> float:
    """Fraction of green field pixels in the central-lower play area.

    Menus / loading / replay-graphic frames are not field-dominant; a real
    pre-snap gameplay frame is mostly green turf. Cheap discriminator that
    rejects the menu false-positives the motion gate alone lets through.
    """
    region = small_bgr[120:270, 80:400]  # central-lower of the 480x270 frame
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    green = (h >= 35) & (h <= 90) & (s >= 40) & (v >= 40)
    return float(green.mean())


def scan_clip(video: Path, stride: int) -> list[dict]:
    """Sample every `stride` frames; return per-sample motion + HUD + field stats."""
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        print(f"WARN could not open {video.name}")
        return []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    kind = _clip_kind(video.stem)
    lo = int(0.05 * total) if total else 0   # skip setup menus at the head
    hi = int(0.97 * total) if total else 10**12  # and the tail

    samples: list[dict] = []
    prev_small = None
    idx = -1
    while True:
        if not cap.grab():
            break
        idx += 1
        if idx % stride != 0:
            continue
        ok, frame = cap.retrieve()
        if not ok or frame is None:
            continue
        small_bgr = cv2.resize(frame, (480, 270))
        small = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2GRAY)
        motion = None if prev_small is None else float(np.mean(cv2.absdiff(small, prev_small)))
        prev_small = small
        if idx < lo or idx > hi:
            continue  # edge frames: still update motion baseline, but not candidates
        cstd = _central_std(frame, SCOREBOARD_BAND) if kind == "matchup" else None
        samples.append({"frame_idx": idx, "ts_sec": round(idx / fps, 2),
                        "motion": motion, "central_std": cstd,
                        "green": round(_green_fraction(small_bgr), 3)})
    cap.release()
    return samples


def pick_candidates(samples: list[dict], kind: str, tight_pct: float,
                    per_window: int, stride: int) -> tuple[list[dict], dict]:
    motions = [s["motion"] for s in samples if s["motion"] is not None]
    if not motions:
        return [], {"reason": "no motion data"}
    tight_thr = float(np.percentile(motions, tight_pct))  # "near-zero" motion
    hi_q_thr = float(np.percentile(motions, 10))          # stillest -> high quality

    # A frame is a SET pre-snap candidate only if the offense is locked: the
    # motion interval INTO it and OUT of it are both near-zero (two consecutive
    # near-zero samples). This rejects the single-frame mid-play lulls and
    # post-snap static moments the v1 rule let through.
    n = len(samples)
    flagged = []
    for i, s in enumerate(samples):
        m = s["motion"]
        if m is None:
            continue
        static_in = m <= tight_thr
        nxt = samples[i + 1]["motion"] if i + 1 < n else None
        static_out = nxt is not None and nxt <= tight_thr
        is_set = static_in and static_out
        hud_ok = (kind != "matchup") or (s["central_std"] is not None and s["central_std"] >= HUD_CSTD_MIN)
        field_ok = s.get("green", 1.0) >= GREEN_MIN
        s["_cand"] = is_set and hud_ok and field_ok
        s["_quality"] = "high" if m <= hi_q_thr else "medium"
        flagged.append(s)

    # Group consecutive candidates (one pre-snap window) and keep a spread few.
    chosen: list[dict] = []
    window: list[dict] = []

    def flush(win):
        if not win:
            return
        if len(win) <= per_window:
            chosen.extend(win)
        else:
            step = len(win) / per_window
            for k in range(per_window):
                chosen.append(win[int(k * step)])

    prev_idx = None
    for s in flagged:
        if not s["_cand"]:
            flush(window); window = []
            prev_idx = None
            continue
        if prev_idx is not None and s["frame_idx"] - prev_idx > stride * 2:
            flush(window); window = []
        window.append(s)
        prev_idx = s["frame_idx"]
    flush(window)

    stats = {"samples": len(samples), "motion_threshold": round(tight_thr, 2),
             "candidates_pre_filter": len(chosen)}
    return chosen, stats


def kickoff_punt_filter(video: Path, chosen: list[dict]) -> tuple[list[dict], int]:
    """Drop kickoff / punt / extra-point frames by reading the down/distance panel.

    Those panels render "KICKOFF" / "PUNT" / "EXTRA POINT" (not "& <n>") and are
    special-teams plays outside the canonical-8 offensive taxonomy. OCR runs only
    on the (already small) gate-passing candidate set, so the cost is bounded.
    "GOAL" (1ST & GOAL) is a normal offensive down and is intentionally kept.
    """
    if not chosen:
        return chosen, 0
    from app.adapters.madden26.ocr_pipeline import _read_text  # lazy: EasyOCR
    cap = cv2.VideoCapture(str(video))
    x, y, w, h = DND_REGION
    kept, dropped = [], 0
    for c in chosen:
        cap.set(cv2.CAP_PROP_POS_FRAMES, c["frame_idx"])
        ok, frame = cap.read()
        if not ok or frame is None:
            kept.append(c)
            continue
        text, _ = _read_text(frame[y:y + h, x:x + w])
        if _SPECIAL_TEAMS_RE.search(text.upper().replace(" ", "")):
            dropped += 1
        else:
            kept.append(c)
    cap.release()
    return kept, dropped


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=FIXTURES_DIR / "formation_candidates.json")
    p.add_argument("--clips", nargs="*", default=None, help="override clip list")
    p.add_argument("--stride", type=int, default=15, help="frame sampling stride (15 = ~0.5s @30fps)")
    p.add_argument("--tight-pct", type=float, default=25.0,
                   help="'near-zero' motion percentile; a set frame needs two consecutive below it")
    p.add_argument("--per-window", type=int, default=3, help="frames kept per locked pre-snap window")
    p.add_argument("--no-kickoff-filter", action="store_true",
                   help="skip the OCR kickoff/punt drop (faster; for debugging)")
    args = p.parse_args()

    if args.clips:
        clips = [FIXTURES_DIR / c for c in args.clips]
    else:
        clips = sorted(c for c in FIXTURES_DIR.glob("madden26_*.mp4") if c.name != "madden26.mp4")

    all_candidates: list[dict] = []
    per_clip_stats: list[dict] = []
    for video in clips:
        kind = _clip_kind(video.stem)
        formation = _practice_formation(video.stem) if kind == "practice" else None
        if kind == "practice" and formation is None:
            print(f"SKIP {video.name} (bonus/non-TOP8 practice clip)")
            per_clip_stats.append({"clip": video.name, "kind": kind, "skipped": "non-TOP8"})
            continue
        samples = scan_clip(video, args.stride)
        chosen, stats = pick_candidates(samples, kind, args.tight_pct, args.per_window, args.stride)
        dropped = 0
        if not args.no_kickoff_filter:
            chosen, dropped = kickoff_punt_filter(video, chosen)
        for c in chosen:
            all_candidates.append({
                "clip": video.name, "kind": kind,
                "frame_idx": c["frame_idx"], "ts_sec": c["ts_sec"],
                "motion": round(c["motion"], 2),
                "auto_label": formation,                       # None for matchup
                "label_quality": c["_quality"] if formation else None,
            })
        stats.update({"clip": video.name, "kind": kind, "auto_formation": formation,
                      "kickoff_punt_dropped": dropped, "candidates": len(chosen)})
        per_clip_stats.append(stats)
        print(f"{video.name:38} {kind:8} cand={len(chosen):4} "
              f"(of {stats['samples']} samples, motion<= {stats['motion_threshold']}, "
              f"kickoff/punt dropped {dropped})"
              + (f" -> auto-label {formation}" if formation else ""))

    n_auto = sum(1 for c in all_candidates if c["auto_label"])
    n_human = len(all_candidates) - n_auto
    out = {
        "milestone": "M5c sub-task 2",
        "selector_version": "v2 (two-consecutive-near-zero + tightened gates + kickoff/punt filter)",
        "stride": args.stride, "tight_pct": args.tight_pct, "per_window": args.per_window,
        "total_candidates": len(all_candidates),
        "auto_labelled_practice": n_auto,
        "unlabelled_matchup_for_human": n_human,
        "per_clip": per_clip_stats,
        "candidates": all_candidates,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(f"\n{len(all_candidates)} candidates "
          f"({n_auto} auto-labelled practice, {n_human} matchup for human pass)")
    print(f"-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
