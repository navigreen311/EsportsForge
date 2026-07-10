# ADR 0020 — The Broadcast-Bar Digit-OCR Limit is DATA-Bound; Defer the Build Until a Target-Style Capture Campaign Exists

- **Status:** Accepted
- **Date:** 2026-07-10
- **Reference:** [ADR 0019](0019-live-feed-hud-recal-and-glyph-ocr-limit.md) (banked the "dedicated digit-OCR pass" followup for scores / clock-seconds `1↔7` / single-digit distance `1↔7`), [ADR 0014](0014-ocr-overlay-over-cnn-for-formation-signals.md) (OCR-over-CNN posture), [ADR 0017 never-fabricate principle](0019-live-feed-hud-recal-and-glyph-ocr-limit.md) (fail-safe / null-degrade — carried in 0019 §Decision 6).
- **Resolves (does not supersede):** the ADR 0019 §Followups item "Dedicated digit-OCR pass for the bar's numerals." 0019 stays `Accepted`; this ADR records *why that pass cannot be built yet* and the one precondition that unblocks it.
- **Scope:** Decision note only. **No code, no capture, no training** in the change that carries this ADR. Title-adapter scope unchanged; `ocr_pipeline` untouched; the three weak fields keep their 0019 null-degrade behavior.

## Context

ADR 0019 banked a dedicated digit-OCR pass to fix three broadcast-bar symptoms with one technique — scores non-detection, clock-seconds `1↔7`, and single-digit distance `1↔7`. Two follow-up sessions on `ai-feature/digit-ocr` executed a data-capture spike and a reader build+eval to attempt that pass. This ADR records the binding conclusion those sessions reached, so the effort is not re-attempted on the same footing.

The reader build (patch-NCC, white-style) validated the *technique* and simultaneously surfaced that the *pass is not buildable with the data we have* — and, critically, that the shortfall is **not** a matter of choosing a better algorithm. The two prior docs are the evidence:
[`digit-ocr-phase1-capture.md`](../phase-completions/digit-ocr-phase1-capture.md) and
[`digit-ocr-reader-build-eval.md`](../phase-completions/digit-ocr-reader-build-eval.md).

## Decision

**The broadcast-bar digit-OCR fix is DATA-bound, not technique-bound. Stop algorithm experiments on the existing data and defer the build until a target-style capture campaign has collected the missing digits — above all a real target-style `1` and `7`.**

### PROVEN — keep (the technique is validated for same-style)

- Patch-NCC (extract glyph → zero-mean unit-norm → max NCC over per-digit exemplars → abstain below a frozen margin) reads these glyphs **excellently when template and field are the same style: NCC 0.95–1.00**.
- On the play clock it **crushes EasyOCR: 6/8 correct + 2 abstain + 0 wrong vs EasyOCR 0/8.**
- **Abstain-over-guess holds: 12/12 read digits correct, zero wrong reads.** Frozen thresholds `τ_abstain=0.60`, `δ_margin=0.01` (set on a validation split, never retuned).
- Conclusion: **the same-style reading technique works.** It is not what is blocking us.

### THE REAL BLOCKER — the target-style DIGITS DON'T EXIST in the captured set

Cross-style template transfer fails (game-clock `0`→play-clock `0` = **0.15**; distance `3`→play-clock templates = 0.38, misreads as `2`). But the deeper finding is that **we cannot fix this with any technique because the target-style examples were never captured.** Real labeled counts:

