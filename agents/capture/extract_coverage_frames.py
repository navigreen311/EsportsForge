"""Extract POST-SNAP coverage frames from the coverage clip corpus into a
labeled image-classification dataset.

DATASET PREP ONLY — no model, no training, no classifier code. This turns the
24 All-22 coverage clips (fixtures/coverage/madden26_coverage_cover{1..4}_{01..06}.mp4)
into a folder-per-class image dataset for a future coverage classifier.

Windowing (PER-CLIP, snap-relative):
  A fixed time window does NOT work — the snap wanders ~2s across clips (the
  pre-snap phase varies with how long the player spent audibling / adjusting
  coverage), which is wider than the usable post-snap window. So the snap
  offset for each clip was located by eyeballing per-clip contact sheets and is
  stored in SNAP_OFFSETS below. Each clip is windowed from snap+WINDOW_START_S
  to snap+WINDOW_END_S — the window where the DBs have rotated into their
  coverage but the play has not yet broken down — and FRAMES_PER_CLIP frames are
  taken evenly across it. Short-clip safe: the window end is clamped to the clip
  length so we never seek past the end.

Label = the coverage token parsed from the filename (cover1/2/3/4). Frames are
named traceably: <coverage>_<NN>_fMM.jpg (e.g. cover3_04_f02.jpg).

Run (VAF venv, which has cv2):
    python agents/capture/extract_coverage_frames.py \
        --corpus /abs/agents/capture/fixtures/coverage \
        --out    /abs/agents/capture/coverage_dataset
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import cv2

# --- Post-snap window (relative to each clip's snap) ------------------------
WINDOW_START_S = 0.5   # seconds AFTER the snap
WINDOW_END_S = 2.0     # seconds AFTER the snap
FRAMES_PER_CLIP = 6    # evenly spaced across [snap+start, snap+end]

# Per-clip snap offset (seconds into clip, "first movement"), eyeballed from the
# per-clip contact sheets. Stored here so extraction is reproducible + re-runnable.
SNAP_OFFSETS: dict[str, float] = {
    "cover1_01": 3.5, "cover1_02": 3.5, "cover1_03": 2.5,
    "cover1_04": 2.5, "cover1_05": 2.5, "cover1_06": 3.0,
    "cover2_01": 2.0, "cover2_02": 2.5, "cover2_03": 2.0,
    "cover2_04": 2.0, "cover2_05": 3.0, "cover2_06": 2.0,
    "cover3_01": 2.0, "cover3_02": 3.5, "cover3_03": 1.5,
    "cover3_04": 4.0, "cover3_05": 3.5, "cover3_06": 4.0,
    "cover4_01": 4.0, "cover4_02": 3.0, "cover4_03": 3.5,
    "cover4_04": 3.5, "cover4_05": 3.0, "cover4_06": 3.0,
}

# Batch 2 (_07+): recorded AT the snap (record-at-snap habit) -> snap ~0.0s, so
# the window runs from the clip start. Confirmed on 8 sampled clips (STRAFE from
# frame one, consistent across classes). No per-clip offsets needed for these.
BATCH2_SNAP = 0.0
BATCH1_MAX = 6  # clip number <= 6 => batch 1 (per-clip offset); >= 7 => batch 2

# madden26_coverage_cover3_04.mp4 -> ("cover3", "04")
CLIP_RE = re.compile(r"(cover[1-4])_(\d{2})", re.IGNORECASE)


def _frame_indices(start_f: int, end_f: int, n: int) -> list[int]:
    if n <= 1 or end_f <= start_f:
        return [start_f]
    step = (end_f - start_f) / (n - 1)
    return [int(round(start_f + step * i)) for i in range(n)]


def extract_clip(path: Path, out_root: Path) -> tuple[str, str, int]:
    """Returns (clip_id, coverage_label_or_reason, frames_written)."""
    m = CLIP_RE.search(path.name)
    if not m:
        return (path.name, "NO_LABEL", 0, None, False)
    coverage = m.group(1).lower()          # "cover3"
    clip_id = f"{coverage}_{m.group(2)}"   # "cover3_04"

    # Batch routing: <=06 uses its saved per-clip snap; >=07 snaps at 0.0.
    clip_num = int(m.group(2))
    if clip_num <= BATCH1_MAX:
        snap = SNAP_OFFSETS.get(clip_id)
        if snap is None:  # fail loudly rather than mis-window a batch-1 clip
            return (clip_id, "NO_SNAP_OFFSET", 0, None, False)
    else:
        snap = BATCH2_SNAP

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return (clip_id, "OPEN_FAIL", 0, snap, False)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Snap-relative window in frames, end clamped to the clip length. `overran`
    # flags a clip where snap+WINDOW_END_S would run past the end (window then
    # gets compressed into what's available) — reported so no silent short-window.
    start_f = int((snap + WINDOW_START_S) * fps)
    want_end_f = int((snap + WINDOW_END_S) * fps)
    overran = want_end_f > total - 1
    end_f = min(want_end_f, max(total - 1, 0))
    start_f = min(start_f, end_f)
    idxs = _frame_indices(start_f, end_f, FRAMES_PER_CLIP)

    out_dir = out_root / coverage
    out_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for i, fidx in enumerate(idxs, start=1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fidx)
        ok, frame = cap.read()
        if not ok:
            continue
        cv2.imwrite(str(out_dir / f"{clip_id}_f{i:02d}.jpg"), frame)
        written += 1
    cap.release()
    return (clip_id, coverage, written, snap, overran)


def main() -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="Extract post-snap coverage frames (dataset prep only).")
    ap.add_argument("--corpus", type=Path, default=here / "fixtures" / "coverage")
    ap.add_argument("--out", type=Path, default=here / "coverage_dataset")
    args = ap.parse_args()

    corpus: Path = args.corpus
    out_root: Path = args.out
    clips = sorted(corpus.glob("madden26_coverage_*.mp4"))
    if not clips:
        print(f"no clips found under {corpus}", file=sys.stderr)
        return 1

    print(f"corpus: {corpus}")
    print(f"out:    {out_root}")
    print(f"window: snap+{WINDOW_START_S}s .. snap+{WINDOW_END_S}s, {FRAMES_PER_CLIP} frames/clip\n")

    per_class: dict[str, int] = {}
    problems: list[str] = []
    overruns: list[str] = []
    total_written = 0
    for clip in clips:
        clip_id, label, n, snap, overran = extract_clip(clip, out_root)
        if label.startswith(("NO_", "OPEN_")):
            problems.append(f"{clip_id}: {label}")
        else:
            per_class[label] = per_class.get(label, 0) + n
            total_written += n
        if overran:
            overruns.append(clip_id)
        flag = "  <- OVERRUN (clamped)" if overran else ""
        print(f"  {clip_id:14s} snap={snap!s:>4}  -> {label:9s} {n} frames{flag}")

    print(f"\nTOTAL frames: {total_written}")
    print("per-class:")
    for label in sorted(per_class):
        print(f"  {label:9s} {per_class[label]}")
    if overruns:
        print(f"\nWINDOW OVERRUN (snap+{WINDOW_END_S}s past clip end -> window clamped): {overruns}")
    if problems:
        print("\nPROBLEMS (not extracted):")
        for p in problems:
            print(f"  {p}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
