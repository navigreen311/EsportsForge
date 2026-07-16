# Scope — Offense/Defense gate for COVERAGE_LOCKED

- **Date:** 2026-07-16
- **Status:** SCOPED (not built). Surfaced during the live solo run + a controlled accuracy test.
- **Related:** ADR 0017 (COVERAGE_LOCKED contract), `coverage_classifier.py`, `state_assembler.py`,
  `context_detector.py`, `defensive_playcall.py`. Findings: coverage-on-offense false-fire; the
  (retracted) Cover-1-misread.

## Problem

`COVERAGE_LOCKED` **false-fires while the player is on offense.** The coverage classifier reads the
pre-snap **coach-cam play-art**; on defense that's the defensive zone-assignment art (the real
fingerprint), but on offense the coach-cam shows **offensive route-art**, which also carries
label-like text. The classifier OCRs those tokens and maps them to a (garbage) coverage, emitting a
spurious `COVERAGE_LOCKED` (observed live: Cover 0 / Cover 2 during offensive series).

**Why it matters (the real damage):** the spurious reads **contaminate the live coverage stream**, and
ArsenalAI's trigger fires on whichever coverage last emitted — so it recommended the wrong weapon
against the wrong (nonexistent) coverage. In the live demo this looked like a "Cover 1 → Cover 0
misread," but a controlled tight-timing accuracy test scored the classifier **6/6 across the full set
(Cover 0/1/2/3/4/6, all stable)**. So the detector is sound; **the defect is the missing gate**, not
the classifier.

## Root cause (from the code)

- `state_assembler._coverage_events` (state_assembler.py:81–113) emits on *any* smoothed non-null
  `coverage.coverage` — there is **no side-of-ball check**.
- `possession` in every payload is a hardcoded **Phase-0 placeholder `"home"`** (state_assembler.py:311)
  — it is NOT detected, so it cannot gate anything (this is also why `possession` read "home" on both
  offense and defense in the live test).
- `context_detector.py` distinguishes **PLAY_CALL vs live gameplay** only — not offense vs defense.
- `coverage_classifier.py` is a pure classifier over OCR'd zone-label tokens; "the coach-cam OCR pass
  and view detection live in the adapter/reader" — i.e. **the adapter decides when to run it**, and
  currently runs it on the coach-cam regardless of side.

## What the pipeline already knows (the lever)

Per play, exactly one play-call path fires:
- **On offense** → `formation_detector` locks an `offensive_formation` off the offensive play-call
  overlay (state_assembler.py:194–227).
- **On defense** → `defensive_playcall.py` reads the defensive play-call card; its own docstring notes
  it "reads the coverage the USER calls (on defense) ... cannot read while on offense." So a
  successful defensive-playcall read is *itself* a defense signal.

Both happen in the **same pre-snap `play_epoch`** as the coach-cam coverage read, so side-of-ball is
knowable at emit time from state already tracked per epoch (`st["_cov_epoch"]`, `_last_locked_*`).

## Options

**A. Side-of-ball state gate (RECOMMENDED, minimal).**
Track a per-epoch `side_of_ball` in adapter state: set `offense` when an `offensive_formation` locks
this epoch; `defense` when `defensive_playcall`/front reads this epoch. In `_coverage_events`, suppress
emission when `side == offense`. Minimal viable version: **if an `offensive_formation` locked in the
current `play_epoch`, return [] from `_coverage_events`** (you're on offense → any coach-cam coverage
read is a false positive). Reuses existing signals + epoch state; no new CV.
- *Risk:* low. *Gap:* misses the case where offense's play-call wasn't read that play (no formation
  lock) yet the coach-cam still false-fires — caught by Option B.

**B. Defensive-art token gate in the classifier (hardening / defense-in-depth).**
Require the coach-cam token set to carry the **defensive zone-label signature** (≥1 of `DEEP ZONE`,
`FLAT`, `HOOK`, `QUARTER`, `CURL`…) and reject when the tokens look like **offensive route names**
(`SLANT`, `GO`, `POST`, `CORNER`, `DRAG`, `WHEEL`…). Self-contained in `coverage_classifier` /
the coach-cam reader; return `None` (no read) on non-defensive art.
- *Risk:* medium — route/zone vocab overlap needs tuning against captured offensive coach-cam art
  (we don't yet have labeled offensive-art fixtures; capture a handful first).

**C. Real possession/side detector (proper long-term fix, larger).**
Replace the `possession` placeholder with an actual HUD read of the possession indicator (ball icon /
team highlight). Gives a true side-of-ball signal that serves coverage gating **and** every other
payload field. Highest value, but it's a new HUD OCR/CV task with its own calibration.

## Recommendation

Ship **A (minimal: suppress coverage when an offensive_formation locked this epoch)** first — it's a
few lines, reuses tracked state, and kills the common false-fire we saw live. Add **B** as hardening
once we've captured offensive-coach-cam fixtures to tune the vocab. Treat **C** as the real fix when
`possession` is built out (it's also needed to un-placeholder the SNAPSHOT `possession` field).

Gate the change behind the existing config so it's revertible, and keep it strictly additive (only
*suppresses* emission — never fabricates a coverage).

## Test plan

- **Regression (no over-suppression):** the live tight-timing harness — replay/live the 6 defensive
  coverages, confirm all 6 still emit correctly (the 6/6 must hold).
- **False-fire suppression:** run an **offensive** series and confirm `COVERAGE_LOCKED` no longer
  emits (0 offense false-fires vs the several we logged tonight).
- **Downstream:** re-run the Arsenal browser demo on defense — the "Secret Weapon Moment" card should
  now track the *actual* called coverage, not a contaminated one.
- Unit: `coverage_classifier` rejects offensive-route token sets (Option B), once fixtures exist.

## Effort / sequencing

- **A:** ~½ session (code + the two live checks). Low risk.
- **B:** ~1 session incl. capturing/labeling offensive-coach-cam fixtures.
- **C:** multi-session (new HUD detector + calibration); do when `possession` is prioritized.

## Also-found, adjacent (log while here)

- `/arsenal/trigger` caches results for 90 s keyed by **user+session+title, NOT coverage**
  (arsenal_ai.py:138) — a coverage change within 90 s returns the stale rec. Independent of the gate
  but compounds the wrong-rec symptom.
- The classifier emits **`"Cover 4 (Quarters)"`** (not bare `"Cover 4"`) — fine for the LLM-based
  Arsenal trigger, but any exact-string matching on coverage downstream should normalize the label.
