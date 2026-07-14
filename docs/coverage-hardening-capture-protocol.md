# Coverage-Hardening Capture Protocol (by-game validation)

- **Goal:** establish whether the shipped coverage OCR reader (`read_coverage` →
  `coverage_classifier`) generalizes **across games**. It was tuned + validated on a
  single ~44-min session (`cov_cc_*`, 10 coverages × 1 capture); robustness across
  stadiums / lighting / camera contexts is **not established** (the by-game validation
  that killed the earlier post-snap *vision* arc was never run on the OCR reader). This
  is the [[feedback_ml_eval_hygiene]] rule applied: reproduce the metric with a
  **GROUP-held-out (by-game)** split before building Phase 1c (Arsenal/War Room) on it.
- **Gate:** ADR 0010 wants held-out **macro-F1 ≥ 0.85** for the coverage signal.
- **Related:** `~/madden-recal-refs/digit-campaign/COVERAGE_CONSTELLATIONS.md` (the
  label fingerprints), `agents/capture/eval_coverage_by_game.py` (the eval harness),
  ADR 0017 (COVERAGE_LOCKED contract), `docs/phase-completions/coverage-ocr-playcall-pivot.md`.

## The signal being tested

The reader reads the **pre-snap COACH-CAM play-art zone-assignment text labels** (a
coverage fingerprint: `#DEEP ZONE` = shell; underneath-label density = man/zone;
QUARTER-flat side = Cover 6/9). So **every capture MUST show the play-art zone labels
pre-snap** — that is the entire signal. A gameplay/post-snap frame carries no labels and
the reader correctly abstains (`None`). The abandoned `cov_g1–g4` vision clips are NOT a
substitute (they were post-snap gameplay); this campaign re-captures the coach-cam view.

## Settings (once)

- **Defense play-art: ON** (Settings → Visual Feedback). With it on, the zone labels are
  drawn on the field pre-snap **without** opening the coach-cam every play.
- Feed: the PS5 → HDMI capture card ("USB3.0 Video"), 1920×1080. `--preflight` first
  (brightness ~16 = black/no-signal; 30–90 = live game).

## What to capture

The **10 canonical coverages**, each across **≥3–4 DISTINCT GAMES** (different
opponents/stadiums, ideally different lighting/time-of-day), **several reps per coverage
per game** (not one frame — one frame per coverage is exactly the gap this fixes).

| Capture (card name)              | canonical label | dir suffix       |
|----------------------------------|-----------------|------------------|
| Cover 0 (all-man blitz)          | `Cover 0`       | `cover0`         |
| Cover 1 (man)                    | `Cover 1`       | `cover1`         |
| Cover 2                          | `Cover 2`       | `cover2`         |
| Cover 2-Man                      | `Cover 2-Man`   | `cover2man`      |
| Cover 3 (Sky/Match/Slim)         | `Cover 3`       | `cover3`         |
| Cover 4 (Quarters)               | `Cover 4`       | `cover4`         |
| Cover 6 (quarter-quarter-half)   | `Cover 6`       | `cover6`         |
| Cover 9 (mirror of 6)            | `Cover 9`       | `cover9`         |
| Tampa 2  → folds to Cover 2      | `Cover 2`       | `tampa2`         |
| Cover 2 Invert → folds to Cover 2| `Cover 2`       | `cover2invert`   |

