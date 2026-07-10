# Digit-OCR Pass — Style-Aware Reader: Build + Held-Out Result

Build and evaluation of the standalone per-field patch-NCC digit reader against the
target-style capture set ([digit-ocr-target-style-capture.md](digit-ocr-target-style-capture.md),
data-unblock per [ADR 0020](../adr/0020-digit-ocr-is-data-bound-defer-until-target-style-capture.md)).
Fixes the ADR-0019 broadcast-bar `1↔7` symptom on the game-clock-seconds field.
**Standalone — nothing wired into `ocr_pipeline`.** Code: `digit_reader.py` (module),
`digit_reader_eval.py` (harness), `digit_templates/` (frozen templates + labels + preview).

## Per-symptom status

### CLOCK-SECONDS `1↔7` — **SOLVED** (on a modest but real held-out sample)

Method: **per-field patch-NCC, same-style templates** — segment the field, tight-crop
each glyph to its largest connected component, normalise to 40×56, zero-mean-unit-norm,
match against **per-digit mean templates**, abstain below frozen thresholds.

Held-out result (disjoint by *view* — whole clock-readings held out, so eval frames are
never near-duplicates of template frames):

| Metric | Result |
|---|---|
| **`1↔7` confusions** | **0** — true-1→7: `0/31`, true-7→1: `0/10` |
| **held-out N / M** | **N = 10 seven-slots (5 views)**, **M = 31 one-slots (15 views)** |
| **genuine separation** | held-out `7`s: NCC **1.00** vs 7-template, **0.16** vs 1-template (not abstain-dodging) |
| **per-digit 0–9** | **228 / 228 correct, 0 wrong, 0 abstain** |
| **reject set** | **45 / 45 abstain** (dark/transition + corrupt-static; 0 leaks) |
| **guardrail vs EasyOCR** | reader **16/16** exact vs EasyOCR **4/16** (EasyOCR: `39→"30"`, `13→"72"`, `07→"677"`, `08→"683"` …) |

**N is stated deliberately: this is proven on a MODEST held-out sample (10 seven-slots /
5 views), not on N=1.** EasyOCR gets 4/16 (it reads non-`1`/`7` clock values fine; it
fails specifically where the symptom lives). Frozen thresholds: **τ = 0.55, δ = 0.02**
(chosen never-fabricate-first on the validation split — minimise wrong reads, then reject
leaks, then coverage; validation was 234/234, 0 wrong).

> **Labeling note:** the capture doc's `:07 :17 :27 :47 :57` (17 `:X7` views) is
> **correct** and stands. During this build an intermediate coarse frame-grouping
> (corr>0.88) briefly mis-collapsed the `7`s to "only `:57`" by merging adjacent clock
> values and mislabeling `:X7` frames as `:X9`. That intermediate claim was wrong and was
> caught because the reader's apparent "errors" were actually correct reads; tight
> grouping (corr>0.965) + a monotonic-countdown check (0 anomalies over 173 runs) restored
> the true 17 `:X7` views, which is what makes a real disjoint held-out `7` sample possible.

### KEY DESIGN FINDING — gcsec and distance are **DIFFERENT STYLES** → two readers

Game-clock-seconds (~21px tall, 2–3px stroke) and single-digit distance (~34px, ~5px
stroke) render at **different scale and stroke weight**; a template built on one field
does not transfer to the other at native scale (cross-field NCC ~0.28–0.42). **Two
per-field template sets are required — a single shared reader must not be re-attempted.**
Same failure mode as the original play-clock cross-style mismatch (ADR 0020): style, not
technique, is the constraint.

### DISTANCE `1↔7` — reader **BUILT**, verdict **PENDING**

Templates built (glyphs/digit `{1:2, 2:25, 3:29, 5:20, 6:26, 7:4}`) and segmentation
confirmed on the corrected distance zone **`[1693,1013]`** (refines the capture doc's
~x=1686; x=1693 excludes the `&` ampersand — the `&` ends ~x=1690, the digit sits
~1695–1720). **Cannot be honestly verified yet:** distance `1` and `7` are **one
situation each (~one glyph view)**, so a held-out frame would be a near-duplicate of a
template — testing on training data. **No LOOCV number is reported on N=1.** Needs a
**second independent live `& 1` and `& 7`** from different field positions before a real
eval. Thicken opportunistically in normal play.

### SCORES — still **BLOCKED**

Center-nameplate score glyphs are a third style (bolder, dark-on-light), with no captured
data. Remains the Phase-2 scoring-campaign prerequisite (ADR 0020 / the segmentation spike).

## NOT YET INTEGRATED

The reader is **standalone and proven on saved frames only.** Wiring into `ocr_pipeline`
(field routing, cadence, cache, `state_assembler` null-degrade) and **re-verification on
the live PS5 feed** (not just saved crops) is a separate session. Live lighting/HUD
variance across games is unproven; the modest per-digit counts for `6/7/8/9` (10–14 each)
are 100% but not hundreds-scale.

## Artifacts (committed; 524 raw frames stay outside the repo per convention)

- `digit_reader.py` — module: `FieldSpec`, `GCSEC`/`DIST` zones, segmentation, `DigitReader`.
- `digit_reader_eval.py` — reproduces the table above (`python -m app.adapters.madden26.digit_reader_eval`; needs the external frames).
- `digit_templates/gcsec_templates.npz`, `dist_templates.npz` — frozen mean templates + thresholds.
- `digit_templates/gcsec_labels.json` — per-frame clock-seconds GT (corrected labels).
- `digit_templates/templates_preview.png` — mean glyph per digit, both fields.
