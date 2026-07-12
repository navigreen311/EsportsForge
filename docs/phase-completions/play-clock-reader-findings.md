# Play-Clock Reader — Findings & Honest State

- **Status:** **Attempted, patch-NCC RULED OUT.** The play-clock (dark-on-white `:00`–`:40`,
  the "third polarity") does **not** yield to the patch-NCC technique that reads the other
  digit fields (clock / distance / quarter / down). Best held-out accuracy **40%** — not
  usable. The reader is **not built**; `play_clock` stays `None` in the payload and the
  snap-detector reset-vs-resume FP fix stays blocked (see `snap-detector-m5b.md`).
- **Date:** 2026-07-11
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

## Recommended next path (not attempted — bigger build, needs sign-off)

**A small CNN classifier on the whole-value patch** (classify 0–40 from the fixed
`[15,12,72,32]` crop). A CNN *learns* to attend to the discriminative digit region and
ignore the constant box — exactly the failure mode that sinks NCC here. The infra exists
(`agents/capture/train_coverage.py` pattern; GPU box available). It needs a denser labelled
set than the 34-value seed — obtainable by **countdown propagation** (value is constant
between ticks, −1 per tick, resets to 40; anchor from the seed) or more subagent reads.

Until then: patch-NCC is banked as ruled out, the seed/labelling scripts are the head start,
and `play_clock` remains `None`.
