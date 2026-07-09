# Digit-OCR Pass — Reader Build + Eval (white-style, patch-NCC)

Build+eval of the white-style digit reader banked from **[ADR 0017](../adr/0017-live-feed-hud-recal-and-glyph-ocr-limit.md)**
(fix the broadcast-bar `1↔7`: clock-seconds + single-digit distance). Standalone
work on `ai-feature/digit-ocr`; **nothing wired into `ocr_pipeline`, nothing
production-ready.** Scores are out of scope (Phase-2 scoring campaign, per the spike).

## Method PROVEN (same-style)
Patch-NCC (extract digit patch → zero-mean unit-norm → max NCC over per-digit
exemplars → abstain below a frozen margin) reads these glyphs **excellently when the
templates are the same style as the field**:
- game-clock `0` → game-clock `0` template = **NCC 0.95–1.00**.
- On the play clock it **massively outperforms EasyOCR**: NCC **6/8 correct + 2
  abstain + 0 WRONG** vs EasyOCR **0/8** (EasyOCR reads single garbage digits or empty).
- **Abstain-over-guess held: 12/12 read digits correct, zero wrong.**
- **Frozen thresholds `τ_abstain=0.60`, `δ_margin=0.01`** (chosen on a validation
  split, **never retuned** — including after the zone fix).

## THE BLOCKER — cross-style template mismatch (the headline finding)
The **play clock is a DIFFERENT glyph style** (small, dark-on-white-box, inverted)
from the **game-clock-seconds and distance fields** (larger, white-on-dark).
**Templates do NOT transfer:**

| Match | NCC |
|---|---|
| game-clock `0` → game-clock `0` (same style) | **0.95–1.00** |
| game-clock `0` → play-clock `0` (cross style) | **0.15** |
| distance `3` → play-clock templates | 0.38 → misclassifies as `2` |

The play clock is the **only all-0-9 source in the campaign**, and it is the **WRONG
STYLE** for the ADR-target fields. **This invalidates the plan to seed the target-field
templates from the play-clock library.** The frozen `τ=0.60` correctly *rejects* these
bad cross-style matches (fails safe, never emits a wrong value). `τ` was **not**
loosened — the cross-style predictions are *wrong* (`3`→`2`), not low-confidence, so
loosening would emit wrong digits (never-fabricate).

## Coverage gap in the target (white-on-dark) style
- Game-clock seconds values seen: `10,09,04,03,02,01,00` → digits **{0,1,2,3,4,9}**
  (**missing 6,7,8**).
- Distance values seen: `3`, `5` → **{3,5}** (**no `1`, no `7`**).
- A complete same-style library **cannot** be built from current data.

## Therefore — precise scope of the `1↔7` result
**The `1↔7` result (0 confusions) is PLAY-CLOCK-PROXY ONLY.** Because the game clock
has no `7` and distance has no `1` or `7`, **the `1↔7` fix — the entire purpose of this
pass — CANNOT be verified in the ADR-target styles with current data.** "0 confusions"
is **not** the symptom being fixed; it is glyph-level evidence in a proxy style, on a
thin sample (1 held-out `7`).

## Zones (real, reusable work)
Calibrated by rendering the box onto raw frames and inspecting extraction (the
`hud_regions` method), verified to bound the glyphs and exclude colon/`&`/chrome:
- **`gcsec = [1383, 1013, 68, 40]`** (game-clock seconds)
- **`dist  = [1700, 1013, 54, 40]`** (single-digit distance)

## Guardrail vs EasyOCR (same frames)
- Play clock: EasyOCR **0/8** vs NCC 6/8 + 2 abstain, 0 wrong.
- Distance: EasyOCR reads `"3"` for **both** `4th&3` (right) and `3rd&5` (**wrong** —
  `3` for a `5`, a silent misread); NCC abstains both. Neither reads distance
  correctly on current data.

## Open issues
- **Reject leak:** neg/4 (delay-of-game, blanked box) → reads `"10"`. Reject set is
  **14/15**. Red-`:00` detection was added but **does not close it** — those frames are
  **not red** (R≈G≈B≈125). A live never-fabricate violation on 1 frame, unresolved.

## What the next capture MUST get (target styles only — the play clock does NOT help)
- Game-clock seconds through **6, 7, 8** (a longer running-clock run gets these free).
- Single-digit distances — especially **`1` and `7`** — plus `2,4,6,8,9`.
- The real **`4th & 1`** (the ADR-0017 failure case) — still uncaptured.

## Alternative on the table (not chosen)
A small **CNN with stroke-width / scale augmentation** could span styles where NCC
cannot. Recorded as a live option if same-style target capture proves impractical.

## Artifacts
Working reader + eval harness preserved (not production) at
`C:\Users\ivann\madden-recal-refs\digit-campaign\reader-wip\` (`reader_eval.py`,
`patch_ncc_core.py`). Not transcribed to worktree modules; not wired in; no commit of
scratchpad code.
