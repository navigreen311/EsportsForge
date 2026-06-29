# Madden 26 Local Capture Protocol

- **Status:** Active for M5c training data sourcing (2026-05-08 onward).
- **Established:** 2026-05-08, after the YouTube sourcing path was permanently deprecated due to account-level pattern detection on the dev account (see `scripts/hud_calibration/sample_training_clips.py` deprecation header).
- **Audience:** the dev workstation operator (Ivan); reusable template for future title adapters whose YouTube sourcing path is not viable.
- **Cross-references:** [HUD calibration methodology](madden26-hud-calibration-methodology.md), [M5c plan v2](../../phase-completions/0-vaf-m5c-plan.md), [Phase 0 status](../../phase-completions/0-vaf-foundation.md).

## Why this exists

YouTube-based training-data sourcing was the original Option A (per the M5c plan). It became unviable for the dev workstation's YouTube account after the rate-limit-then-account-flag escalation on 2026-05-07–08. The local capture path was the documented fallback (Option C); it is now the canonical path for this milestone.

The hardware pipeline is **proven**: the M4.5 fixture (`agents/capture/fixtures/real/madden26.mp4`, LAC vs ARI, 2:00 of 1080p59.94) was captured through the same setup and produced 9 of 10 OCR-element acceptance against the calibrated `hud_regions.json`. This protocol formalises that path so future captures hit the same quality bar.

## Capture hardware

Same pipeline as the M4.5 fixture:

- **PS5** running Madden 26 (purchased 2026-05-08 for this milestone).
- **Capture card** (HDMI passthrough → USB, recording at 1080p60 minimum).
- **CLX PC** (Ivan's dev workstation) — receives the capture, encodes, writes the .mp4.

The capture-card model and recording software are operator-owned; this protocol is agnostic to which specific tools are used as long as the resulting file meets the per-clip requirements below.

## Per-clip requirements

| Field | Requirement |
| --- | --- |
| **Duration** | 3–5 minutes continuous gameplay (no menu transitions in the middle) |
| **Resolution** | 1080p (1920×1080); calibrated `hud_regions.json` is at this resolution |
| **Frame rate** | ≥30 fps source; 60 fps preferred (matches M4.5 fixture) |
| **HUD** | Stock Madden 26 HUD only — no streaming overlays, no facecam window, no chyron banners, no caption boxes |
| **Game mode** | CPU vs CPU (Play Now → "CPU vs CPU" or franchise-mode super-sim with HUD visible). Reason: consistent gameplay quality, varied formations, no human-input bias toward favourite plays. |
| **Audio** | Optional; not used by the classifier. Strip during encode if it reduces file size. |
| **Codec** | H.264 baseline or main profile (matches M4.5 fixture's `madden26.mp4`) |
| **Container** | `.mp4` (`.webm`, `.mkv` also accepted; the harness reads via OpenCV which is codec-agnostic) |

## Matchup diversity requirement

Per the M5c plan v2 sub-task 1: **≥ 4 different teams across the 5–8 clip set**. Single-team training overfits the classifier on jersey colour, helmet shape, and stadium presentation rather than on formation geometry.

Recommended matchup distribution (5–8 clips):

| Clip # | Suggested matchup | Diversity factor |
| --- | --- | --- |
| 1 | LAC vs ARI (already captured — M4.5 fixture, can be reused) | Existing — reuse |
| 2 | KC vs BUF | Different jersey colour palette + different stadium |
| 3 | DAL vs PHI | NFC East rivalry — distinct uniforms |
| 4 | SF vs SEA | NFC West |
| 5 | GB vs CHI | Cold-weather lighting variation |
| 6–8 (optional) | Operator's pick | Add diversity if available |

The exact teams are operator's call; the diversity bar is what matters. If 5 clips all feature the Cowboys (a likely outcome if the operator is a Cowboys fan), the dataset has only one offensive team's jersey — the classifier will overfit on it.

## Filename convention

```
agents/capture/fixtures/real/madden26_<team1>_vs_<team2>.mp4
```

Where `<team1>` and `<team2>` are NFL team abbreviations as shown on the Madden HUD (e.g., `LAC`, `ARI`, `KC`, `BUF`, `DAL`, `PHI`, `SF`, `SEA`). Lowercase. Examples:

- `madden26_lac_vs_ari.mp4` (this is the M4.5 fixture's preferred new name; the original `madden26.mp4` is preserved for backward compatibility but will be aliased on next sourcing-script run).
- `madden26_kc_vs_buf.mp4`
- `madden26_dal_vs_phi.mp4`
- `madden26_sf_vs_sea.mp4`
- `madden26_gb_vs_chi.mp4`

## Fixtures path

```
agents/capture/fixtures/real/
```

Already gitignored at the `.mp4`/`.webm`/`.mkv` patterns (see `.gitignore`). New clips dropped here are NOT committed; only the validation reports + index files are.

## HUD verification step

After each clip is captured + saved to the fixtures path, run the verification harness:

```bash
# From repo root, with services/visionaudioforge/.venv active:
python scripts/hud_calibration/verify_capture.py \
  --video agents/capture/fixtures/real/madden26_<matchup>.mp4
```

The verification script (`scripts/hud_calibration/verify_capture.py`, added 2026-06-29 with the first capture batch) samples 5 frames at 10/25/50/75/90% positions and checks:

1. Resolution matches 1920×1080 (or scales linearly per the `_crop` helper); framerate ≥30 fps; codec H.264.
2. Bottom-band HUD region present (`central_std >= 70` in the scoreboard area, same heuristic the M4.5 calibration used).
3. Sample OCR readings (production `OCRPipeline`) confirm `team_home_abbr` / `team_away_abbr` parse to the expected NFL abbreviations.

The scoreboard-band + abbrev checks (2 and 3) apply only to **matchup** clips. **Practice-mode** clips render a different play-call HUD with no scoreboard band, so they are verified on container sanity alone (`--video` auto-detects clip kind by filename). Run the whole batch with `--all`.

Output: `agents/capture/fixtures/real/<matchup>_capture_verification.json` per clip + `_capture_verification_summary.json` for `--all`. Pass/fail logged.

> **HUD-layout caution (discovered 2026-06-29).** The first capture batch uses a **compact center-clustered scorebug**, not the M4.5 fixture's left-anchored full-width broadcast bar that `hud_regions.json` v2.0.0 was calibrated against. The container is perfect (all 1080p30 H.264) but the v2.0.0 bboxes miss the new HUD, so checks 2–3 report FAIL on matchup clips against v2.0.0 — a coordinate mismatch, **not** a capture defect (a first-pass re-calibration reads the new layout correctly). A failing matchup clip here means "re-calibrate `hud_regions.json` for this scorebug (sub-task 1b)", not "re-capture". Only re-capture if the container checks (resolution/fps/codec) or HUD *presence* (visually confirmed) genuinely fail.

## Operator handoff (for clip delivery)

When the operator drops clips into `agents/capture/fixtures/real/`:

1. Send a status update naming the new files.
2. Wait for explicit instruction to run `verify_capture.py` (per the user's gating rule — no auto-run on file detection).
3. After verification, status report: per-clip pass/fail + measured `central_std` numbers.

## Reusability for future title adapters

This protocol pattern transfers to:

- **CFB 26** — same EA Sports engine, same HUD topology. Re-use the verification heuristic with CFB-specific abbreviation list.
- **NBA 2K26 / EA FC 26 / MLB 26** — different HUD layouts; calibrate first via the [HUD calibration methodology](madden26-hud-calibration-methodology.md), then write a `<title>-local-capture-protocol.md` mirroring this doc.
- **FPS / fighting / golf / cards titles** — same shape: capture hardware → 3–5 min clip requirements → matchup/scenario diversity → filename convention → fixtures path → verification step.

The only Madden-specific elements are: HUD-band coordinates, NFL team abbreviation list, CPU-vs-CPU mode reference. Everything else is the reusable shape.

## Forge rule alignment

Per [FORGE_ARCHITECTURE_PATTERN.md](../../FORGE_ARCHITECTURE_PATTERN.md):

- **Rule 5** (adapters added without core changes) — capture protocol changes only the inputs to the Madden adapter's training run; no core service code touched.
- **Rule 4** (events are structured + canonical) — captured frames flow into the same `EventEnvelope` shape after training.
- **Rule 1** (multi-dimensional from day one) — capture protocol is per-title; future titles get their own.
