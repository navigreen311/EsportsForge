"""Sample frames densely in the gameplay portion of the Madden fixture.

The 12-frame uniform sample missed too much HUD coverage — the clip mixes
facecam intro, menu screens, and gameplay. Calibration needs ≥10
gameplay-with-HUD frames; this script picks them by index range.

Run:

    python scripts/hud_calibration/sample_dense_gameplay.py
"""

from __future__ import annotations

from pathlib import Path

import cv2

VIDEO = Path("agents/capture/fixtures/real/madden26.mp4")
OUT_DIR = Path("scripts/hud_calibration/frames")

# Gameplay window appears to start ~frame 4500. Sample 10 frames between
# 4500 and 7100. Avoid frames near 4538 (kickoff state — HUD shows
# "KICKOFF" not down/distance) and pick a mix.
INDICES = [4400, 4700, 5000, 5500, 5900, 6100, 6300, 6600, 6800, 7100]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(VIDEO))
    if not cap.isOpened():
        raise RuntimeError(f"open failed: {VIDEO}")

    for idx in INDICES:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            print(f"WARN: read failed at {idx}")
            continue
        out = OUT_DIR / f"frame_{idx:06d}.png"
        cv2.imwrite(str(out), frame)
        print(f"wrote {out.name}")

    cap.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
