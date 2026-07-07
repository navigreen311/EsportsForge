# ADR 0018 — Coverage Classifier: the Lever Is Deep-Secondary Region-Crop, Not Temporal Rotation

- **Status:** Accepted
- **Date:** 2026-07-06
- **Reference:** [CLAUDE.md](../../CLAUDE.md) — project development context. Aligns with the Forge "adapters extended without core changes" principle (Rule 5): the coverage classifier and its training/eval pipeline live entirely offline in the Madden adapter's capture agent (`agents/capture/`); core is untouched. (The canonical Forge-rules doc `FORGE_ARCHITECTURE_PATTERN.md` is referenced repo-wide but not yet committed — tracked debt, see ADR 0013 followups.)
- **Revises:** the **"temporal / multi-frame proven necessary"** conclusion recorded in [docs/coverage-classifier-findings.md](../coverage-classifier-findings.md) (Round 4, committed `ce33860`). That inference did **not** survive a direct look at the pixels — see below. Temporal is **deprioritized** for these failures; it survives only as a candidate for the single `cover3_15` two-high case.
- **Establishing case:** Option B ("temporal") kickoff — the pre-registered windowing pass that gated it, then the resolution/crop experiment and a crop-robustness + seed-stability hardening sweep.
- **Related:** [ADR 0010](0010-phase-1c-gated-on-adapter-v0-3.md) (v0.3 gate: coverage macro-F1 ≥ 0.85 on held-out), [ADR 0017](0017-coverage-locked-payload-contract.md) (COVERAGE_LOCKED payload — the downstream consumer, on `feat/v0.3-coverage-contract`), [ADR 0014](0014-ocr-overlay-over-cnn-for-formation-signals.md) (the "resolve the signal at the right representation" precedent).

## Context

The single-frame ResNet18 coverage classifier plateaued at **macro-F1 ~0.79** (0.786 ± 0.043, Round 4, 117 clips). Its residual failure was a directional **Cover 3 → Cover 4** confusion concentrated in four held-out clips (`cover3_07/13/14/15`). The Round-4 finding, reasoning from the confusion matrix alone, inferred the cause was a **two-high disguise that rotates to single-high post-snap** — i.e. a frame at `snap+1–2s` is ambiguous and *"only the temporal safety rotation after the frame separates them"* — and concluded **temporal (multi-frame) input was proven necessary.**

That conclusion was an inference from numbers, never from the footage. Before building a temporal model, we ran a pre-registered **windowing pass**: does the footage actually show a rotation?

## What the pixels showed (the windowing pass)

Zoomed deep-secondary crops across `snap−0.5 … +2.5s` for the 4 failing clips + 2 true-Cover-4 contrasts:

- **3 of the 4 failing clips (`07/13/14`) are stable single-high** — one deep-middle safety, present and unchanged across the whole window. **There is no rotation to observe.** Only `cover3_15` is a genuine two-high look.
- True Cover-4 (`cover4_08/10`) shows **two split deep safeties** → the distinguishing cue is **safety count (1 vs 2)**, and it is **statically present** in the footage.
- That cue lives in a handful of pixels that **downsampling the full frame to the model's 224² input destroys.** The model calls stable single-high Cover 3 "Cover 4" because at 224² it cannot resolve one deep safety from two.

**Therefore temporal is not the mechanism** for the majority of failures — there is nothing temporal to catch on stable single-high clips. The Round-4 premise did not survive contact with the pixels. This is a **resolution / localization** problem, not a time problem.

## Decision — the operative lever is deep-secondary *region-crop*, not global resolution

Two variants isolate *how many pixels* from *where the pixels are*, at the same CV / fine-tune / seed (only the input transform changes; scripts `diag_resolution.py` @ `3a1ca65`, `diag_crop.py` @ `7e4b65b`):

| config | macro-F1 | `cover3_13` (the diagnostic clip) |
|---|---|---|
| 224 full-frame (baseline) | 0.786 ± 0.043 | C4 |
| 320 full-frame | 0.827 ± 0.024 | C4 `[c4:9]` |
| **384 full-frame** (more total pixels) | 0.841 ± 0.028 | **C4 `[c4:10]` — STALLED** |
| **deep-secondary crop → 320** | **~0.86** | **C3 `[c3:8]` — CRACKED** |

More *total* pixels (384) did not fix `cover3_13`; a crop that makes the **deep-secondary band dominate the input** did. **The lever is pixels-on-the-region, not global resolution.**

## Hardened result

`crop→320` ≈ **macro-F1 0.86 mean** (the earlier "0.867" was one draw; cuDNN nondeterminism is ~0.005 run-to-run, so **it is not a precise 0.867**). Pre-registered hardening (`diag_crop_param.py` @ `b8e3fa6`):

- **Crop-robustness:** across 4 reasonable crop windows (tighter / wider / shifted / original), macro-F1 = **0.859–0.895** — no collapse toward 0.82. The lever is **not overfit** to the hand-picked window.
- **Seed-stability:** original crop across seeds 1337/42/7 = **0.862 / 0.866 / 0.865** — mean stays ≥0.85 on every seed. **Not seed-lucky.**
- Per-clip robustness: `cover3_07` fixed in **6/6** configs; `cover3_13` cracked in **5/6**; `cover3_14` in **2/6**; `cover3_15` in **0/6**.

**This clears ADR 0010's bar in the mean** (macro-F1 ≥ 0.85 on held-out). It does **not yet** meet "stable on every fold."

## Open / deferred (each is a fresh effort with its own pre-registered bar)

- **Fold floor is soft.** Per-fold floors dip to **0.81–0.83** for most crops; only the *tighter* window (`0.15,0.10,0.85,0.52`, macro-F1 0.895) held every fold ≥0.85. That tighter crop is a **flagged future lead, deliberately NOT adopted** — chasing it now would be crop-tuning against the same 6 clips that motivated the region, deepening overfit risk.
- **`cover3_13` ↔ `cover3_14` is a genuine trade.** No single fixed crop holds both: the tighter crop recovers `14` but loses `13`; every crop that holds `13` misses `14`. → points to **per-clip / ensemble** handling, not one magic window.
- **`cover3_15` is a parked two-high miss** — never flips under any crop. This is the **one case a temporal model might still address** (a real disguise that rotates), so temporal is retained only as a narrow candidate here, not the general lever.
- **The crop region is still 6-clip-motivated.** Robustness across 4 windows mitigates the overfit concern substantially, but true validation wants **more held-out clips**.

## Consequences

- The banked, reproducible artifact is the **single-frame ~0.79 model** (reference, `ce33860`) plus the **region-crop ~0.86 pipeline** (`diag_crop.py`/`diag_crop_param.py`). Nothing is wired to the adapter; the **v0.3 gate (ADR 0010) stays closed** until ≥0.85 is stable (not just mean-clearing).
- Future coverage work should treat **"resolve the signal at the right representation"** as the first question (echoing ADR 0014's OCR-over-CNN pivot) — here, cropping to where the discriminative pixels live beat both more data (Round 3/4) and more global resolution (384).
- Standing rule retained: only numbers **traceable to an executed run with logged output** count as results.
