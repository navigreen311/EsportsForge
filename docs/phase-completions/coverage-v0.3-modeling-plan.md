# Coverage v0.3 — modeling plan + Phase B prototype results

Follow-up to `coverage-v0.3-feasibility-spike.md` (which found the headline 0.86 was
frame-level leakage; honest held-out-by-clip is ~0.42–0.45). This records what a real
coverage effort looks like, and the **Phase B prototype** run on the existing 120-clip All-22
corpus that refined the plan.

## ⛔ BY-GAME VALIDATION (2026-07-12) — the tier ladder does NOT hold; POST-SNAP VISION IS A RESEARCH ARC. Pivoting to OCR-of-play-call.

**Everything below (the T0 0.83 / T1 0.87 / T2 0.74 tier numbers) was measured BY CLIP on a
SINGLE visual context** (the 120-clip corpus is all one Raiders matchup). We captured **4 new
game-tagged games** (Chargers/Rams/Packers/… — distinct stadiums, teams, lighting) precisely to
test generalization **by game**. It does not generalize:

| Approach (leave-one-GAME-out unless noted) | shell 1-high/2-high |
|---|---|
| fixed deep-crop (the "0.83" method), by-CLIP on new clips | **0.375** — broken on new stadiums |
| whole-frame CNN | 0.44 |
| player-bbox CNN | 0.06 (by-clip) |
| deep-defender crop CNN | 0.18 (by-clip) |
| **structured deep-defender COUNT** | **no separation** (6.96 vs 6.96) |

**Near chance across every approach** — several can't even separate the 16 new clips by-clip. The
0.83 was the model keying on **context** (stadium/uniforms/framing), not reading coverage. A
robust player-detection **framing** was built (person detector → player-relative crop, which
*does* solve the field-position problem and is reusable), but frozen ImageNet features simply
don't carry the 1-vs-2-safety signal, and a direct geometric deep-count doesn't separate it
either (too confounded: which players are the defense, safeties-vs-corners, camera/field-position
depth).

**Verdict: reading post-snap coverage from broadcast/All-22 frames is a genuine RESEARCH ARC** —
it needs a purpose-trained model + player tracking + field registration + diverse labelled data
at scale. **Do NOT wire the T0/T1/T2 classifiers** — they would emit context-overfit,
near-chance predictions in production. The by-game captures did their job: they caught the
mirage before it shipped. (Reproduce: `agents/capture/player_crop.py` + the scratch validation.)

**PIVOT — OCR-of-defensive-play-call (the same move that saved the formation classifier, ADR
0014).** The defensive **play-call screen shows the coverage by name** ("Cover 1 Hole", "Cover
3", "Sam Mike 1") — read it with the proven overlay-OCR pattern (`read_formation_name` /
`is_play_call_screen`). It sidesteps the vision problem for the cases it covers (the defensive
call is on-screen: you're calling the D / analysing your own defense). It **cannot** read the
*opponent's* coverage while you're on offense — that remains the hard vision case, deferred. It
also shares the play-call screen with the **v0.2 defensive front** (same OCR pass reads Nickel/
Dime *and* the coverage). See `coverage-ocr-playcall-pivot.md`.

*The tier-ladder material below is retained as the honest record of what was tried and why it
was abandoned — read it with this correction in mind.*

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
| T3 variant | Cover 2-Man, Cover 1-Robber, Cover 0/6 (ADR 0017) | nice-to-have | **data-blocked** — no variant labels (see "T3 assessed") |

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

#### T3 assessed — data-blocked (no variant labels); defer

T3 is categorically different from T0–T2 and **cannot be started on the existing corpus**: the
120 clips are labeled `cover1/2/3/4` only — there are **no variant labels** and no variant
examples, so there is nothing to train or evaluate. (T0–T2 all had labels *derivable* from
cover1–4; T3 does not.) Running an unsupervised within-class clustering probe would only surface
stadium/formation structure, un-attributable to variants — misleading, so not run.

**The in-scope T3 vocabulary is narrow (ADR 0017), not "every variant":** `Cover 2-Man`,
`Cover 1-Robber` (emit if distinguishable), plus `Cover 0` (pure man, 0-high) and `Cover 6`
(quarter-quarter-half). ADR 0017 also treats **man vs zone as *derivable* from the coverage
number** (0/1 = man, 2/3/4/6 = zone), so it is **not** a T3 visual-classification task — that
axis is already covered by the number. The genuinely-visual T3 asks are the *man wrinkles*:
Cover **2-Man** (a 2-high shell played man) and Cover **1-Robber** (Cover 1 + a robber).

**Encouraging connection:** those are exactly the man-vs-zone *technique* signal T1 already found
learnable (0.87 on the clean Cover1-vs-Cover3 slice) — so detecting "a 2-high shell being played
man" (Cover 2 vs Cover 2-Man) is plausibly within reach *once labeled examples exist*. The schema
is already ready: `defensive_coverage` is a free-str with the vocabulary ADR-pinned (0017), so no
contract work is needed.

**Recommendation: defer T3 until T0–T2 ship.** It's the finest, hardest, lowest-value tier, and
it's blocked on data, not modeling. When pursued, it's a simple extension of the game-tagged
capture: add `Cover 0 / Cover 2-Man / Cover 1-Robber / Cover 6` calls (labeled by construction in
practice mode) to the same sessions — one campaign still feeds every tier.

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
