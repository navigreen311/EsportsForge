"""Render candidate HUD bboxes onto a frame as labeled coloured rectangles.

The output PNG is the calibration "did I draw the box in the right
place?" feedback loop. Update CANDIDATES, re-run, eyeball, repeat.

Final coords end up in services/visionaudioforge/app/adapters/madden26/
hud_regions.json.

Run:

    python scripts/hud_calibration/annotate_bboxes.py \
        --frame scripts/hud_calibration/frames/frame_006100.png \
        --out  scripts/hud_calibration/annotated/frame_006100_anno.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

# Bbox = [x, y, w, h] in 1080p coords. Madden 26 HUD lives in the bottom
# band; coords measured against frame 6100 of agents/capture/fixtures/
# real/madden26.mp4 and validated against frames 4400, 4538, 6421, 7049.
CANDIDATES: dict[str, dict] = {
    "scoreboard_band":  {"bbox": [0, 1006, 1190, 74],   "color": (0, 220, 0)},
    "team_home_logo":   {"bbox": [80, 1014, 280, 60],   "color": (0, 200, 200)},
    "team_home_abbr":   {"bbox": [460, 1024, 145, 40],  "color": (255, 100, 0)},   # "LAC"
    "score_home":       {"bbox": [640, 1018, 90, 50],   "color": (255, 50, 50)},   # "0" home
    "score_away":       {"bbox": [770, 1018, 80, 50],   "color": (255, 50, 50)},   # "0" away
    "team_away_abbr":   {"bbox": [870, 1024, 130, 40],  "color": (255, 100, 0)},   # "ARI"
    "team_away_logo":   {"bbox": [990, 1014, 200, 60],  "color": (0, 200, 200)},
    "quarter":          {"bbox": [1265, 1024, 80, 40],  "color": (255, 0, 220)},   # "1ST" (game)
    "clock":            {"bbox": [1350, 1024, 110, 40], "color": (255, 0, 220)},   # "3:18"
    "play_clock":       {"bbox": [1465, 1024, 80, 40],  "color": (220, 0, 255)},   # ":11"
    "down":             {"bbox": [1545, 1024, 95, 40],  "color": (220, 220, 0)},   # "1ST" (down)
    "distance":         {"bbox": [1640, 1024, 100, 40], "color": (220, 220, 0)},   # "& 10"
    "field_position":   {"bbox": [1720, 1024, 195, 40], "color": (200, 200, 100)},  # "▲41"
}


def annotate(frame_path: Path, out_path: Path) -> None:
    img = cv2.imread(str(frame_path))
    if img is None:
        raise RuntimeError(f"could not read {frame_path}")
    h, w = img.shape[:2]
    print(f"frame: {frame_path.name}  shape={(w, h)}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    overlay = img.copy()
    for name, spec in CANDIDATES.items():
        x, y, bw, bh = spec["bbox"]
        color = spec["color"]
        cv2.rectangle(overlay, (x, y), (x + bw, y + bh), color, 2)
        # Label tag above the box.
        ty = max(y - 6, 12)
        cv2.putText(
            overlay,
            name,
            (x, ty),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            color,
            1,
            cv2.LINE_AA,
        )
        # Per-region crop dump for OCR sanity check.
        crop = img[y : y + bh, x : x + bw]
        crop_path = out_path.parent / f"{out_path.stem}_{name}.png"
        if crop.size > 0:
            cv2.imwrite(str(crop_path), crop)

    cv2.imwrite(str(out_path), overlay)
    print(f"annotated -> {out_path}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--frame", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    annotate(args.frame, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
