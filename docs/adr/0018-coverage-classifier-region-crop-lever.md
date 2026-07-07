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

## Addendum (2026-07-06) — recon: data reality + the 4-clip failure taxonomy

A facts-only recon pass (no training) fixed two things the body left open: how expensive more data is, and exactly what the residual gap is made of. Both bear on whether remaining work is a broad fix or fine-grained hardening.

### Data reality
- **120 labeled clips IS the corpus** (cover1=25, cover2=25, cover3=45, cover4=25; 117 after `DROP`). There are **no cheap unlabeled coverage clips** to draw on: of 148 files in the capture folder, 120 are this set and the other 28 are 10 full-game quarter clips (unsegmented) + 18 *offensive-formation* clips (for the ADR 0014 formation detector, not coverage). `fixtures/real/` (42 broadcast clips) is a separate validation set. **Expansion = a deliberate capture campaign at ~3–5 min/clip.**
- **Labels are correct-by-construction, not eyeballed:** the defense is *called* in practice mode, encoded in the filename (`coverN`), and regex-routed to a class folder at extraction. The only manual per-clip step is **snap-timing** (read from a contact sheet). So the "6-clip-motivated" caveat in this ADR is strictly about the **crop-region choice**, **not** label trust.

### The 4-clip failure taxonomy (the whole residual at ~0.86)
Across the 6 hardening configs (4 crops × seeds), **16 of 20 validation clips are stable-correct** on every crop and seed. The remaining gap is exactly four clips, spanning **three distinct failure modes**:
- **`cover3_13` / `cover3_14` — a genuine 2-clip CROP TRADE.** The tighter crop fixes `14` but loses `13`; every other config does the reverse. No other clip shows this. → wants **per-clip / ensemble**, not one magic crop.
- **`cover3_11` — SEED INSTABILITY.** Correct under all four crops @seed1337, but flips to **Cover 2** at seeds 42/7. A distinct mode → wants **seed-robustness**, unrelated to the crop.
- **`cover3_15` — hard TWO-HIGH.** Stable-wrong (Cover 4) across all 6 configs. **~11 two-high clips already sit in TRAIN and the model still misses it → hard-not-under-sampled.** This is the one genuine candidate for the **deferred temporal** approach, or it parks as a known miss. **More coverage data will not crack it.**

### Implication
The model is **~0.86 mean (clears ADR 0010's mean bar)** with a **fully characterized 4-clip residual across three separate failure modes**. Remaining work is **fine-grained hardening** (per-clip/ensemble for 13/14, seed-robustness for 11, temporal-or-park for 15) — **not a broad fix, and not more data.**

## Addendum 2 (2026-07-07) — `cover3_11` parked (data quality), seed-ensemble ruled out

Followed the addendum-1 open item "seed-robustness for 11" to a conclusion. Two locked outcomes:

- **`cover3_11` — DISPOSITION: DATA QUALITY, not model fragility → PARKED.** The frame-level votes are **near-uniform** (5–6 of 9 C3 @seed1337 → **4-4** and **3-3-3** ties @seeds 42/7), so the "flip to Cover 2" is a tiebreak, not a confident misread. Looking at the clip: it is a genuine single-high Cover 3 (correctly labeled) but **human-controlled** (`STRAFE` HUD + movement cone — a person manually steering the deep defender, distorting the clean zone shell) **and a short clamped-overrun clip** (3.3s; extract window compressed to a 0.8s late slice). So it is atypical vs the clean shells the other clips show. **Parked as a known edge case; candidate for re-capture as a clean, non-controlled clip.** Not chased further — forcing one atypical clip risks overfit.
- **SEED-ENSEMBLE — RULED OUT as a production lever.** A 3-seed logit-averaging ensemble (seeds 1337/42/7, ORIG crop, `eval_seed_ensemble.py`) was evaluated as a *production-model candidate*, framed as whole-model seed-robustness, not an 11 rescue. Result: **macro-F1 flat (0.865 ± 0.038 vs 0.866 single-seed), the 16 stable clips unchanged, and `cover3_11` reaches only a hair-thin 5-3 C3** (same margin as seed1337 — not stabilized). **3× cost, no production gain.** The production candidate **remains the single-seed (1337) ORIG-crop model.**
- **Side note:** under the ORIG crop, `cover3_13` is a strong C3 (`[c1:1, c3:9]`) at every seed — its only failure was the *tighter* crop, confirming the 13↔14 trade is **crop-specific**, not general.

### Updated residual
Of the original 4-clip residual: **`cover3_11` and `cover3_15` are now PARKED** (data-quality / hard-two-high — neither is a model bug more work should chase). The **one remaining live item is the `cover3_13`↔`cover3_14` crop trade** (per-clip / ensemble candidate) — noting `cover3_13` is already correct under the ORIG production crop, so the live pain is really just `cover3_14`.
