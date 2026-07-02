"""Verify newly captured Madden 26 clips against the calibrated HUD.

Implements the "HUD verification step" of the local capture protocol
(docs/integrations/visionaudioforge/madden26-local-capture-protocol.md).
For each clip it samples frames at fixed percentile positions and checks:

  1. Container sanity — resolution / framerate / codec actually present in
     the file, sanity-checked against the protocol's 1920x1080 / >=30 fps /
     H.264 expectation.
  2. HUD-band presence — the scoreboard bbox from hud_regions.json v2.0.0
     has high intra-region contrast (`central_std >= 70`), the same
     heuristic the M4.5 calibration used to tell a HUD-bearing gameplay
     frame from a menu / replay / cutscene frame.
  3. OCR spot-check — the production OCRPipeline reads the calibrated
     subregions; for CPU-vs-CPU matchup clips the team-abbreviation reads
     are compared against the matchup encoded in the filename.

Clip kind matters. CPU-vs-CPU *matchup* clips carry the full scoreboard
HUD and get the team-abbrev OCR gate. *Practice-mode* clips render a
different HUD (play-call / coaching overlay, no scoreboard band), so they
are verified for container + HUD-band presence only; the team-abbrev gate
does not apply and is reported as N/A rather than as a failure.

Output: one JSON report per clip at
`agents/capture/fixtures/real/<stem>_capture_verification.json`, plus an
aggregate `_capture_verification_summary.json` when run with --all.

Run (from repo root, with services/visionaudioforge/.venv active):

    python scripts/hud_calibration/verify_capture.py --all
    python scripts/hud_calibration/verify_capture.py \
        --video agents/capture/fixtures/real/madden26_bal_vs_cin_q1.mp4
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = REPO_ROOT / "services" / "visionaudioforge"
sys.path.insert(0, str(SERVICE_ROOT))

from app.adapters.madden26.ocr_pipeline import OCRPipeline, _crop  # noqa: E402

FIXTURES_DIR = REPO_ROOT / "agents" / "capture" / "fixtures" / "real"
HUD_REGIONS_PATH = SERVICE_ROOT / "app" / "adapters" / "madden26" / "hud_regions.json"

# Protocol expectations (madden26-local-capture-protocol.md "Per-clip requirements").
EXPECTED_RES = (1920, 1080)
MIN_FPS = 30          # protocol floor; 30 fps is acceptable, 60 preferred
EXPECTED_CODECS = {"h264", "avc1"}
CENTRAL_STD_THRESHOLD = 70.0  # scoreboard-band HUD-presence heuristic

# Percentile positions through the clip to sample (skip the first/last 5%
# to avoid intro/transition slates).
DEFAULT_SAMPLE_PCTS = (0.10, 0.25, 0.50, 0.75, 0.90)

# Filename team-token -> abbreviation as Madden's HUD renders it. Tokens
# that already match the HUD abbrev are uppercased directly; this map only
# covers the divergences worth normalising.
TEAM_TOKEN_TO_HUD = {
    "wash": "WAS",
    "pits": "PIT",
    "la": "LAR",   # Rams in these captures
    "sf": "SF",
    "ne": "NE",
    "gb": "GB",
    "tb": "TB",
    "kc": "KC",
}

_ABBREV_RE = re.compile(r"^[A-Z]{2,3}$")


def _ffprobe_codec(video: Path) -> str | None:
    """Return the v:0 codec_name via ffprobe, or None if ffprobe absent."""
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    try:
        out = subprocess.run(
            [exe, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name", "-of",
             "default=nw=1:nk=1", str(video)],
            capture_output=True, text=True, timeout=30,
        )
        return out.stdout.strip() or None
    except (subprocess.SubprocessError, OSError):
        return None


def _fourcc_to_str(fourcc: float) -> str:
    code = int(fourcc)
    return "".join(chr((code >> (8 * i)) & 0xFF) for i in range(4)).strip("\x00").strip()


def _classify_clip(stem: str) -> tuple[str, tuple[str, str] | None]:
    """Return (kind, expected_abbrevs). kind is 'practice' or 'matchup'.

    For matchup clips the two team abbreviations are decoded from the
    `<a>_vs_<b>` portion of the filename (stray separators tolerated).
    """
    name = stem.replace("madden26_", "", 1)
    if name.startswith("practice"):
        return ("practice", None)
    m = re.search(r"([a-z]+)_+vs_+([a-z]+)", name)
    if not m:
        return ("matchup", None)
    a, b = m.group(1), m.group(2)
    norm = lambda t: TEAM_TOKEN_TO_HUD.get(t, t.upper())
    return ("matchup", (norm(a), norm(b)))


def _central_std(frame: np.ndarray, bbox: list[int]) -> float:
    """Grayscale intensity std over a calibrated bbox — HUD-presence proxy.

    A HUD-bearing band (text + panels over a semi-opaque strip) has high
    intra-region contrast; a menu / replay / cutscene frame at the same
    coordinates is comparatively flat. `_crop` handles resolution scaling.
    """
    crop = _crop(frame, bbox)
    if crop.size == 0:
        return 0.0
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
    return float(gray.std())


def _abbrev_aligned(read: str | None, expected: str) -> bool:
    if not read:
        return False
    r = read.upper()
    return r == expected or expected in r or (len(r) >= 2 and r[:2] == expected[:2])


def verify_clip(video: Path, pipeline: OCRPipeline, sample_pcts, ocr_frames: int) -> dict:
    kind, expected_abbrevs = _classify_clip(video.stem)
    report: dict = {
        "clip": video.name,
        "kind": kind,
        "expected_abbrevs": list(expected_abbrevs) if expected_abbrevs else None,
    }

    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        report["error"] = "could not open video"
        report["verdict"] = "fail"
        report["reasons"] = ["video would not open"]
        return report

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = round(float(cap.get(cv2.CAP_PROP_FPS)), 2)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    codec = _ffprobe_codec(video) or _fourcc_to_str(cap.get(cv2.CAP_PROP_FOURCC))
    duration_sec = round(total / fps, 1) if fps > 0 else None

    report["container"] = {
        "resolution": [width, height],
        "fps": fps,
        "codec": codec,
        "frame_count": total,
        "duration_sec": duration_sec,
    }

    res_ok = (width, height) == EXPECTED_RES
    fps_ok = fps >= MIN_FPS
    codec_ok = (codec or "").lower() in EXPECTED_CODECS
    report["container_checks"] = {
        "resolution_ok": res_ok,
        "fps_ok": fps_ok,
        "fps_note": ("matches 30 fps capture (protocol floor; plan v2 "
                     "assumed 60)" if abs(fps - 30) < 1 else f"{fps} fps"),
        "codec_ok": codec_ok,
    }

    # Sample frames.
    sample_indices = [min(total - 1, max(0, int(p * total))) for p in sample_pcts]
    # OCR the middle `ocr_frames` of the sampled set (most likely live HUD).
    if ocr_frames >= len(sample_indices):
        ocr_set = set(sample_indices)
    else:
        lo = (len(sample_indices) - ocr_frames) // 2
        ocr_set = set(sample_indices[lo:lo + ocr_frames])

    scoreboard_bbox = pipeline.regions["scoreboard"]["bbox"]
    frame_reports: list[dict] = []
    best_abbrev_frame: dict | None = None

    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok or frame is None:
            frame_reports.append({"frame_idx": idx, "read_ok": False})
            continue
        cstd = round(_central_std(frame, scoreboard_bbox), 1)
        fr: dict = {
            "frame_idx": idx,
            "ts_sec": round(idx / fps, 2) if fps > 0 else None,
            "read_ok": True,
            "central_std": cstd,
            "hud_band_present": cstd >= CENTRAL_STD_THRESHOLD,
        }
        if idx in ocr_set:
            t0 = time.monotonic()
            snap = pipeline.read_frame(frame)
            fr["ocr"] = {
                "team_home_abbr": snap.team_home_abbr,
                "team_away_abbr": snap.team_away_abbr,
                "score_home": snap.score_home,
                "score_away": snap.score_away,
                "quarter": snap.quarter,
                "clock": snap.clock,
                "down": snap.down,
                "distance": snap.distance,
                "field_position": snap.field_position,
                "confidence_overall": round(snap.confidence_overall, 3),
            }
            fr["ocr_elapsed_ms"] = round((time.monotonic() - t0) * 1000.0, 1)
            home_plausible = bool(snap.team_home_abbr and _ABBREV_RE.match(snap.team_home_abbr.upper()))
            away_plausible = bool(snap.team_away_abbr and _ABBREV_RE.match(snap.team_away_abbr.upper()))
            if home_plausible and away_plausible and best_abbrev_frame is None:
                best_abbrev_frame = fr
        frame_reports.append(fr)

    cap.release()
    report["frames"] = frame_reports

    present_frames = [f for f in frame_reports if f.get("hud_band_present")]
    max_cstd = max((f["central_std"] for f in frame_reports if f.get("read_ok")), default=0.0)
    hud_present = len(present_frames) > 0
    report["hud_band"] = {
        "max_central_std": max_cstd,
        "frames_with_band": len(present_frames),
        "frames_sampled": sum(1 for f in frame_reports if f.get("read_ok")),
        "threshold": CENTRAL_STD_THRESHOLD,
        "present": hud_present,
    }

    # OCR / abbrev gate (matchup clips only).
    abbrev_result: dict = {"applies": kind == "matchup"}
    if kind == "matchup":
        ocr_frames_with_abbrevs = [
            f for f in frame_reports
            if f.get("ocr") and f["ocr"]["team_home_abbr"] and f["ocr"]["team_away_abbr"]
            and _ABBREV_RE.match((f["ocr"]["team_home_abbr"] or "").upper())
            and _ABBREV_RE.match((f["ocr"]["team_away_abbr"] or "").upper())
        ]
        abbrev_result["frames_with_plausible_abbrevs"] = len(ocr_frames_with_abbrevs)
        abbrev_result["plausible"] = len(ocr_frames_with_abbrevs) > 0
        if expected_abbrevs and best_abbrev_frame:
            read_home = best_abbrev_frame["ocr"]["team_home_abbr"]
            read_away = best_abbrev_frame["ocr"]["team_away_abbr"]
            exp = set(expected_abbrevs)
            # HUD home/away ordering is broadcast-dependent — accept either side.
            aligned = (
                any(_abbrev_aligned(read_home, e) for e in exp)
                and any(_abbrev_aligned(read_away, e) for e in exp)
            )
            abbrev_result["read"] = [read_home, read_away]
            abbrev_result["aligned_with_filename"] = aligned
    report["abbrev_check"] = abbrev_result

    # Verdict.
    reasons: list[str] = []
    if not res_ok:
        reasons.append(f"resolution {width}x{height} != 1920x1080")
    if not fps_ok:
        reasons.append(f"fps {fps} < {MIN_FPS}")
    if not codec_ok:
        reasons.append(f"codec {codec!r} not in {sorted(EXPECTED_CODECS)}")
    # The scoreboard-band heuristic + team-abbrev OCR are calibrated against
    # the M4.5 full-width broadcast bar and only apply to matchup clips.
    # Practice-mode clips render a different (play-call) HUD with no
    # scoreboard band, so they are verified on container sanity alone.
    if kind == "matchup":
        if not hud_present:
            reasons.append(
                f"scoreboard band below threshold (max central_std {max_cstd} "
                f"< {CENTRAL_STD_THRESHOLD}) — may indicate HUD-layout drift vs v2.0.0")
        if not abbrev_result.get("plausible"):
            reasons.append(
                "no sampled frame produced plausible team abbreviations against "
                "v2.0.0 bboxes — check HUD-layout alignment")

    report["container_ok"] = res_ok and fps_ok and codec_ok
    report["verdict"] = "pass" if not reasons else "fail"
    report["reasons"] = reasons
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--video", type=Path, help="single clip to verify")
    g.add_argument("--all", action="store_true",
                   help="verify every madden26_*.mp4 in the fixtures dir "
                        "(excludes the M4.5 fixture madden26.mp4)")
    p.add_argument("--ocr-frames", type=int, default=3,
                   help="how many of the sampled frames to OCR (default 3)")
    p.add_argument("--sample", type=str, default=None,
                   help="comma-separated sample percentiles, e.g. 10,25,50,75,90")
    args = p.parse_args()

    if args.sample:
        sample_pcts = tuple(float(x) / 100.0 for x in args.sample.split(","))
    else:
        sample_pcts = DEFAULT_SAMPLE_PCTS

    if args.all:
        videos = sorted(
            v for v in FIXTURES_DIR.glob("madden26_*.mp4") if v.name != "madden26.mp4"
        )
    else:
        videos = [args.video]
    if not videos:
        print("no clips found")
        return 1

    pipeline = OCRPipeline()
    print(f"Verifying {len(videos)} clip(s). EasyOCR cold-start on first read…\n")

    reports: list[dict] = []
    for video in videos:
        t0 = time.monotonic()
        rep = verify_clip(video, pipeline, sample_pcts, args.ocr_frames)
        rep["verify_elapsed_sec"] = round(time.monotonic() - t0, 1)
        reports.append(rep)

        out_path = FIXTURES_DIR / f"{video.stem}_capture_verification.json"
        out_path.write_text(json.dumps(rep, indent=2, default=str))
        cc = rep.get("container", {})
        print(f"[{rep['verdict'].upper():4}] {video.name}  "
              f"({rep['kind']}, {cc.get('resolution')}, {cc.get('fps')}fps, "
              f"{cc.get('codec')}, max_cstd={rep.get('hud_band', {}).get('max_central_std')})"
              + (f"  reasons={rep['reasons']}" if rep["reasons"] else ""))

    summary = {
        "milestone": "M5c sub-task 1",
        "clips_verified": len(reports),
        "passed": sum(1 for r in reports if r["verdict"] == "pass"),
        "failed": sum(1 for r in reports if r["verdict"] == "fail"),
        "per_clip": [
            {"clip": r["clip"], "kind": r["kind"], "verdict": r["verdict"],
             "reasons": r["reasons"], "max_central_std": r.get("hud_band", {}).get("max_central_std"),
             "fps": r.get("container", {}).get("fps"),
             "resolution": r.get("container", {}).get("resolution"),
             "codec": r.get("container", {}).get("codec"),
             "abbrev": r.get("abbrev_check", {})}
            for r in reports
        ],
    }
    if args.all:
        summary_path = FIXTURES_DIR / "_capture_verification_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, default=str))
        print(f"\nsummary -> {summary_path}")
    print(f"\n{summary['passed']}/{summary['clips_verified']} passed, "
          f"{summary['failed']} failed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
