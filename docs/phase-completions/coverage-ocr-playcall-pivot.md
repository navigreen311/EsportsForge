# Coverage (and defensive front) via OCR-of-play-call — the pivot

- **Why:** post-snap coverage-from-vision is a research arc — the by-clip tier ladder (T0 0.83
  etc.) did **not** survive by-game validation (near chance across every approach; see
  `coverage-v0.3-modeling-plan.md` "BY-GAME VALIDATION"). Rather than a multi-year vision effort,
  pivot to reading the defensive call off the **play-call screen** — the same OCR-of-overlay move
  that saved the offensive formation classifier (ADR 0014, 100%).
- **Status:** feasibility CONFIRMED on the captured clips; not yet built.

## What the defensive play-call screen exposes (all cleanly readable)

Verified on the capture clips (e.g. the Rams defensive play-call screen). Each play card shows, in
large text, the **entire defensive stack**:

| Signal | On screen | Serves |
|---|---|---|
| **Coverage** (by name) | "Cover 1 Hole", "Tampa 2", "Cover 3", "OLB Fire Man" | **v0.3** `defensive_coverage` |
| **Front / personnel** | "4-3 Over" (+ Nickel / Dime / Dollar / Prevent formation tabs) | **v0.2** `defensive_formation` |
| **Man / zone / blitz** | explicit **MAN / ZONE / BLITZ** badge on each card | **T1** — *directly labelled, no classifier* |

So one OCR pass over the defensive play-call screen yields the coverage, the front, AND man/zone —
the whole stack the vision approach failed to read.

## The hard limit (be honest about scope)

This reads the coverage the **user calls** — it works when the defensive play-call screen is
on-screen (you're on defense, or analysing your own defensive tendencies). It **cannot** read the
**opponent's** coverage while you're on offense (their call is never on your screen). That
opponent-coverage case is the genuine post-snap-vision research arc, and stays deferred. Many
product uses (own-defense analytics, defensive tendency tracking, drill feedback) are covered.

## Approach (mirror `formation_detector.detect_offensive`)

1. **Detect the defensive play-call screen** — extend `is_play_call_screen` / a context check
   (the defensive screen has the formation tabs + 3 coverage cards + MAN/ZONE badges).
2. **OCR the SELECTED card** — the highlighted/committed card carries the called coverage. Read
   its coverage-name text region; also read the formation tab ("4-3 Over") for the front and the
   badge for man/zone. (Selected-card detection = a highlight/box cue, like the offensive
   play-select subtitle.)
3. **Map to canonical vocabulary** — normalise "Cover 1 Hole" → `Cover 1`, "Tampa 2" → `Cover 2`
   (Tampa variant), etc., to the ADR-0017 set (`defensive_coverage` is free-str, so raw + canonical
   both fine, like `offensive_formation`).
4. **Wire** `detect_defensive_front` (v0.2) and `detect_coverage` (v0.3) to read the same screen;
   emit `defensive_formation` + `defensive_coverage` (+ derive man/zone).

## What it needs to build (days-scale, not research)

- **Dedicated defensive-play-call captures** (the coverage clips have incidental play-call frames;
  a clean set like the offensive `madden26_playcall_*` — record the defensive play-call screen per
  coverage/front, labelled by construction). The 4 game-tagged coverage clips already contain
  usable defensive play-call frames to bootstrap.
- **OCR region calibration** for the defensive play-call layout (add regions to `hud_regions.json`
  — coverage-name, formation-tab, badge — validate by rendering the crops back).
- **Selected-card detection** + name→canonical mapping + wiring.

Because it reuses the proven overlay-OCR pipeline end-to-end, once the screens are captured this is
a **days-scale build**. Shares the screen with the **v0.2 defensive front** — one capture + one OCR
pass serves v0.2, v0.3, and man/zone together.

## Reusable from the vision attempt

`agents/capture/player_crop.py` (person-detection → player-relative framing) is field-position
invariant and reusable if the opponent-coverage vision arc is ever revisited. The 4 game-tagged
captures are the honest by-game test set + a seed for either path.
