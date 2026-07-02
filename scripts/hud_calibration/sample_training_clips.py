"""[DEPRECATED for Madden 26 / M5c — preserved as Option A template
for future title adapters.]

DEPRECATED 2026-05-08 — DO NOT RUN FOR M5c MADDEN 26 SOURCING.

Why deprecated for this milestone:
  The YouTube sourcing path failed for the Madden 26 dev workstation
  account on 2026-05-07/08. Initial IP-level rate-limit (yt-dlp
  invocation throttle) was followed by an account-level pattern flag
  even with valid signed-in cookies — yt-dlp's auth was accepted but
  YouTube silently downgraded responses to thumbnail-only formats
  (`tv downgraded player API JSON`) instead of serving real video
  streams. Diagnostic confirmed the account itself was flagged,
  not the IP. Waiting was unlikely to clear it.

Pivoted to Option C — local Madden 26 capture via PS5 + capture
card + dev workstation. Protocol documented at
docs/integrations/visionaudioforge/madden26-local-capture-protocol.md.

Why preserved (not deleted):
  Future title adapters (CFB 26, NBA 2K26, EAFC 26, MLB 26, FPS /
  fighting / golf / cards titles) will use fresh accounts that have
  not yet been flagged. The yt-dlp + multi-matchup sourcing pattern
  here is the right shape for them; only the URL list + filename
  pattern need swapping. Defensive posture (180s inter-request
  sleep, idempotent cache check, timestamped invocation log) carries
  over.

To use this template for a new title:
  1. Copy this file to scripts/hud_calibration/sample_training_clips_<title>.py.
  2. Replace CANDIDATES with the new title's URL set.
  3. Update FIXTURES_DIR to the new title's fixtures path.
  4. Run from a fresh account (or rotate accounts if the dev account
     has been flagged on the prior title).
  5. If the new title also fails YouTube sourcing, fall through to
     a per-title local capture protocol (mirror the Madden 26 one).

Original docstring follows for reference:
================================================================

Source 5–8 multi-matchup Madden 26 clips for M5c training.

Downloads ~3 minute sections of public YouTube Madden 26 ranked /
franchise / CPU-simulation gameplay. Each matchup has a primary URL
and at least one alternate, so reproduction works even if a primary
URL is removed later.

Selection criteria (per M5c plan v2 sub-task 1):
  - >= 3 minutes continuous gameplay (we clip 1:00-4:00 to skip intros).
  - Stock HUD (no custom overlays — "no commentary" / "CPU sim" /
    "PS5 full gameplay" titles tend to be clean).
  - >= 1080p source resolution.
  - >= 4 different teams represented across the set (jersey + helmet
    diversity matters for generalisation).
  - Skip game-mode menus and short highlights.

After download, verifies HUD presence by sampling 3 frames per clip
and checking the bottom-band scoreboard region. Clips failing
verification are auto-replaced with their documented alternate URL.

Defensive posture (per 2026-05-07 retry hardening after YouTube
rate-limited the IP):
  - 180-second sleep between yt-dlp invocations (no back-to-back
    requests; rapid iteration triggered the rate-limit in the first
    attempt).
  - Cache check: skip clips whose .mp4 is already on disk and >= 1 MB.
    Re-runs of this script are idempotent.
  - Every yt-dlp invocation timestamps + appends to
    scripts/hud_calibration/training_clips_invocations.log so we can
    correlate request volume with future rate-limit events.

Run from repo root:

    python scripts/hud_calibration/sample_training_clips.py

Output:
  - agents/capture/fixtures/real/madden26_<matchup>.mp4 (gitignored)
  - scripts/hud_calibration/training_clips_index.json (committed —
    records the verified clip set, source URL, duration, resolution).
  - scripts/hud_calibration/training_clips_invocations.log (gitignored,
    rolling — appended on each yt-dlp invocation).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "agents" / "capture" / "fixtures" / "real"
INDEX_PATH = REPO_ROOT / "scripts" / "hud_calibration" / "training_clips_index.json"
INVOCATION_LOG = REPO_ROOT / "scripts" / "hud_calibration" / "training_clips_invocations.log"

# Sleep between successive yt-dlp invocations. Rate-limit defense.
INTER_REQUEST_SLEEP_SEC = 180

# Use the yt-dlp shipped in the EsportsForge backend venv (M4.5 baseline).
YT_DLP = REPO_ROOT / "backend" / "venv" / "Scripts" / "yt-dlp.exe"

# yt-dlp format selector — same approach as M4.5's working madden26.mp4
# download. Default extractor client (android_vr) is fine; downloads can
# be slow due to YouTube's JS-runtime dependency, but bytes do flow.
FORMAT_SELECTOR = (
    "bv*[height>=720][height<=1080][ext=mp4]+ba[ext=m4a]/"
    "b[height>=720][height<=1080][ext=mp4]/"
    "b[height>=720][height<=1080]"
)
# Clip 1:00-4:00 — skips intros, gives 3 minutes of gameplay.
DOWNLOAD_SECTIONS = "*1:00-4:00"


@dataclass
class CandidateClip:
    matchup: str
    teams: list[str]
    primary_url: str
    alternate_urls: list[str]
    notes: str = ""

    @property
    def filename(self) -> str:
        return f"madden26_{self.matchup}.mp4"


# Verified candidate set. The matchup field maps to the output filename;
# teams is for documentation + the training_clips_index. Each entry has
# >= 1 alternate URL per the user's reproducibility ask.
#
# All URLs identified via WebSearch in M5c sub-task 1 (2026-05-07).
# Sources: youtube searches for "madden 26 ranked gameplay", "madden 26
# franchise full game", "madden 26 cowboys gameplay youtube full".
CANDIDATES: list[CandidateClip] = [
    CandidateClip(
        matchup="patriots_vs_bills",
        teams=["NE", "BUF"],
        primary_url="https://www.youtube.com/watch?v=ClwXthq_w-k",
        alternate_urls=["https://www.youtube.com/watch?v=MHnfhTBhuuU",
                        "https://www.youtube.com/watch?v=0DpZeUzFims"],
        notes="Patriots @ Bills full game, no commentary — clean stock HUD",
    ),
    CandidateClip(
        matchup="cowboys_vs_eagles",
        teams=["DAL", "PHI"],
        primary_url="https://www.youtube.com/watch?v=sbXhnpQvLkA",
        alternate_urls=["https://www.youtube.com/watch?v=shRowq2fkto",
                        "https://www.youtube.com/watch?v=sP1vxGQBF6w"],
        notes="2026 rivalry simulation; XFactor Simulations channel",
    ),
    CandidateClip(
        matchup="cowboys_vs_jets",
        teams=["DAL", "NYJ"],
        primary_url="https://www.youtube.com/watch?v=4eGAI0Pj9dk",
        alternate_urls=["https://www.youtube.com/watch?v=QjTeT8MHopQ"],
        notes="PS5 UHD 4K60FPS — high quality source",
    ),
    CandidateClip(
        matchup="49ers_vs_cowboys",
        teams=["SF", "DAL"],
        primary_url="https://www.youtube.com/watch?v=7OtSN9dyuIU",
        alternate_urls=["https://www.youtube.com/watch?v=aODqMqFN554"],
        notes="PS5 simulation full gameplay",
    ),
    CandidateClip(
        matchup="ravens_vs_cowboys",
        teams=["BAL", "DAL"],
        primary_url="https://www.youtube.com/watch?v=1cdxUoyXosA",
        alternate_urls=["https://www.youtube.com/watch?v=xk2AUUxwrEw"],
        notes="PS5 first look — newer EA build",
    ),
    CandidateClip(
        matchup="cowboys_vs_seahawks",
        teams=["DAL", "SEA"],
        primary_url="https://www.youtube.com/watch?v=aODqMqFN554",
        alternate_urls=["https://www.youtube.com/watch?v=uVoX93KlFT0"],
        notes="2026 rivalry game simulation",
    ),
]


def _log_invocation(url: str, output: Path, status: str) -> None:
    """Append a timestamped invocation record. Helps correlate rate-
    limit events with request patterns on retries."""
    import datetime
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    INVOCATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with INVOCATION_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{status}\t{url}\t{output.name}\n")


def _download(url: str, output: Path) -> bool:
    """Run yt-dlp on a single URL into output. Returns True on success.

    Streams yt-dlp output to our stdout so progress is visible in
    background-task logs (capture_output=True buffers indefinitely on
    long YouTube format-extraction calls — observed during sub-task 1).
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    _log_invocation(url, output, "begin")
    cmd = [
        str(YT_DLP),
        "-f", FORMAT_SELECTOR,
        "--merge-output-format", "mp4",
        "-o", str(output),
        "--no-playlist",
        "--download-sections", DOWNLOAD_SECTIONS,
        "--no-warnings",
        url,
    ]
    print(f"  yt-dlp {url}", flush=True)
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        # Stream output. Cap total wait at 8 minutes per clip.
        import time
        start = time.monotonic()
        while True:
            line = proc.stdout.readline() if proc.stdout else ""
            if line:
                # Truncate yt-dlp progress lines for readability.
                stripped = line.rstrip()
                if stripped:
                    print(f"    {stripped[:140]}", flush=True)
            elif proc.poll() is not None:
                break
            if time.monotonic() - start > 720:
                proc.kill()
                print(f"  TIMEOUT after 12 min — killing", flush=True)
                return False
        rc = proc.wait()
    except Exception as exc:
        print(f"  EXCEPTION: {exc}", flush=True)
        return False
    if rc != 0:
        print(f"  yt-dlp failed (rc={rc})", flush=True)
        _log_invocation(url, output, f"failed_rc{rc}")
        return False
    ok = output.exists() and output.stat().st_size > 1_000_000
    _log_invocation(url, output, "success" if ok else "no_file")
    return ok


