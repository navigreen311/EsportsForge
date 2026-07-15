# Coverage hardening — by-game validation results (2026-07-14)

Ran the capture campaign in `docs/coverage-hardening-capture-protocol.md`: 3 new games,
the 10 coverages each, coach-cam play-art. Bottom line: **the coverage reader generalizes
by-game — held-out macro-F1 = 0.92, clearing the ADR-0010 gate (≥ 0.85).** Two limitations
were characterized along the way (Cover 6/9 mirror; the fixed-bbox SNAPSHOT HUD).

## ✅ Coverage by-game — GATE CLEARED

`agents/capture/eval_coverage_by_game.py --games cc,g5,g6,g7` (clip = mode-vote of its
frame reads, the one-per-play unit the adapter emits):

| Game | Matchup | Clip accuracy |
|---|---|---|
| `cc` | (tuning session, in-sample) | 10/10 |
| `g5` | Jaguars / Chiefs | 8/10 |
| `g6` | Chiefs / Ravens | 10/10 |
| `g7` | Colts / Rams | 10/10 |

- **Held-out (g5+g6+g7): 28/30 = 0.93 accuracy, macro-F1 = 0.92.**
- Per-coverage held-out: all 3/3 except Cover 6 (2/3) and Cover 9 (2/3).
- Confusion: `Cover 6 → Cover 3 ×1`, `Cover 9 → Cover 6 ×1` (both on g5 only).

The honesty caveat is resolved **in favor of generalization**: across three distinct
stadiums/matchups the reader holds up, with a single characterized weak spot. **Phase 1c's
coverage prerequisite is met.**

## Limitation A — Cover 6/9 is a mirror/orientation limit (not OCR-fixable)

Cover 6 and Cover 9 are **mirror** coverages, distinguished only by which side the
QUARTER-flat is on. The pre-snap coach-cam's **L/R orientation flips with drive direction**
— g5 was mirrored relative to `cc`/g6/g7, so its 6/9 read as each other's mirror. An
edge-upscale pass (re-OCR the L/R sidelines at higher zoom) *does* surface the small
far-edge QUARTER/SOFT-SQUAT labels, but (1) it still gets the **side wrong** on flipped
captures (measured: g5 read 6↔9 swapped), because the ambiguity is geometric not textual,
and (2) it costs **~3× the OCR budget** (~3400 ms vs the 1500 ms tier). So it was **not
shipped**. Kept: the cheap **fuzzy-QUARTER** misread fix (`coverage_classifier._TOKEN_FIX`:
`ZARTER`/`JARTER`/`ARTER`→`QUARTER`) which recovers the misspelled far-edge labels for free.
The marginal 6/9 confusion is accepted — 0.92 clears the gate. A real fix needs field-
orientation normalization (e.g. from the yard-line numbers), a separate effort.

## Limitation B — the fixed-bbox SNAPSHOT HUD doesn't generalize across matchups

Discovered while trying to confirm 2-digit scores on a 4th game (Broncos/Raiders, `score_
g8_10-3`, GT DEN 10 – LV 3): the whole gameplay HUD read `None` there. Cause: **the PS5
broadcast bar is laid out DYNAMICALLY by team-abbreviation width** — `DEN` (3 chars) shifts
the score/clock cluster right vs `KC` (2 chars) — so the bboxes in `hud_regions.json`
(calibrated on `game_hud_1`, KC/LV) **misalign on other matchups**. This affects scores AND
clock/down/quarter.

**Score-reader rework outcome (EasyOCR + dynamic bbox): NOT an improvement — kept #132.**
- The italic score numeral defeats **both** engines: EasyOCR misreads it (`10`→`70`,
  `6`→`0`) and patch-NCC misreads across matchups. Measured: switching scores to EasyOCR
  **regresses** the one working matchup — `game_hud_1` KC 0 / LV 6 → read `(0,0)`.
- So the patch-NCC `_read_score` (#132) stays: it reads scores where its calibration aligns
  (KC/LV) and **abstains** elsewhere (abstain-over-guess — no garbage emitted, DEN/LV → None).
- A robust cross-matchup score reader needs a **dedicated italic-score-digit model**
  (data-gated, like the play-clock CNN finding) **plus dynamic layout** (anchor elements to
  detected landmarks). Larger effort, low priority for an informational field.

**Broader note:** the live-gameplay SNAPSHOT HUD (scores/clock/down/quarter) is currently
matchup-calibrated (KC/LV) and won't generalize to other matchups until the bar layout is
made dynamic. The COVERAGE reader is unaffected (it reads on-field play-art, not the bar) —
which is why it generalized cleanly. Dynamic HUD layout is the tracked follow-up.
