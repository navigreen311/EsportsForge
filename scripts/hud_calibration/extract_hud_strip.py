"""Extract the bottom HUD band from sampled frames as standalone PNG strips.

The full frame is 1920x1080 — too wide to eyeball on a typical display.
Extracting just the bottom 80 px and saving it gives a 1920x80 strip
at full pixel fidelity, which is what we need for sub-region calibration.
"""

from __future__ import annotations

from pathlib import Path

import cv2

FRAMES_DIR = Path("scripts/hud_calibration/frames")
OUT_DIR = Path("scripts/hud_calibration/strips")

# HUD-bearing frames identified by visual inspection.
HUD_FRAMES = [4400, 4538, 6100, 6421, 7049]

# Bottom band: y from 1006 to 1080 (last 74 px) — confirmed by
# visual inspection of frame_006100.
BAND_TOP = 1006
BAND_HEIGHT = 74


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for idx in HUD_FRAMES:
        src = FRAMES_DIR / f"frame_{idx:06d}.png"
        if not src.exists():
            print(f"missing: {src}")
            continue
        img = cv2.imread(str(src))
        if img is None:
            print(f"could not read: {src}")
            continue
        strip = img[BAND_TOP : BAND_TOP + BAND_HEIGHT, :]
        out = OUT_DIR / f"strip_{idx:06d}.png"
        cv2.imwrite(str(out), strip)
        print(f"wrote {out.name}  shape={strip.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
