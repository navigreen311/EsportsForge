"""Select pre-snap candidate frames from the Madden 26 capture batch.

M5c sub-task 2, step 1 (candidate selection — runs before the labeling tool).
Scans each clip and emits the frame indices that look like a stable pre-snap
moment: low frame-to-frame motion (players set, not mid-play) and, for the
CPU-vs-CPU matchup clips, a present HUD band (live gameplay, not a replay /
cutscene / menu).

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
HUD_CSTD_MIN = 45.0
GREEN_MIN = 0.45  # min field-green fraction — rejects menu / loading frames

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


def pick_candidates(samples: list[dict], kind: str, motion_pct: float,
                    per_window: int, stride: int) -> tuple[list[dict], dict]:
    motions = [s["motion"] for s in samples if s["motion"] is not None]
    if not motions:
        return [], {"reason": "no motion data"}
    thr = float(np.percentile(motions, motion_pct))
    hi_q_thr = float(np.percentile(motions, 20))  # very-static -> high quality

    # Flag each sample as a pre-snap candidate.
    flagged = []
    for s in samples:
        m = s["motion"]
        if m is None:
            continue
        is_static = m <= thr
        hud_ok = (kind != "matchup") or (s["central_std"] is not None and s["central_std"] >= HUD_CSTD_MIN)
        field_ok = s.get("green", 1.0) >= GREEN_MIN
        s["_cand"] = is_static and hud_ok and field_ok
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

    stats = {"samples": len(samples), "motion_threshold": round(thr, 2),
             "candidates": len(chosen)}
    return chosen, stats


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=FIXTURES_DIR / "formation_candidates.json")
    p.add_argument("--clips", nargs="*", default=None, help="override clip list")
    p.add_argument("--stride", type=int, default=15, help="frame sampling stride (15 = ~0.5s @30fps)")
    p.add_argument("--motion-pct", type=float, default=35.0, help="keep frames below this motion percentile")
    p.add_argument("--per-window", type=int, default=3, help="frames kept per pre-snap window")
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
        chosen, stats = pick_candidates(samples, kind, args.motion_pct, args.per_window, args.stride)
        for c in chosen:
            all_candidates.append({
                "clip": video.name, "kind": kind,
                "frame_idx": c["frame_idx"], "ts_sec": c["ts_sec"],
                "motion": round(c["motion"], 2),
                "auto_label": formation,                       # None for matchup
                "label_quality": c["_quality"] if formation else None,
            })
        stats.update({"clip": video.name, "kind": kind, "auto_formation": formation})
        per_clip_stats.append(stats)
        print(f"{video.name:38} {kind:8} cand={stats['candidates']:4} "
              f"(of {stats['samples']} samples, motion<= {stats['motion_threshold']})"
              + (f" -> auto-label {formation}" if formation else ""))

    n_auto = sum(1 for c in all_candidates if c["auto_label"])
    n_human = len(all_candidates) - n_auto
    out = {
        "milestone": "M5c sub-task 2",
        "stride": args.stride, "motion_pct": args.motion_pct, "per_window": args.per_window,
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
