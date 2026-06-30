# HUD Region Calibration Methodology

- **Status:** v1 — established during M4.5 (Phase 0 remainder, 2026-05-07).
- **Audience:** future title-adapter authors (CFB 26, NBA 2K26, EAFC 26, MLB 26, Warzone, Fortnite, UFC 5, Undisputed, PGA 2K25, Video Poker).
- **Reference adapter:** `services/visionaudioforge/app/adapters/madden26/`. Read the Madden adapter as the worked example while applying this methodology to a new title.
- **Cross-references:** [docs/specs/02-visionaudioforge-core.md §"OCR pipeline"](../../specs/02-visionaudioforge-core.md), [docs/specs/04-madden26-adapter-spec.md](../../specs/04-madden26-adapter-spec.md), [Forge architecture pattern](../../FORGE_ARCHITECTURE_PATTERN.md) Rule 5 (adapters added without core changes).

## Why this exists

Phase 0's `hud_regions.json` was derived from the spec, not from measured frames. Real Madden 26 footage revealed three problems:

1. The HUD coordinate system was **wrong** — Madden 26 ships its HUD in a bottom band, not a top band.
2. Several subregions overlapped the wrong content (e.g., the spec's "team_home_abbr" bbox hit the helmet logo rather than the team-abbreviation text).
3. There was no reproducible procedure for measuring real coords, so the next title would repeat the same error.

This methodology fixes (3) so that calibration becomes a one-day deterministic exercise per title rather than a guessing game.

## Prerequisites

- A representative video clip of the title at the target capture resolution (1920×1080 by default; methodology scales — see "Resolution scaling" below).
- The clip must contain at least 10 frames showing the persistent gameplay HUD (i.e., not menu screens, not replays, not intro/outro slates).
- Python venv active (per the service's README; for VAF, `services/visionaudioforge/.venv`).
- OpenCV available (`opencv-python-headless`) — already in `requirements.txt`.

## Step 1 — Sample frames across game states

Goal: sample ≥ 12 frames spread across three states of the title's UI:

- **Pre-action / pre-snap / pre-pitch / lobby** — HUD elements at rest.
- **Mid-action / mid-play** — HUD updating (e.g., game clock advancing, kill-feed flashing).
- **Menu / post-action** — pause menu or score recap or replay overlay (any state where the HUD differs from gameplay).

Use the sampler pattern at `scripts/hud_calibration/sample_frames.py` (uniform percentile sampling across the clip). For titles where uniform sampling misses the gameplay window — e.g., a clip with a long facecam intro — also use `scripts/hud_calibration/sample_dense_gameplay.py` as a template for index-range sampling once you've identified the gameplay window.

Save all sampled frames to `scripts/hud_calibration/frames/<title>/frame_<idx>.png`. The 6-digit zero-padded frame index in the filename is the cross-reference to the source video.

## Step 2 — Identify HUD-bearing frames

Open each sampled PNG. By eye, classify each frame:

- ✅ **HUD-bearing gameplay** — the production HUD overlay is visible. These frames feed the calibration.
- ❌ **HUD-absent gameplay** — gameplay action with no HUD overlay (some content creators disable HUD; we cannot calibrate from these).
- ❌ **Menu / cutscene / replay** — different UI; calibrate separately if the OCR pipeline needs to read these too.

You need at least 5 HUD-bearing gameplay frames spread across pre-snap/post-snap/etc. If the clip yields fewer than 5, source another clip — calibration on too few frames is unreliable.

For Madden 26 in M4.5, the calibration set was: frames 4400, 4538, 6100, 6421, 7049 from `agents/capture/fixtures/real/madden26.mp4`.

## Step 3 — Extract HUD strip(s)

Use `scripts/hud_calibration/extract_hud_strip.py` (template) to crop the HUD region from each calibration frame and save as standalone PNG strips. The strip width is the full frame width (1920 px); the strip height is the HUD band's height (typically 60–120 px).

The strips are the calibration substrate. They are the right resolution for measuring sub-element pixel coordinates without scaling artifacts.

For Madden 26: the bottom band runs from y=1006 to y=1080 (74 px tall) and spans the full width.

## Step 4 — Measure subregion bboxes iteratively

Use `scripts/hud_calibration/annotate_bboxes.py` (template) to:

1. Define **candidate bboxes** in the script's `CANDIDATES` dict — `[x, y, w, h]` per subregion. First pass is allowed to be rough.
2. Run the script against one calibration frame. The script:
   - Saves an annotated PNG with each bbox drawn as a coloured rectangle + label.
   - Saves each subregion's crop as a separate PNG.
3. Open each subregion crop. Verify the bbox tightly bounds the intended element. Adjust coords. Re-run.
4. Once tight on the first frame, re-run against the remaining calibration frames. Bboxes must produce the same content category on each frame (e.g., `team_home_abbr` reads "LAC" on every frame). If a bbox drifts across frames, the layout is not stable and the title's HUD requires per-state regions instead of a single fixed region.

Iteration is normal — the M4.5 calibration took two passes to converge.

**Iteration tactic:** when a candidate bbox is clearly off, look at the saved crop PNG and use the visual offset to pick the correction. "Crop showed the helmet, I wanted the abbreviation → shift x right by ~150 px."

## Step 5 — Validate via OCR

Use `scripts/hud_calibration/validate_ocr.py` (template) to:

1. Hand-label expected ground truth per HUD element per frame (in the `GROUND_TRUTH` dict). For each calibration frame, write out the expected score, clock, abbreviation, etc. by looking at the frame.
2. Mark each frame's **state**: `play`, `kickoff`, `menu`, etc. Some elements only render meaningfully in certain states (e.g., Madden's `down` and `distance` panels show "KICKOFF" / "+35" during kickoff frames, not numeric values).
3. Run the validator. It runs the production OCR pipeline against each frame, compares each subregion read to ground truth, and reports per-element success rate.
4. **Acceptance: ≥ 80% per HUD element on the calibrated frames in their primary state.** State-dependent elements are scored against frames in their target state (e.g., `down` is scored against play-state frames, not kickoff-state frames).

If an element scores below 80%:
- Re-inspect the bbox in step 4.
- Check OCR allowlist (digits-only allowlist on a digit field; alpha allowlist on team abbreviations).
- Check resolution scaling (see below).

## Step 6 — Commit the calibration

Bundle into a single commit:

- `services/visionaudioforge/app/adapters/<title>/hud_regions.json` — calibrated coords, with a `calibration` block listing source clip, date, milestone, calibrated frame indices, and notes on state-dependent regions.
- `scripts/hud_calibration/<helpers>` — sampler / strip extractor / annotator / validator. Each script can be templated from Madden's M4.5 work.
- `agents/capture/fixtures/<title>/m45_ocr_validation.json` — validator output as evidence.
- The methodology doc (this file) updated only if the new title surfaces a methodology gap.

Commit message references the milestone and the title's adapter spec section.

## Resolution scaling

Calibration coords are stored at 1920×1080. The `_crop` helper in `services/visionaudioforge/app/adapters/madden26/ocr_pipeline.py` scales coords to the actual frame resolution at read time:

```python
if (h_full, w_full) != (1080, 1920):
    sx, sy = w_full / 1920.0, h_full / 1080.0
    x, y, w, h = int(x * sx), int(y * sy), int(w * sx), int(h * sy)
```

For titles whose HUD doesn't scale linearly across resolutions (e.g., a HUD that reflows at narrower aspect ratios), record the calibration resolution per resolution bucket in `hud_regions.json` instead of trusting linear scaling.

## State-dependent regions

Some HUD subregions render different content based on game state:

- **Madden 26**: `down` and `distance` show numeric values during play; show "KICKOFF" / "PUNT" / "EXTRA POINT" during transition states.
- **Likely-similar titles**: CFB 26 (same engine), NBA 2K26 (period vs free-throw vs replay), EA FC 26 (in-play vs goal celebration vs replay).

Strategy: keep the bbox stable; let the OCR pipeline classify state by reading multiple regions and applying state-specific allowlists. Document state branches in the title's adapter spec.

## What goes wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| OCR returns null on a region | Bbox is wrong; allowlist is wrong; image is too small (< ~30 px tall after upscale) | Re-inspect the cropped PNG. Check allowlist. The `_read_text` helper upscales 3× — that may not be enough for very small text. |
| OCR returns garbage characters | Allowlist too permissive; region overlaps a graphic element | Restrict allowlist; tighten the bbox |
| Bbox works on frame 1 but fails on frame 100 | HUD reflows on an event boundary (e.g., during replay) | Multi-state bboxes — record per-state regions in `hud_regions.json` |
| Calibration appears correct but downstream events look wrong | OCR cadence: per-frame OCR is too slow on real footage; cache per-snap | OCR cadence reform — see Phase 0 milestone breakdown |
| Bboxes correct for the dev clip, wrong for production capture | Resolution scaling assumption is broken | Record per-resolution calibration; add to `hud_regions.json` |

## HUD drift between calibrations — recurring maintenance

**Calibration is not a one-time setup. It is recurring maintenance driven by external game updates you do not control.** A title publisher (EA, 2K, etc.) can change the on-screen HUD in a seasonal patch, a presentation-mode default, or a UI refresh — and the moment they do, a calibration measured against the old footage stops aligning. This happened to Madden 26 between M4.5 and M5c (see ADR 0013).

### Worked example — Madden 26 v2.0.0 → v2.1.0 (M5c sub-task 1b)

`hud_regions.json` v2.0.0 was calibrated (M4.5) against `madden26.mp4`, which shows a **left-anchored full-width broadcast bar**. The M5c capture batch (2026-06-25–27) instead shows a **compact center-clustered scorebug**. Same game, same 1080p30 capture — a different HUD presentation. Every v2.0.0 bbox missed the new layout: the scoreboard cluster had shifted **+213…+304 px right** and the down/distance panel had collapsed **−449…−854 px left** into a centered sub-row. Result: 0/10 elements readable against v2.0.0 on the new clips, despite the captures being pristine.

### Detection signal — how you know drift happened

Two cheap signals, both produced by `scripts/hud_calibration/verify_capture.py`:

1. **`central_std` of the calibrated scoreboard band drops / straddles its threshold** — the band coordinates now average HUD-over-background instead of solid HUD.
2. **OCR yields 0 valid reads of stable fields** (team abbreviations parse to garbage) on footage that is visually fine.

A human glance at one frame confirms it instantly: the HUD is legible, just not where the bboxes are. **Drift is a coordinate/preprocessing problem, not a capture defect** — do not re-capture; re-calibrate.

### Re-calibration workflow

Re-run Steps 1–6 against the new footage, with three deltas:

- **Step 1 sampler:** `scripts/hud_calibration/sample_calibration_frames.py` finds clean-HUD frames via a valid-clock gate and spreads them across game states; it is clip-set-agnostic and reusable for any title-update re-cal. Cover the stress cases the new render introduces (for the v2.1.0 scorebug: white-on-saturated-team-color abbrevs/scores, smaller element type, KICKOFF/GOAL panels).
- **Step 4 measurement:** re-crop, do not re-translate — element type sizes change between presentations (v2.1.0 `down` is 95→60 px wide).
- **Step 5 validator:** use a mismatch-printing validator (`validate_ocr_v21.py` is the v2.1.0 example) so a wrong ground-truth label can be told apart from a real OCR miss. During v2.1.0 several first-pass GT labels were wrong and the audit caught them — trust the mismatch list, not the headline percentage, until you have eyeballed the disputes.

### Font/preprocessing confusions are presentation-specific

The new render's font carries its own OCR confusions, fixed in the adapter (never core):

- v2.1.0 ordinals OCR "2ND"→"ZND", "4TH"→"ATR" — handled by additive `_ORDINAL_MAP` aliases.
- v2.1.0 score "0" renders as a ring read as "U" — handled by reading scores without a digit allowlist + a `_parse_score` glyph normalizer.

### Versioning + fixture transition

- **Bump `schema_version`** (2.0.0 → 2.1.0) and record a `supersedes` note in the `calibration` block.
- **Replace, then re-baseline** (the M5c decision): the new layout becomes *the* calibration. Retire the old reference clip as the OCR source but **keep it on disk** as historical reference for the superseded version. Any downstream baseline pinned to the old clip (e.g. the OCR-smoothing regression set) migrates to a clip on the new layout — document the swap explicitly, never silently re-point.
- **Accept known-weak elements honestly.** v2.1.0 scores land below the 80% bar (large italic numerals defeat EasyOCR on 2-digit values); documented as a v0.1 known-weak element with a tracked follow-up, exactly as field_position was the weak element in v2.0.0. Do not hide it.

### Budget it

Treat per-title re-calibration as a recurring ~0.5–1.0 day line item whenever a capture batch trips the drift detector, not as a surprise. The cost is bounded because the workflow above is deterministic.

## Single-frame agent labeling limits (M5c sub-task 2)

Calibration produces the OCR pipeline; the *formation classifier* additionally
needs labeled training frames. M5c tried to have the coding agent bulk-label
matchup-clip pre-snap frames into the canonical-8 offensive formations. The
empirical result drew a clear, reusable line:

**What the agent does reliably (high accuracy):**
- **SKIP screening.** The agent confidently rejects non-trainable frames —
  coach close-ups, crowd/sideline cuts, kickoffs/punts, replay graphics, and
  mid-play piles/ball-carrier close-ups. These are visually unambiguous.

**What the agent cannot do (from these frames):**
- **Resolve the canonical-8 formation.** Madden's gameplay camera is elevated,
  ball-following, and zoomed — not an all-22 formation view. In a single static
  frame the agent cannot recover **QB depth** (shotgun vs pistol vs
  under-center) or **WR-count-per-side** (trips vs bunch vs doubles vs empty),
  which are exactly the distinctions the taxonomy is built on. Measured
  confident yield was ~0–1 of 12 sampled frames; precise-class accuracy fell
  below even the 85% escalation line. Cropping to the LOS and upscaling did not
  recover the missing detail.

This is a **camera-angle limitation, not a tooling failure**, and every sports
sim with a similar broadcast/ball-following camera (CFB 26, NBA 2K26, EA FC 26,
MLB 26) will hit it. Do not assume an agent can label fine on-field geometry
from gameplay frames; budget for the division of labor below.

**The reusable division of labor** (full protocol in
[training-data-labeling-protocol.md](training-data-labeling-protocol.md)):

1. **Agent pre-screens skips** — high-accuracy rejection of non-trainable frames.
2. **A tightened selector produces a clean pool** — require the players *locked*
   (two consecutive near-zero-motion samples, not a single mid-play lull),
   strong field-green dominance, a live scorebug, and an OCR drop of
   kickoff/punt panels. This is the v2 `sample_pre_snap_candidates.py`.
3. **A human labels the canonical classes** — with frame-scrubbing for snap
   context and domain knowledge, which the camera angle still demands.

The escalation discipline that surfaced this — *attempt, calibrate on a small
sample, and stop before bulk-producing low-confidence labels* — is itself the
reusable rule. Bad ground truth poisons the classifier worse than fewer labels.

## Next titles' calibration order

Per the integration spec, the calibration order matches the adapter rollout:

1. Madden 26 (Phase 0 — done, 2026-05-07)
2. CFB 26 (Phase 2 — same EA Sports engine, expect ~50% bbox reuse)
3. NBA 2K26
4. EA FC 26
5. MLB 26
6. Warzone / Fortnite / UFC 5 / Undisputed / PGA 2K25 / Video Poker — each separate

Each new title's M-x.5 milestone reads this doc, copies the helper scripts to `scripts/hud_calibration/<title>/`, and produces its own `hud_regions.json` + validation report.

## Forge rule alignment

Per [FORGE_ARCHITECTURE_PATTERN.md](../../FORGE_ARCHITECTURE_PATTERN.md):

- **Rule 5** (adapters added without core changes): calibration changes only `services/visionaudioforge/app/adapters/<title>/hud_regions.json`. The dispatcher, integrity gate, and event envelope contract do not change.
- **Rule 4** (events are structured and canonical): OCR readings flow into the same `EventEnvelope` shape; consumers don't see calibration details, they see typed payload fields.
- **Rule 1** (multi-dimensional from day one): the calibration is per-title; adding a new title's calibration does not touch other titles' calibrations.
