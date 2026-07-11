"""Validate OCR pipeline against the calibrated hud_regions.json.

Runs the production OCR pipeline against each calibration frame and
compares each subregion read to a hand-labeled ground-truth value.

Acceptance criterion (M4.5): >= 80% success rate per HUD element across
the calibrated frames.

Output: a JSON report at agents/capture/fixtures/real/m45_ocr_validation.json
suitable for committing as evidence.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = REPO_ROOT / "services" / "visionaudioforge"
sys.path.insert(0, str(SERVICE_ROOT))

from app.adapters.madden26.ocr_pipeline import OCRPipeline  # noqa: E402

# Hand-labeled ground truth per frame. Values are strings; comparisons
# are case-insensitive after stripping non-comparison chars per element.
#
# Notes:
#   * Frames 4400 and 4538 are kickoff state. The "down" and "distance"
#     panels render "KICKOFF" / "+35" instead of digits. We mark them
#     as "kickoff_state" so the report can split scoring.
#   * play_clock is "--" (no play clock) on kickoff/post-snap frames.
GROUND_TRUTH: dict[int, dict] = {
    4400: {
        "team_home_abbr": "LAC", "team_away_abbr": "ARI",
        "score_home": 0, "score_away": 0,
        "quarter": 1, "clock": "4:00",
        "play_clock": None, "down": None, "distance": None,
        "field_position": "+35",
        "state": "kickoff",
    },
    4538: {
        "team_home_abbr": "LAC", "team_away_abbr": "ARI",
        "score_home": 0, "score_away": 0,
        "quarter": 1, "clock": "4:00",
        "play_clock": None, "down": None, "distance": None,
        "field_position": "+35",
        "state": "kickoff",
    },
    4700: {
        "team_home_abbr": "LAC", "team_away_abbr": "ARI",
        "score_home": 0, "score_away": 0,
        "quarter": 1, "clock": "3:57",
        "play_clock": None, "down": None, "distance": None,
        "field_position": "+35",
        "state": "kickoff",
    },
    5300: {
        "team_home_abbr": "LAC", "team_away_abbr": "ARI",
        "score_home": 0, "score_away": 0,
        "quarter": 1, "clock": "3:53",
        "play_clock": "28", "down": 1, "distance": 10,
        "field_position": "+24",
        "state": "play",
    },
    5900: {
        "team_home_abbr": "LAC", "team_away_abbr": "ARI",
        "score_home": 0, "score_away": 0,
        "quarter": 1, "clock": "3:21",
        "play_clock": "11", "down": 1, "distance": 10,
        "field_position": "+41",
        "state": "play",
    },
    6100: {
        "team_home_abbr": "LAC", "team_away_abbr": "ARI",
        "score_home": 0, "score_away": 0,
        "quarter": 1, "clock": "3:18",
        "play_clock": "11", "down": 1, "distance": 10,
        "field_position": "+47",
        "state": "play",
    },
    6300: {
        "team_home_abbr": "LAC", "team_away_abbr": "ARI",
        "score_home": 0, "score_away": 0,
        "quarter": 1, "clock": "2:50",
        "play_clock": "14", "down": 1, "distance": 10,
        "field_position": "+30",
        "state": "play",
    },
    6421: {
        "team_home_abbr": "LAC", "team_away_abbr": "ARI",
        "score_home": 0, "score_away": 0,
        "quarter": 1, "clock": "2:48",
        "play_clock": "12", "down": 1, "distance": 10,
        "field_position": "+30",
        "state": "play",
    },
    7000: {
        "team_home_abbr": "LAC", "team_away_abbr": "ARI",
        "score_home": 0, "score_away": 0,
        "quarter": 1, "clock": "2:29",
        "play_clock": "28", "down": 1, "distance": 10,
        "field_position": "+10",
        "state": "play",
    },
    7049: {
        "team_home_abbr": "LAC", "team_away_abbr": "ARI",
        "score_home": 0, "score_away": 0,
        "quarter": 1, "clock": "2:28",
        "play_clock": "28", "down": 1, "distance": 10,
        "field_position": "+70",
        "state": "play",
    },
}

FRAME_PATH = REPO_ROOT / "scripts" / "hud_calibration" / "frames"
REPORT_PATH = REPO_ROOT / "agents" / "capture" / "fixtures" / "real" / "m45_ocr_validation.json"

# Elements that should read on every frame regardless of state.
STATE_INDEPENDENT = {"team_home_abbr", "team_away_abbr", "score_home", "score_away", "quarter", "clock"}
# Elements that depend on state (kickoff vs play).
STATE_DEPENDENT_PLAY = {"play_clock", "down", "distance", "field_position"}


def matches(expected, actual) -> bool:
    if expected is None:
        return actual is None or actual == "" or actual == 0
    if isinstance(expected, int) and isinstance(actual, int):
        return expected == actual
    if isinstance(expected, str) and isinstance(actual, str):
        return expected.upper() == actual.upper()
    if isinstance(expected, str) and isinstance(actual, int):
        return str(actual) == expected
    return False


def main() -> int:
    pipeline = OCRPipeline()
    frame_results: list[dict] = []
    per_element_success: dict[str, dict[str, int]] = {}

    print("Loading OCR pipeline (lazy EasyOCR — first read will be slow)…")
    t_start_total = time.monotonic()

    for idx, gt in GROUND_TRUTH.items():
        frame_path = FRAME_PATH / f"frame_{idx:06d}.png"
        if not frame_path.exists():
            print(f"WARN: frame missing: {frame_path}")
            continue
        img = cv2.imread(str(frame_path))
        t0 = time.monotonic()
        snap = pipeline.read_frame(img)
        elapsed_ms = round((time.monotonic() - t0) * 1000.0, 1)
        actual = {
            "team_home_abbr": snap.team_home_abbr,
            "team_away_abbr": snap.team_away_abbr,
            "score_home": snap.score_home,
            "score_away": snap.score_away,
            "quarter": snap.quarter,
            "clock": snap.clock,
            "play_clock": snap.play_clock,
            "down": snap.down,
            "distance": snap.distance,
            "field_position": snap.field_position,
        }

        per_field: dict[str, dict] = {}
        for field in ["team_home_abbr", "team_away_abbr", "score_home",
                      "score_away", "quarter", "clock", "play_clock",
                      "down", "distance", "field_position"]:
            ok = matches(gt[field], actual[field])
            per_field[field] = {
                "expected": gt[field],
                "actual": actual[field],
                "match": ok,
            }
            bucket = per_element_success.setdefault(
                field, {"hits": 0, "trials": 0, "play_hits": 0, "play_trials": 0,
                        "kickoff_hits": 0, "kickoff_trials": 0}
            )
            bucket["trials"] += 1
            bucket["hits"] += int(ok)
            if gt["state"] == "play":
                bucket["play_trials"] += 1
                bucket["play_hits"] += int(ok)
            else:
                bucket["kickoff_trials"] += 1
                bucket["kickoff_hits"] += int(ok)

        frame_results.append({
            "frame_idx": idx,
            "state": gt["state"],
            "elapsed_ms": elapsed_ms,
            "fields": per_field,
            "ocr_overall_confidence": snap.confidence_overall,
        })
        print(f"frame {idx} ({gt['state']}): "
              f"{sum(1 for f in per_field.values() if f['match'])}/{len(per_field)} fields matched "
              f"({elapsed_ms} ms)")

    elapsed_total = round(time.monotonic() - t_start_total, 1)

    # Summary per element.
    summary_per_element: dict[str, dict] = {}
    for field, bucket in per_element_success.items():
        all_pct = round(100.0 * bucket["hits"] / bucket["trials"], 1) if bucket["trials"] else 0.0
        play_pct = round(100.0 * bucket["play_hits"] / bucket["play_trials"], 1) if bucket["play_trials"] else 0.0
        kick_pct = round(100.0 * bucket["kickoff_hits"] / bucket["kickoff_trials"], 1) if bucket["kickoff_trials"] else 0.0
        summary_per_element[field] = {
            "all_states_pct": all_pct,
            "play_state_pct": play_pct,
            "kickoff_state_pct": kick_pct,
            "raw": bucket,
        }

    overall_play_only = sum(
        bucket["play_hits"] for f, bucket in per_element_success.items()
        if f in STATE_INDEPENDENT or f in STATE_DEPENDENT_PLAY
    )
    overall_play_trials = sum(
        bucket["play_trials"] for f, bucket in per_element_success.items()
        if f in STATE_INDEPENDENT or f in STATE_DEPENDENT_PLAY
    )

    report = {
        "milestone": "M4.5",
        "calibration_source": "scripts/hud_calibration/frames/frame_*.png",
        "frames_evaluated": list(GROUND_TRUTH.keys()),
        "elapsed_total_sec": elapsed_total,
        "per_frame": frame_results,
        "per_element_success_rate": summary_per_element,
        "overall_play_state_success_rate": round(
            100.0 * overall_play_only / overall_play_trials, 1
        ) if overall_play_trials else 0.0,
        "acceptance_threshold_pct": 80.0,
        "elements_meeting_acceptance_in_play_state": [
            f for f, s in summary_per_element.items() if s["play_state_pct"] >= 80.0
        ],
        "elements_below_acceptance_in_play_state": [
            f for f, s in summary_per_element.items() if s["play_state_pct"] < 80.0
        ],
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nreport -> {REPORT_PATH}")
    print("\nPer-element success (play state only):")
    for f, s in summary_per_element.items():
        marker = "OK" if s["play_state_pct"] >= 80.0 else "FAIL"
        print(f"  [{marker}] {f}: {s['play_state_pct']}% (across {s['raw']['play_trials']} play frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
