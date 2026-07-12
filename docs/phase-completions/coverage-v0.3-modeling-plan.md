# Coverage v0.3 — modeling plan + Phase B prototype results

Follow-up to `coverage-v0.3-feasibility-spike.md` (which found the headline 0.86 was
frame-level leakage; honest held-out-by-clip is ~0.42–0.45). This records what a real
coverage effort looks like, and the **Phase B prototype** run on the existing 120-clip All-22
corpus that refined the plan.

## Phase B prototype — what actually moves the needle (5-fold by-clip, frozen ResNet18)

Tested cheaply on the existing corpus (117 usable clips, ~117 independent plays) — **no new
capture**. All numbers are macro-F1, held-out **by clip**:

| Approach | macro-F1 | Read |
|---|---|---|
| avgpool, single-frame (the shipped design) | 0.45 | baseline |
| avgpool, mean-over-window | 0.51 | frame-ensembling helps a little |
| avgpool, temporal-stats (mean+std+delta) | 0.40 | **motion features HURT** (overfit) |
| avgpool, GRU over the sequence | 0.22 | **temporal model collapses** (117 seqs too few) |
| **spatial (512×3×3, location preserved), mean-over-window** | **0.58** | **preserving WHERE is the lever** |

**Learning curve (spatial model):** val-F1 0.44 → 0.52 → 0.53 → **0.58** at 25/50/75/100% of
train clips, with **train-fit = 1.00 at every fraction**. Still climbing at 93 clips, not
saturated.

### Three conclusions (each changed the plan)

1. **Single-frame was not the (whole) problem; TEMPORAL is not the cheap win.** Aggregating
   motion over frozen avgpool features *hurt* — the GRU/temporal-stats overfit 117 plays. Don't
   invest in temporal modeling until the data is much larger.
2. **Spatial location IS the lever (0.45 → 0.58).** Coverage is geometric — *where* the safeties
   and corners are — and global average pooling threw that away. Location-aware features are the
   biggest cheap gain, and they point straight at the structured/pose approach below.
3. **Data is the binding constraint.** train-fit 1.00 + a still-rising learning curve = classic
   data-starvation. 117 plays caps everything; more clips will pay off. This is the prerequisite.

## What a real effort looks like

### 1. Granularity ladder — ship the coarsest useful tier that clears the bar

| Tier | Classes | Value | Current by-clip |
|---|---|---|---|
| T0 shell | 1-high vs 2-high | high | ~0.63 acc (near 0.58 baseline) |
| T1 man/zone | man vs zone | high | untested |
| T2 coverage | Cover 1/2/3/4 | ideal (ADR 0017) | ~0.58 (spatial) |
| T3 variant | Sky/Cloud, Tampa, Palms | nice-to-have | very hard |

Don't ship a tier until it clears the bar **held-out by game**. A reliable T0 beats an
unreliable T2.

### 2. Held-out protocol (the lesson — bake it in)

- **Split by GAME/SESSION, never by frame** (frame split leaked → 0.42→0.86). Per-clip still
  shares stadium/teams/lighting within a game; hold out whole games.
- A **frozen, versioned test set** never trained/tuned on. Report macro-F1 + per-class +
  confusion + calibration + train/val gap every run.
- **Per-play metadata** (stadium, teams, offensive formation, coverage variant, disguise y/n) to
  stratify and catch confounds (e.g. keying on the *offense* instead of the defense).

### 3. Modeling — ranked by Phase B evidence

1. **Location-aware features first** (spatial > avgpool, proven). Keep the spatial grid; consider
   cropping the deep-secondary region to concentrate signal.
2. **Structured / pose (highest upside).** Detect the secondary, place players in **field
   coordinates** (homography off yard lines), model safety depth + corner leverage + zone
   spacing. Encodes what coverage *is*; most data-efficient; interpretable. Needs a detector +
   field registration.
3. **Temporal — deferred** until data is large (Phase B shows it overfits now); then model the
   post-snap rotation (motion is the real signal, but needs the samples to support it).
4. **Backbone fine-tuning** — only once data is large (overfits at this scale).

### 4. Data campaign (the prerequisite)

- 117 plays → ~30/class is ~10× too small. Target **hundreds–low-thousands of plays per class**.
- Diversity axes: stadiums/lighting/time-of-day, uniform sets, **offensive** formations (so it
  can't cheat on offense), field position/hash, and **coverage disguise**.
- Labeling is cheap by construction: **practice-mode known-coverage capture** (set the call →
  free labels), scriptable like the digit campaign; the snap detector supplies the window; log
  the metadata above per play. (Camera: All-22 deploys; playable-cam is a separate data problem —
  see `COVERAGE_CAPTURE_PLAN.md`.)

### 5. Staged plan

- **A — Protocol** (done in spirit): by-game splits + versioned test set; honest baseline ~0.45.
- **B — Prototype** (done): spatial helps (0.58), temporal doesn't yet, data is the ceiling.
- **C — Data campaign** (next, needs capture): known-coverage, diverse, by-game folds. The
  learning curve says this pays off.
- **D — Structured/pose** (if pixels plateau): DB detection + field-normalized geometry.
- **E — Calibrate, abstain, wire**: ship only when held-out-by-game clears the tier bar; emit
  with confidence + **abstain-over-guess**; wire `detect_coverage` → `COVERAGE_LOCKED`.

### 6. Risks / kill-criteria

- If data + location-aware + (eventually) temporal **can't beat ~0.65 by-game on even the T0
  shell**, live-feed coverage may not be worth it → pre-snap shell proxy, or scope out (the
  `gameplan/coverageHighlight.ts` seam is documented-silent, degrades gracefully).
- **Disguise** is inherent difficulty. **Playable-cam** support is a second, harder data problem.

*Reproduce Phase B: build the dataset with `agents/capture/extract_coverage_frames.py`, then
`python agents/capture/coverage_probes.py --data <coverage_dataset>` — it runs the leakage demo,
the avgpool-vs-spatial / temporal comparison, the learning curve, and the T0 shell probe (frozen
ResNet18, 5-fold by-clip). The by-clip 4-way baseline is also the repo's `crossval_coverage.py`.*
