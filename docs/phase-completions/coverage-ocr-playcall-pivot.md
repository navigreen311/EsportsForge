# Coverage (and defensive front) via OCR-of-play-call — the pivot

- **Why:** post-snap coverage-from-vision is a research arc — the by-clip tier ladder (T0 0.83
  etc.) did **not** survive by-game validation (near chance across every approach; see
  `coverage-v0.3-modeling-plan.md` "BY-GAME VALIDATION"). Rather than a multi-year vision effort,
  pivot to reading the defensive call off the **play-call screen** — the same OCR-of-overlay move
  that saved the offensive formation classifier (ADR 0014, 100%).
- **Status:** feasibility CONFIRMED **and OCR verified** — EasyOCR read a captured Rams
  defensive play-call screen at high confidence: coverage names `Cover 1 Hole` / `OLB Fire Man` /
  `Tampa 2`, front `4-3 Over`, and badges `MAN` / `BLITZ` / `ZONE`. The **canonical parser is
  built + CI-tested** (`app/adapters/madden26/defensive_playcall.py` +
  `tests/test_defensive_playcall.py`, 4 tests on the real OCR strings) — it maps a card's
  (name, front, badge) → canonical `front` + `coverage` (ADR-0017 vocab) + man/zone. **Remaining
  to ship:** per-card **region OCR** (reading the whole band splits "Cover 1 Hole" into loose
  tokens, so OCR each card's name region separately — needs `hud_regions.json` bboxes), a
  **defensive-play-call-screen detector**, **selected-card** resolution (the browse screen shows
  3 options — determine which the user commits), and **adapter wiring** (`detect_defensive_front`
  / `detect_coverage`). A small set of **dedicated defensive-play-call captures** makes the
  region calibration + selected-card work clean.

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

## v0.3 defensive COVERAGE — CLASSIFIER BUILT (reads the coach-cam play-art)

The committed coverage is **NOT** on the play-call card screen: selecting a card fades all 3
uniformly to the field, and the pre-snap field carries no coverage name (investigated frame-by-frame,
capture `committed_cov_3`). The signal that works is the **pre-snap coach-cam** (play-art ON): Madden
draws every defender's zone assignment as a clean on-field **text label** — a coverage *fingerprint*,
clean deterministic OCR (categorically better than the failed post-snap vision).

**Validated on 10 real captures** (`~/madden-recal-refs/digit-campaign/cov_cc_*`, logged in
`COVERAGE_CONSTELLATIONS.md`): Cover 0/1/2/2-Man/Tampa2/3/3-Slim/4/6/9. The decision tree:

- **`#DEEP ZONE` labels = the deep shell** (0→4), monotonic and exact.
- **Underneath-label density** (labels excluding the deep zones): sparse (≤2) ⇒ **man** (man defenders
  are drawn as LINES, not labels), dense ⇒ **zone**. Man family = N-deep + man-under: Cover 0/1/2-Man.
- **Underneath set + L/R asymmetry** disambiguates same-shell coverages: a QUARTER-flat label on a
  3-deep ⇒ Cover 6 (quarters left) / Cover 9 (quarters right); else Cover 3.
- **Resolution limit** (acceptable): label-identical variants fold to the canonical family — Tampa 2
  == Cover 2 Invert in labels, both → "Cover 2" (differ only by MID READ route depth, geometry not text).
- **BLITZ** = orthogonal red-line pixel signal, carried as a separate flag (a card's name saying
  "...Man" does NOT mean man coverage — trust the labels/density, not the words).

**Built + tested (this PR):** `coverage_classifier.py` (pure decision tree, `tests/test_coverage_classifier.py`
= 7 tests on the 10 real constellations *including* the OCR noise + the far-edge label EasyOCR missed on
Cover 6) + `OCRPipeline.read_coverage` (OCR the play-art band y∈[0.12,0.72] upscaled, group tokens into
2-D labels, classify; self-gates to None off the coach-cam) + `FormationDetector.detect_coverage`.
**End-to-end 10/10** on the captured clips (raw frame → OCR → correct canonical coverage + man/zone).

**Remaining to emit `COVERAGE_LOCKED`:** adapter wiring on the LIVE (pre-snap) path — a cadenced
`detect_coverage` read (EasyOCR band-read is ~costly, so cadence it; read_coverage already self-gates to
None when the coach-cam isn't up) + mode-vote `defensive_coverage` + emit once per pre-snap, mirroring the
v0.2 front emit but on the live path. Scoped as a focused follow-up (hot-path change). Optional refinements:
robuster edge-label OCR (per-label upscale) and man-line detection for the label-less Cover 0.

## v0.2 defensive FRONT — SHIPPED (reads the committed front off the coverage-card screen)

The **defensive front** (`defensive_formation`) is now wired end-to-end. The committed
front + alignment ("3-4 Under", "Nickel Over", "4-4 Split") is printed on the **same
coverage-card subtitle line** the offensive reader uses (`formation_name`/`_2`/`_3`
regions) — but it's a defensive front, a vocabulary **disjoint** from offensive
formations, so `canonical_front()` disambiguates the two on the shared regions. This
mirrors the offensive reader's hard-won lesson: the **committed** front is the one on the
coverage-CARD screen (the formation the user drilled into to pick a coverage), NOT the
formation-picker list highlight (which is only the *hovered/browsed* front — the direct
analog of the offensive formation-select banner that produced the live wrong-lock).

- `OCRPipeline.read_defensive_front` → `DefensiveFrontReading(front, full_name, conf,
  is_defensive_play_call)`; `FormationDetector.detect_defensive_front` maps it to a
  `FormationReading`; the adapter reads it on every `PLAY_CALL` frame (offense XOR defense
  by vocabulary) and the assembler mode-votes it and emits `FORMATION_LOCKED` with
  `defensive_formation` once per screen. Guarded so a defensive front never leaks into
  `offensive_formation`.
- **Validated on the dedicated capture** (`defcall_1.mp4`): reads 3-4 / 4-4 / Nickel off
  the coverage-card screens and correctly abstains on the formation-picker browse screens.
- **KNOWN v0.2 edge:** an offensive "Goal Line" formation collides with the "Goal Line"
  front (the only overlapping token) — deferred (needs a possession/badge confirm); rare,
  and the two screens are mutually exclusive per snap.

Remaining for the OCR pivot: **v0.3 coverage** — the SELECTED-card resolution (the
coverage-card browse screen shows 3 equal options; the call = which button the user
presses) + wire `detect_coverage`. The front is committed once the user is on a
formation's cards, so v0.2 didn't need selected-card; v0.3 coverage does.

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
