# ADR 0013 — HUD Calibration Is Recurring Maintenance Driven by External Game Updates

- **Status:** Accepted
- **Date:** 2026-06-29
- **Reference:** [CLAUDE.md](../../CLAUDE.md) — project development context. Aligns with the Forge "adapters extended without core changes" principle (Rule 5): re-calibration touches only a title adapter's `hud_regions.json` + that adapter's OCR pipeline, never core. (The canonical Forge-rules doc, `FORGE_ARCHITECTURE_PATTERN.md`, is referenced across the repo but not yet committed — tracked as separate architectural debt; see Followups.)
- **Supersedes calibration artifact:** `services/visionaudioforge/app/adapters/madden26/hud_regions.json` v2.0.0 → v2.1.0.
- **Related:** [HUD calibration methodology](../integrations/visionaudioforge/madden26-hud-calibration-methodology.md) §"HUD drift between calibrations", [local capture protocol](../integrations/visionaudioforge/madden26-local-capture-protocol.md), [M5c plan](../phase-completions/0-vaf-m5c-plan.md) sub-task 1b.

## Context

M4.5 calibrated Madden 26's `hud_regions.json` (v2.0.0) against `agents/capture/fixtures/real/madden26.mp4`, which renders a **left-anchored full-width broadcast scorebar**. The implicit assumption — visible in the methodology doc's framing of calibration as "a one-day deterministic exercise per title" — was that calibration is a **one-time setup** per title.

That assumption broke in M5c. The local capture batch (2026-06-25–27, same game, same PS5, same 1080p30 H.264 pipeline) renders a **compact center-clustered scorebug** instead. Whether a Madden title update changed the default scorebug between May and June or it is a Play-Now-CPU-vs-CPU presentation difference is a **known unknown** (non-blocking). Either way the effect is the same: every v2.0.0 bbox missed the new layout (scoreboard cluster shifted +213…+304 px right; down/distance collapsed −449…−854 px left into a centered sub-row), yielding **0/10 readable OCR elements** on captures that were otherwise pristine (1920×1080 / 30 fps / H.264, 20/20 on container checks).

This is not a capture defect and not a one-off. Title publishers (EA, 2K, etc.) change HUDs in seasonal patches, presentation defaults, and UI refreshes on their own cadence. Any adapter that reads an on-screen HUD is exposed to this for the life of the title.

## Decision

**Treat HUD calibration as recurring maintenance, not one-time setup.**

1. **Drift is expected and detectable.** `scripts/hud_calibration/verify_capture.py` is the standing detector: a drop/straddle in the calibrated band's `central_std` plus 0 valid OCR reads of stable fields (team abbreviations) on visually-fine footage means the HUD moved. A failing matchup clip there means "re-calibrate", not "re-capture".

2. **Re-calibration is the bounded workflow in the methodology doc** (Steps 1–6 against the new footage; re-crop don't re-translate; mismatch-printing validator so wrong ground-truth is distinguishable from real OCR misses). Budget ~0.5–1.0 day per drift event.

3. **Versioning is explicit.** Bump `hud_regions.json` `schema_version`, record a `supersedes` note in the `calibration` block, and document element drift inline.

4. **Replace + re-baseline** when a new layout becomes canonical (the M5c choice for Madden): the new calibration replaces the old; the old reference clip is **retired as the OCR source but kept on disk** as historical reference; any downstream baseline pinned to the old clip migrates to a new-layout clip with the swap documented explicitly — never silently re-pointed.

5. **Font/preprocessing fixes stay in the adapter** (Forge Rule 5). v2.1.0 added ordinal aliases (`ZND`→2, `ATR`→4) and a score glyph-normalizer (`_parse_score`) to `ocr_pipeline.py`; the dispatcher, event envelope, and integrity gate did not change.

6. **Known-weak elements are documented honestly, not hidden.** v2.1.0 scores fall below the 80% bar (large italic numerals defeat EasyOCR on 2-digit values); accepted as a v0.1 known-weak element with a tracked follow-up, exactly as field_position was the weak element under v2.0.0. No silent compression of the acceptance bar.

## Consequences

- The methodology doc gains a permanent "HUD drift between calibrations" section; future title adapters inherit the recurring-maintenance framing from day one.
- Every adapter reading a HUD carries an ongoing maintenance liability. Capture batches should run `verify_capture.py` as a gate; a drift hit opens a re-calibration sub-task with its own commit, not a silent in-place patch.
- The M4.5 OCR baseline (the 7 hand-labeled `madden26.mp4` play-state frames behind `validate_ocr.py`) is no longer the canonical Madden OCR reference. Sub-tasks 6/6.5 re-establish the temporal-smoothing regression baseline on a v2.1.0-layout matchup clip (see the M5c plan's fixture-transition note). `madden26.mp4` + `m45_ocr_validation.json` remain as historical record of v2.0.0.
- Scores being a documented v0.1 known-weak element means any future feature that consumes live score must first harden score OCR (digit segmentation / template matching) — captured as a follow-up, not assumed working.

## Followups

- **Score-OCR hardening** when a feature consumes live score: per-digit segmentation or template-matching the ~10 stylized scorebug glyphs. Not on the M5c critical path (formation training reads on-field layout, not the scorebug).
- **Canonical Forge-rules doc debt:** `FORGE_ARCHITECTURE_PATTERN.md` is referenced by this ADR's siblings (0001, 0005–0012), the methodology doc, and the capture protocol, but does not exist in the tree (a draft was generated in a prior session but never committed). Create `docs/FORGE_ARCHITECTURE_PATTERN.md` and resolve the dangling references portfolio-wide in its own commit.
- **Drift-cadence question for Phase 2:** once CFB 26 / NBA 2K26 adapters land, decide whether to add a scheduled "re-verify calibration on each capture batch" step to the capture protocol rather than relying on a human noticing OCR garbage.
