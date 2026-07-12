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
| T0 shell | 1-high vs 2-high | high | **0.83 F1** with deep-field crop (see "T0 started" below) |
| T1 man/zone | man vs zone | high | signal PRESENT: **0.87 F1** on Cover1-vs-Cover3 (see "T1 probed") |
| T2 coverage | Cover 1/2/3/4 | ideal (ADR 0017) | **0.74** hierarchical + deep crop (was flat 0.45/0.58 — see "T2 reframed") |
| T3 variant | Sky/Cloud, Tampa, Palms | nice-to-have | very hard |

Don't ship a tier until it clears the bar **held-out by game**. A reliable T0 beats an
unreliable T2.

#### T0 started — the shell is buildable (deep-field crop)

Started T0 on the existing 120 clips (`agents/capture/coverage_t0_shell.py`). The shell IS the
deep-safety count, so cropping the frame to the **deep field** (top ~40% in the All-22 view,
where the safeties sit) jumps T0 from **0.67 → 0.83 macro-F1** (5-fold by-clip). Crops 35–50%
all work; 30% is too tight (cuts safeties). **Cropping *away* the crowd/sideline *helped* —
evidence the signal is the safeties, not a stadium confound.**

| conf gate | coverage | accuracy |
|---|---|---|
| ≥0.5 (none) | 100% | 0.84 |
| ≥0.8 | 76% | 0.90 |
| ≥0.9 | 69% | 0.91 |

Under the codebase's **abstain-over-guess** rule this is a shippable-shaped signal: call the
shell when confident (~0.90), abstain otherwise. It clears the ~0.65 kill-criterion.
**Gaps to actually ship:** (a) validate **held-out by game** (this is by-clip; no game labels in
the corpus — needs a held-out capture); (b) more data (117 plays, still data-bound); (c) the
top-40% crop is a mildly eval-selected hyperparameter. Path: a small known-coverage capture
with game/session tags → by-game validation → wire `detect_coverage` to emit `1-high/2-high` +
confidence + abstain (T0 first; keep `defensive_coverage` free-str per ADR 0017).

#### T1 probed — the man/zone signal is present (needs diverse captures to build)

Probed T1 for **signal presence** (`agents/capture/coverage_t1_manzone.py`). The corpus
doesn't cleanly support man/zone (only Cover 1 is unambiguously man; Cover 2 is ambiguous;
man/zone correlates with the shell), so the clean test that isolates man/zone from the shell is
**Cover 1 (man) vs Cover 3 (zone) — both 1-high**. Result (5-fold by-clip, top-70% crop = the DB
band): **F1 0.87, acc 0.88** (baseline 0.65); abstain conf≥0.6 → 0.89 on 94%. So DB technique
(man = turn-and-run with receivers; zone = drop/settle, eyes to QB) is a **strong, learnable
signal** — even more separable than the shell, and it lives in a wider crop (corners + safeties,
top ~70%), not the deep strip T0 used.

**But this is only a signal-presence probe on a Cover1-vs-Cover3 slice, NOT a T1 classifier.** A
real T1 needs **diverse man coverages** (Cover 0 / 1-Robber / 2-Man / man-under) and zone
coverages, and must resolve **Cover 2** — this corpus has only Cover 1 as man. So T1's path is a
**dedicated man/zone capture** (varied man + zone calls, game-tagged) → by-game validation. The
encouraging part: the signal is clearly there, so the capture is worth it.

#### T2 reframed — 4-way is not a wall (0.45 → 0.74 by-clip)

The Phase-B flat classifier put 4-way at ~0.45/0.58 and framed T2 as a modeling wall. That was
a *flat classifier on the whole frame*. Two fixes (`agents/capture/coverage_t2_hier.py`):

1. **Crop to the deep field** (the dominant lever): flat 4-way **0.58 → 0.70** just from the
   top-40% crop — same insight as T0/T1.
2. **Hierarchical decomposition** with a tailored crop per branch (**0.70 → 0.74**):
   - shell (1-high vs 2-high) — deep-40% crop — ~0.83 (T0)
   - within 1-high: Cover 1 vs 3 — top-70% crop — ~0.87 (T1)
   - within 2-high: Cover 2 vs 4 — deep-40% crop — **~0.94** (safety width, halves vs quarters,
     is crisp deep — the easiest branch)

Each branch uses the crop that best separates *its* distinction, can abstain independently, and
falls back to the coarser T0 shell when a sub is unconfident. **Net: 4-way by-clip 0.45 → 0.74**,
approaching the 0.85 target. So T2 is **not an approach wall — it's data-limited** (learning curve
still rising at 117 plays) and needs **by-game** validation (this is by-clip). Same caveats: 117
plays, per-branch crops mildly eval-selected, hierarchy errors compound (a shell miss routes to
the wrong sub). This is the same game-tagged capture as T0/T1 — one campaign feeds all three tiers.

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
