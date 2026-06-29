"""Sample HUD calibration frames from the real Madden 26 capture batch.

M5c sub-task 1b, methodology step 1 (calibration frame sampling). Picks
clean-HUD gameplay frames across the CPU-vs-CPU matchup clips to drive the
`hud_regions.json` v2.1.0 re-calibration of the new center-clustered scorebug.

A frame is "clean HUD" when the game clock reads a valid `M:SS` at the new
centered-scorebug clock position — a cheap, reliable gate that the scorebug
is on-screen and rendered (it survives kickoffs/punts, where the game clock
still ticks while the down/distance panel shows KICKOFF/PUNT). Within each
clip the kept frames are spread across the timeline so scores, downs,
quarters and field positions vary; each frame's raw down/distance read is
recorded so kickoff/punt panels can be spotted during review.

This sampler is intentionally clip-set agnostic — re-runnable for any future
title-update re-calibration (the recurring-maintenance pattern documented in
the HUD calibration methodology).

Run (from repo root, with services/visionaudioforge/.venv active):

    python scripts/hud_calibration/sample_calibration_frames.py \
        --out scripts/hud_calibration/frames_v21 --per-clip 3
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

from app.adapters.madden26.ocr_pipeline import _read_text  # noqa: E402

FIXTURES_DIR = REPO_ROOT / "agents" / "capture" / "fixtures" / "real"

# Default calibration source: a colour-diverse spread of the matchup clips
# (navy/red, red/green, green/blue, blue/aqua, burgundy/black-gold, navy/gold,
# powder-blue/green, navy-orange/red-blue) — the white-on-team-colour stress
# cases for the abbrev/score preprocessing.
DEFAULT_CLIPS = [
    "madden26_bal_vs_cin_q1.mp4",
    "madden26_kc_vs_phi._q1.mp4",
    "madden26_gb_vs_det_q1.mp4",
    "madden26_buf_vs_mia_q1.mp4",
    "madden26_wash_vs_pits_q4.mp4",
    "madden26_dal_vs_sf_q1.mp4",
    "madden26_lac_vs_sea_q4.mp4",
    "madden26_chi_vs_hou_q4.mp4",
]

# First-pass measured positions on the new centered scorebug (this session's
# feasibility probe). The clock bbox is the clean-HUD detector; down/distance
# is read raw to tag kickoff/punt panels. Final bboxes are set in 1b.2.
CLOCK_BBOX = [932, 1030, 92, 34]
DND_BBOX = [752, 1035, 116, 24]   # spans "3RD & 6" / "KICKOFF" / "PUNT"

_CLOCK_RE = re.compile(r"^\d{1,2}:\d{2}$")
_SCAN_POSITIONS = 44   # timeline probes per clip


def _bottom_strip(frame: np.ndarray) -> np.ndarray:
    return frame[960:1080, 0:1920]


def sample_clip(video: Path, per_clip: int) -> list[dict]:
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        print(f"WARN: could not open {video.name}")
        return []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Scan the clip timeline; collect frames with a valid clock read.
    candidates: list[dict] = []
    for i in range(_SCAN_POSITIONS):
        pct = 0.04 + (i / (_SCAN_POSITIONS - 1)) * 0.92
        idx = int(pct * total)
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        cx, cy, cw, ch = CLOCK_BBOX
        clock_txt, _ = _read_text(frame[cy:cy + ch, cx:cx + cw], "0123456789:")
        if not _CLOCK_RE.match(clock_txt.strip()):
            continue
        dx, dy, dw, dh = DND_BBOX
        dnd_txt, _ = _read_text(frame[dy:dy + dh, dx:dx + dw])
        candidates.append({
            "frame_idx": idx,
            "ts_sec": round(idx / fps, 2) if fps > 0 else None,
            "clock_read": clock_txt.strip(),
            "down_distance_read": dnd_txt.strip(),
            "_frame": frame.copy(),
        })

    if not candidates:
        cap.release()
        print(f"WARN: {video.name}: no clean-HUD frames found")
        return []

    # Spread the kept frames across the timeline for state variety, but bias
    # toward including any likely kickoff/punt panel (alpha letters in d/d).
    def looks_special(c: dict) -> bool:
        return bool(re.search(r"[A-Za-z]{3,}", c["down_distance_read"]))

    chosen: list[dict] = []
    specials = [c for c in candidates if looks_special(c)]
    if specials:
        chosen.append(specials[0])
    remaining = [c for c in candidates if c not in chosen]
    need = max(0, per_clip - len(chosen))
    if remaining and need:
        step = max(1, len(remaining) // need)
        for j in range(0, len(remaining), step):
            chosen.append(remaining[j])
            if len(chosen) >= per_clip:
                break
    chosen = sorted(chosen, key=lambda c: c["frame_idx"])[:per_clip]
    cap.release()
    return chosen


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=REPO_ROOT / "scripts" / "hud_calibration" / "frames_v21")
    p.add_argument("--per-clip", type=int, default=3)
    p.add_argument("--clips", nargs="*", default=DEFAULT_CLIPS)
    args = p.parse_args()

    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Sampling calibration frames -> {out_dir} ({args.per_clip}/clip, "
          f"{len(args.clips)} clips). EasyOCR cold-start on first read...\n")

    index: list[dict] = []
    for clip_name in args.clips:
        video = FIXTURES_DIR / clip_name
        if not video.exists():
            print(f"WARN: missing {clip_name}")
            continue
        stem = video.stem
        picks = sample_clip(video, args.per_clip)
        strips = []
        for c in picks:
            frame = c.pop("_frame")
            fname = f"{stem}_f{c['frame_idx']:06d}.png"
            cv2.imwrite(str(out_dir / fname), frame)
            c["clip"] = clip_name
            c["file"] = fname
            index.append(c)
            strip = _bottom_strip(frame).copy()
            cv2.putText(strip, f"{fname}  clock={c['clock_read']}  dnd={c['down_distance_read']!r}",
                        (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            strips.append(strip)
        if strips:
            cv2.imwrite(str(out_dir / f"_review_{stem}.png"), np.vstack(strips))
        print(f"{clip_name:34} -> {len(picks)} frames "
              f"(clocks: {[c['clock_read'] for c in picks]})")

    (out_dir / "calibration_index.json").write_text(json.dumps(
        {"source": "M5c sub-task 1b", "clips": args.clips,
         "per_clip": args.per_clip, "frame_count": len(index), "frames": index},
        indent=2))
    print(f"\n{len(index)} calibration frames written. index -> "
          f"{out_dir / 'calibration_index.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
