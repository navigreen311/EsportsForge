# Play-Clock Reader — Findings & Honest State

- **Status:** **RESOLVED via a small CNN** (patch-NCC ruled out first — kept below as the
  honest record). The play-clock (dark-on-white `:00`–`:40`, the "third polarity") does
  **not** yield to the patch-NCC technique (best held-out **40%**), but a small 2-head CNN
  on the whole-value patch reads it **72% exact / 82% within-±1** held-out (2x NCC), and —
  the high-value use — **94%** on the snap-detector reset-vs-resume decision. Shipped as
  `models/play_clock_v0_1.onnx` (ONNX/onnxruntime), wired to the `play_clock` payload
  (best-effort, confidence-gated) and the snap-detector `last_snap_pause` FP annotation.
  See the **CNN resolution** section at the bottom.
- **Date:** 2026-07-11 (patch-NCC findings); CNN resolution 2026-07-11
- **Data:** 8 live snap-capture clips (the ones from the snap-detector work) are full of
  play-clock countdowns 40→0 in varied field/lighting. A subagent read a 48-crop seed
  (34 clean values 14–40); expanding each anchor to its ±10-frame same-value window gave
  ~400–650 labelled patches.

## What was tried (all executed, held-out by clip)

| Approach | Held-out accuracy | Why it fails |
|---|---|---|
| Whole-value NCC (raw grayscale, 41 value templates) | **22%** | The white box + colon + chrome bar dominate the 72×32 patch — NCC ≈ 0.98 to *every* value template regardless of the digits. The digits are too small a fraction of the patch to discriminate. |
| Whole-value NCC (Otsu-binarized) | **22%** | Same — the binarized *box outline* is a large constant shape that dominates; the digits still don't move the NCC. |
| Per-digit NCC (segment into tens/ones, 10 templates) | **40%** | The 10-template idea is sound and the seed covers 0–9, but the **segmentation doesn't generalize across clips**: the dark-on-white digits, a thin `1`, variable digit widths, the colon, and the box/chrome make the isolated glyphs inconsistent, so templates built on some clips mis-match others. |

Segmentation was the crux and consumed most of the effort: connected-components merge the
two digits; equal-column split miscuts (variable widths); projection-split + morphology-open
erased the thin `1`; a gentler split still gave inconsistent glyphs. This is the same wall
that deferred the reader originally — now confirmed with real data and real numbers, not a
data-thinness excuse (the data is plentiful).

## Why the other fields worked but this one doesn't

The clock/distance/quarter/down are **white-on-dark** with clean separation — the proven
invert-free `field_present` + largest-CC crop isolates each glyph cleanly. The play-clock is
**dark-on-white inside a bright box with a colon and a chrome bar**; inverting to reuse the
pipeline turns the box/chrome into competing bright foreground, and the digits don't isolate
consistently. It is a genuinely harder segmentation problem, not a tuning gap.

## CNN resolution (built + shipped)

**A small 2-head CNN on the whole-value patch** — the recommended path, executed. Heads
classify tens (0–4) and ones (0–9) from the tight white-box crop `[1448,1022,88,38]` (the
`hud_regions` `play_clock` zone clips the digit bottoms; the box extends below it). The CNN
*learns* to attend to the digits and ignore the constant box — the exact failure mode that
sinks NCC.

- **Data.** The 8 live snap clips. Dense labels by **countdown propagation**: 8 subagents
  read each clip's 1-fps contact sheet, then monotonicity-clean (drop `?`/red, drop isolated
  misreads) → 575 white-clock labelled seconds → ~5.2k mid-second training patches. Trainer +
  labels committed at `services/visionaudioforge/tools/play_clock/`.
- **Accuracy (held-out by clip).** exact **72%**, within-±1 **82%** (2x the 40% NCC baseline);
  train-fit is 75% (label-noise/font-ambiguity bias ceiling, not overfit). More clips would
  raise it — the current ceiling is 8-clip data, not the method.
- **Reset-vs-resume 94%.** The high-value use needs only the DIRECTION of change (reset toward
  :40 vs resume counting down); the reset gap dwarfs per-read noise, so held-out this decision
  is 94% even though the exact read is 72%.

**Wiring.** `play_clock_reader.PlayClockReader` (ONNX via onnxruntime; graceful-None if the
model/onnxruntime is absent, same contract as the patch-NCC template readers). Payload:
`OCRPipeline._read_play_clock` on an `every_n:6` cadence, confidence-gated (τ=0.55), smoothed
(`play_clock` window=3). Snap FP fix: the cached value feeds `SnapDetector.update(pc_value=…)`,
which sets `last_snap_pause=True` when a POST_SNAP freeze's clock RESUMES down — a
non-destructive annotation for the downstream confidence gate (the snap already fired). See
`snap-detector-m5b.md`.