(Tampa 2 and Cover 2-Invert are label-identical to Cover 2 without route geometry — they
fold to `Cover 2` by design, ADR 0017. That's correct, not a miss.)

## Recipe (per rep)

1. Pick a game (note the opponent/stadium → it's the `<game>` tag, e.g. `g5`, `g6`).
2. Commit the coverage on the defensive play-call screen.
3. Pause pre-snap at the field with the play-art zone labels visible (~2–3 s).
4. Record ~25 s so capture-card feed-lag can't land on the wrong screen:
   ```
   cd ~/madden-recal-refs/digit-campaign
   <vaf-venv-python> grab_live.py --record --label cov_<game>_<coverage> --seconds 25
   ```
   → writes `cov_<game>_<coverage>/cov_<game>_<coverage>.mp4`.

**Naming is load-bearing:** `cov_<game>_<coverage>` — the `<game>` tag is how the eval
holds out by game. Use a NEW game id per distinct game (`g5`, `g6`, `g7`, …); keep the
`<coverage>` suffix exactly as the table's "dir suffix" column.

## Evaluate

From `services/visionaudioforge` with that venv (so `app` imports resolve):

```
cd services/visionaudioforge
PYTHONPATH="$PWD" .venv/Scripts/python.exe \
    ../../agents/capture/eval_coverage_by_game.py \
    --root ~/madden-recal-refs/digit-campaign --tuning-game cc
```

The harness scores each clip (mode-vote of its non-null frame reads — the same
one-coverage-per-play unit the adapter emits), then reports **per-game** accuracy, the
**HELD-OUT** aggregate (all games except `cc`), **macro-F1**, per-coverage accuracy, and
a **confusion matrix**. Unmapped dirs are listed, never silently dropped.

## Reading the result

- **Held-out macro-F1 ≥ 0.85** → the reader generalizes; ADR 0010's coverage-quality
  gate is met and Phase 1c can build on `COVERAGE_LOCKED` honestly.
- **Below that** → the confusion matrix + per-coverage table say where it breaks. Known
  fragilities to expect (from the constellation notes): far-edge labels (SOFT SQUAT /
  VERT HOOK) OCR poorly → Cover 6/9 collapse to Cover 3; the man/zone flip hinges on one
  underneath-count threshold; band/upscale were perf-tuned to the `cc` session. Fixes are
  small and DATA-led (per-label CLAHE/upscale for edges, retune the man threshold, expand
  the `_TOKEN_FIX` table) — not a classifier rewrite.
- **High abstention** on a game → that game's clips likely lack the play-art labels
  (coach-cam not held / play-art off) — a capture issue, not a reader miss.

## Baseline (first run, 2026-07-14)

Ran the harness against everything in `~/madden-recal-refs/digit-campaign`:

- **In-sample (`cov_cc`, the tuning session): 10/10** — the reader nails the session it was
  built on (Cover 0/1/2/2-Man/3/4/6/9, Tampa 2 + Cover 2-Invert → Cover 2).
- **Held-out (`cov_g1–g4`): 0/19, macro-F1 0.00 — but 15/19 ABSTAINED (0 frames read).**
  Those clips are the abandoned **post-snap vision** captures (gameplay, no play-art), so
  the reader correctly finds no zone labels and abstains. **There is no valid held-out
  coach-cam data yet** — which is the whole point: the by-game number is currently
  unmeasurable, not bad. This run's value is proving that concretely.

**Action:** capture `cov_g5+_<coverage>` **coach-cam / play-art** clips per the recipe
above (≥3 new games × the 10 coverages), then re-run. That produces the first real
held-out macro-F1 for the ADR 0010 gate.

## Also grab: 2-digit scores (same session, for `_read_score`)

`_read_score` reads live scores via patch-NCC (PR #132). Single-digit is **confirmed**
(`game_hud_1`: KC 0 / LV 6, 19/20 frames); **2-digit values (>9) are UNVERIFIED** — that
capture never scored >9, so the 2-slot segmentation path has never been checked against a
real ≥10 score. The coverage games naturally cross 9 points as they progress, so grab this
in the **same PS5 session** — no extra setup, and it's a plain gameplay frame (no coach-cam
needed for scores).

Once either team's score is 2-digit, record a short clip with the scorebug visible,
labeling the clip with the **actual score** (the ground truth):

```
cd ~/madden-recal-refs/digit-campaign
<vaf-venv-python> grab_live.py --record --label score_<game>_<home>-<away> --seconds 8
# e.g.  score_g5_14-10   when it reads 14–10
```

Aim for a spread across the **tens digit** — one clip in the 10–19 range, one in 20+ — so
each 2-digit shape is exercised (not just, say, "10" over and over).

These multi-game gameplay clips **also** serve the play-clock CNN: a game-box retrain is
feasible but couldn't be shown to beat EasyOCR on one game (labels were EasyOCR's own — see
`services/visionaudioforge/tools/play_clock/game-box-retrain-findings.md`). A second game's
grey `:SS` play-clock, or ~50 hand-labeled crops, gives the independent ground truth to
settle it. Low priority — EasyOCR ships and works.

**Evaluate:** run `read_fields` (score fields) over the extracted frames and confirm
`score_home`/`score_away` match each clip's label — the same offline check that confirmed
single-digit. A correct read on **≥2 distinct 2-digit values with different tens digits**
closes "2-digit scores confirmed." If a value misreads, the fix is small and local (the
score glyphs already match the distance templates; expect at most a per-digit template
touch-up or a `segment_patch` slot-width tweak — see `_read_score` / `_read_distance`).
