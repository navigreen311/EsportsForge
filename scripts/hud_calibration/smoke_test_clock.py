"""Digit-reader smoke test — read the HUD off a PS5 frame against the shipped hud_regions.

A2/A1 pre-flight. Constructs the REAL OCRPipeline (same code path the live adapter
uses), runs read_frame() over one or more PS5 frames, and prints every field. Use it
two ways:

  * OFFLINE (deterministic, no PS5): point it at the saved calibration frames to confirm
    the digit reader + merged hud_regions.json read a clock on clean main.
        python scripts/hud_calibration/smoke_test_clock.py scripts/hud_calibration/frames

  * LIVE (A1 pre-flight): grab one PS5 frame to a PNG, then
        python scripts/hud_calibration/smoke_test_clock.py path/to/live_frame.png --expect :X7
    Exits 0 iff a clock was read (and, if --expect given, matches its seconds).

Run from services/visionaudioforge/ with that venv so `app` imports resolve, e.g.:
    cd services/visionaudioforge
    .venv/Scripts/python.exe ../../scripts/hud_calibration/smoke_test_clock.py <path> [--expect :X7]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

from app.adapters.madden26.ocr_pipeline import OCRPipeline


def _frames(target: Path) -> list[Path]:
    if target.is_dir():
        return sorted(target.glob("*.png"))
    return [target]


def _seconds(clock: str | None) -> str | None:
    """':37' style — the last two chars of 'M:SS', for --expect matching."""
    if not clock or ":" not in clock:
        return None
    return ":" + clock.rsplit(":", 1)[-1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="a PNG frame or a directory of frames")
    ap.add_argument(
        "--expect",
        default=None,
        help="require the clock seconds to match, e.g. ':X7' (X = any tens digit)",
    )
    args = ap.parse_args()

    target = Path(args.target)
    frames = _frames(target)
    if not frames:
        print(f"no frames at {target}", file=sys.stderr)
        return 2

    print("constructing OCRPipeline (warms EasyOCR ~2s)...", file=sys.stderr)
    ocr = OCRPipeline()

    any_clock = False
    expect_ok = args.expect is None
    for fp in frames:
        frame = cv2.imread(str(fp))
        if frame is None:
            print(f"  {fp.name:24s}  <unreadable>")
            continue
        s = ocr.read_frame(frame)
        clk = s.clock
        any_clock = any_clock or clk is not None
        sec = _seconds(clk)
        flag = ""
        if args.expect and sec is not None:
            # ':X7' — compare only the non-'X' positions.
            pat = args.expect.lstrip(":")
            got = (sec or "").lstrip(":")
            match = len(pat) == len(got) and all(
                p in ("X", "x") or p == g for p, g in zip(pat, got)
            )
            expect_ok = expect_ok or match
            flag = "  <== matches --expect" if match else ""
        print(
            f"  {fp.name:24s}  Q{s.quarter} {str(clk):>6}  pc={str(s.play_clock):>4}  "
            f"{s.down}&{s.distance}  {s.team_home_abbr}{s.score_home}-"
            f"{s.score_away}{s.team_away_abbr}{flag}"
        )

    print(
        f"\nread a clock on >=1 frame: {any_clock}"
        + (f"   --expect {args.expect} satisfied: {expect_ok}" if args.expect else ""),
        file=sys.stderr,
    )
    return 0 if (any_clock and expect_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