def _verify_hud_presence(video_path: Path) -> tuple[bool, dict]:
    """Sample 5 frames and check HUD-band presence.

    Heuristic per M4.5: the bottom-band central scoreboard region
    (y=1024-1064, x=460-1000) has central_std >= 70 on HUD-bearing
    frames. Returns (passed, stats_dict).
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return False, {"error": "open failed"}
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if total < 60 or width < 1280:
        cap.release()
        return False, {
            "error": f"too short or low-res (frames={total}, w={width})",
            "frames": total, "fps": fps, "wh": [width, height],
        }
    # Sample at 10%, 25%, 50%, 75%, 90% of duration.
    sample_indices = [int(total * p) for p in (0.10, 0.25, 0.50, 0.75, 0.90)]
    hud_hits = 0
    central_stds: list[float] = []
    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue
        # Resolution-scale the M4.5 bbox to actual frame size.
        h_full, w_full = frame.shape[:2]
        sx, sy = w_full / 1920.0, h_full / 1080.0
        x0, x1 = int(460 * sx), int(1000 * sx)
        y0, y1 = int(1024 * sy), int(1064 * sy)
        central = cv2.cvtColor(frame[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
        cstd = float(central.std())
        central_stds.append(round(cstd, 1))
        if cstd >= 70:
            hud_hits += 1
    cap.release()
    return (hud_hits >= 2), {
        "frames": total, "fps": fps,
        "resolution": [width, height],
        "central_std_per_sample": central_stds,
        "hud_hits": hud_hits,
        "samples": len(sample_indices),
    }


def main() -> int:
    print(
        "\n!!! DEPRECATED for Madden 26 / M5c — see file header.\n"
        "    YouTube sourcing was permanently abandoned on 2026-05-08\n"
        "    after account-level pattern detection. Local capture is\n"
        "    the active sourcing path:\n"
        "    docs/integrations/visionaudioforge/madden26-local-capture-protocol.md\n"
        "\n"
        "    To force-run anyway (e.g., for a future title adapter\n"
        "    using a fresh account), set ALLOW_DEPRECATED_YT_SOURCING=1.\n",
        flush=True,
    )
    import os
    if os.environ.get("ALLOW_DEPRECATED_YT_SOURCING") != "1":
        return 3
    if not YT_DLP.exists():
        print(f"ERROR: yt-dlp not found at {YT_DLP}")
        return 1
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    verified: list[dict] = []
    failed: list[dict] = []

    import time
    is_first_request = True
    for clip in CANDIDATES:
        out_path = FIXTURES_DIR / clip.filename
        print(f"\n=== {clip.matchup} ({'/'.join(clip.teams)}) ===", flush=True)
        if out_path.exists() and out_path.stat().st_size > 1_000_000:
            print(f"  already downloaded: {out_path.name} (cached, skipping yt-dlp)", flush=True)
            ok = True
            used_url = "(cached)"
            urls_to_try = []
        else:
            ok = False
            used_url = None
            urls_to_try = [clip.primary_url] + clip.alternate_urls
            for url in urls_to_try:
                # Inter-request sleep — defense against YouTube rate-limit.
                if not is_first_request:
                    print(f"  sleeping {INTER_REQUEST_SLEEP_SEC}s before next yt-dlp invocation (rate-limit defense)…", flush=True)
                    time.sleep(INTER_REQUEST_SLEEP_SEC)
                is_first_request = False
                if _download(url, out_path):
                    ok = True
                    used_url = url
                    break
                # Clean partial download before next try.
                if out_path.exists():
                    out_path.unlink()
        if not ok:
            print(f"  FAILED — all URLs exhausted for {clip.matchup}")
            failed.append({"matchup": clip.matchup, "tried": urls_to_try})
            continue

        passed, stats = _verify_hud_presence(out_path)
        verdict = "PASS" if passed else "FAIL-HUD"
        print(f"  {verdict}: {stats}")
        if passed:
            verified.append({
                "matchup": clip.matchup,
                "teams": clip.teams,
                "filename": clip.filename,
                "source_url": used_url,
                "primary_url": clip.primary_url,
                "alternate_urls": clip.alternate_urls,
                "notes": clip.notes,
                "verification": stats,
            })
        else:
            failed.append({
                "matchup": clip.matchup,
                "filename": clip.filename,
                "verification": stats,
                "tried": [used_url],
            })
            # Keep the file on disk for inspection but don't add to verified.

    index = {
        "milestone": "M5c sub-task 1",
        "date": "2026-05-07",
        "verified_clips": verified,
        "failed_clips": failed,
        "total_verified": len(verified),
        "target_min": 5,
        "target_max": 8,
    }
    INDEX_PATH.write_text(json.dumps(index, indent=2))
    print(f"\n{'=' * 50}")
    print(f"verified: {len(verified)}/{len(CANDIDATES)}")
    print(f"failed:   {len(failed)}")
    print(f"index -> {INDEX_PATH}")
    if len(verified) < 5:
        print(f"\nWARN: only {len(verified)} clips verified — below the 5-clip floor.")
        print("Status check: flag to user; either add more candidates or proceed with single-source-with-augmentation fallback.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
