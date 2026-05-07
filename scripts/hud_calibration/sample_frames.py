"""Sample N frames from a video at indices distributed across pre-snap,
post-snap, and menu states.

Phase 0 M4.5 deliverable. Output: a directory of PNG frames + an index
file listing each frame's source position. Intended for manual region
labeling in a downstream tool (the calibration write-up describes the
flow end-to-end).

Run:

    python scripts/hud_calibration/sample_frames.py \
        --video agents/capture/fixtures/real/madden26.mp4 \
        --out scripts/hud_calibration/frames \
        --count 12

Defaults pick frames at uniform percentile positions through the clip.
For the Madden 26 fixture (7193 frames, 2:00 at 59.94 fps), 12 frames
land roughly every 10 seconds, which catches both pre-snap and
mid-play states without a state classifier.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2


def sample(video: Path, out_dir: Path, count: int) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open {video}")

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if total <= 0:
        raise RuntimeError(f"Video reports zero frames: {video}")

    # Uniform percentile sampling — picks frames across the clip.
    # Skip the first 2% and last 2% to avoid intro/outro slates.
    indices = []
    for i in range(count):
        pct = 0.02 + (i / (count - 1)) * 0.96
        indices.append(int(pct * total))

    samples: list[dict] = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            print(f"WARN: read failed at frame {idx}, skipping")
            continue
        out_path = out_dir / f"frame_{idx:06d}.png"
        cv2.imwrite(str(out_path), frame)
        samples.append(
            {
                "frame_idx": idx,
                "ts_sec": round(idx / fps, 3) if fps > 0 else None,
                "path": str(out_path.relative_to(out_dir.parent.parent.parent)).replace("\\", "/"),
            }
        )
        print(f"wrote {out_path.name}  (idx={idx}, t={idx/fps:.2f}s)")

    cap.release()

    index = {
        "source_video": str(video.relative_to(video.parents[3])).replace("\\", "/"),
        "source_resolution": [width, height],
        "source_fps": fps,
        "source_frame_count": total,
        "sample_count": len(samples),
        "samples": samples,
    }
    index_path = out_dir / "frames_index.json"
    index_path.write_text(json.dumps(index, indent=2))
    print(f"\nindex -> {index_path}")
    return index


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--count", type=int, default=12)
    args = p.parse_args()
    sample(args.video, args.out, args.count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