- **Distance (target style, white-on-dark):** only **{3, 5}** — a single `3` and a single `5`. **ZERO `1` and ZERO `7`.** The `1↔7` pair that is the entire point of this pass **has no target-style examples on the distance field at all — it cannot even be tested there.**
- **Game-clock seconds (target style):** ~**6** crops total, covering **{0,1,2,3,4,9}** and **no target-style `7`** — the seconds run froze at the 2-minute warning, so `05–08` (incl. `07`) were never seen. The single held-out `7` on record (reader-build eval) is a **play-clock proxy `7`, not a target-style seconds `7`.** Missing 5,6,7,8.
- **Play clock (the "complete 0-9 library"):** does span 0-9 **but** (a) only ~**1–4 instances per digit** — 7/8/9 have just **2 exemplars each**; (b) it is the **WRONG style** (small, dark-on-white-box, third polarity) for the two target fields; and (c) **it was never segmented into labeled digit crops** — it is raw full-frame screenshots. There is no dataset, only images.

`N ≈ 1–4` examples per class, most in the wrong style, un-segmented, **trains nothing and cannot evaluate generalization.** No algorithm invents examples that were never captured.

### INVALIDATED PLANS — record so they are NOT resurrected

1. **"Train a CNN on the complete 0-9 play-clock library."** Assumes a labeled dataset that **does not exist** — the play-clock frames were never segmented into digit crops, and even segmented they are ~2–4/class in the wrong style. Also invalid for HOG/kNN or any learner: all are equally data-bound.
2. **"Seed target-field templates from the play-clock library / cross-style transfer."** Cannot be *tested*, let alone shipped: with **one (proxy) held-out `7` and zero target-style `1`s**, cross-style generalization on the `1↔7` symptom is unmeasurable. A pass rate on {0,2,3,4} would prove nothing about the pair that matters.
3. Corollary: **do NOT run another technique experiment on the existing thin data** (no "just try stroke-normalization / HOG / a tiny CNN on what we have"). The bottleneck is upstream of technique.

### WHY PRACTICE MODE DOESN'T RESCUE IT

Practice mode **cannot set down-and-distance.** Target-style `& 1` and `& 7` (and a real `4th & 1`, the ADR-0019 failure case) can therefore only appear when **live gameplay deals those situations** — they are not forceable in a lab. This is why the gap persisted across capture attempts: two `4th & short` tries hit a glitched frame and a delay-of-game blanked box.

### THE ONLY PATH TO A FIX

A **target-style capture campaign** — game-clock-seconds and single-digit distance in the actual white-on-dark HUD style, **especially `1` and `7`, and a real `4th & 1`** — collected from **live play**. The play clock is a dead end for the targets. Until that data exists, **no technique can fix scores / clock-seconds / single-digit distance.** (A running-clock capture that does *not* stop at the 2-minute warning harvests seconds `05–08` incl. `07` cheaply; the `1`/`7` distances still require live game situations.)

## Current production posture (honest, acceptable)

The three weak fields **fail SAFE** under ADR 0019's null-degrade: they are **nulled / abstained, never wrong** (never-fabricate). A wrong `4th & 1`→`& 7` or `:17`→`:11` is not emitted; the field is dropped and SNAPSHOT keeps flowing. **Tier 1 is functional without this fix** — formation + down/distance/quarter + clock-minutes are proven live (0019); only sub-digit precision and scores are held back, safely.

## Consequences

- **The digit-OCR build is deferred**, not cancelled. `ai-feature/digit-ocr` remains held/unmerged; `main` is untouched. No production wiring exists or is added.
- The preserved same-style reader + eval harness (`~/madden-recal-refs/digit-campaign/reader-wip/`) stays as the validated technique to reuse **once target-style data exists** — it is not thrown away.
- No further algorithm experiments are authorized against the current data.

## Notes / followups (the decision is the maintainer's — recorded, not forced)

**Recommendation (maintainer to decide):** defer the build and choose one of —
- **(A) Passive accumulation:** collect target-style digits during normal live play and build the reader once enough `1`/`7`/scores crops accumulate; **or**
- **(B) Accept the limits as permanent-for-now:** the three fields stay null-degraded and Tier 1 ships as-is.

Either way: **do NOT run another technique experiment on the existing thin data.** Revisit this ADR when a target-style set with real `1`s and `7`s exists.
