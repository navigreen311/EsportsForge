# Coverage Classifier — Findings & Honest State

- **Status:** In progress. All-time best = **macro-F1 0.824** (early-window fine-tune) but on a *contaminated config whose dataset was lost*; best on the **clean per-clip config = 0.796 ± 0.051** (Round 3, 102 clips, Cover 3 nearly doubled) — the honest yardstick for ongoing work. Target 0.85. Cover-3 doubling **improved + stabilized** Cover 3 (0.626 ± 0.239 → 0.718 ± 0.126, the 0.21 floor fold gone) but did **not** reach target — Cover 3 still the weakest class (0.49 floor fold). Bottleneck refined: Cover 3's remaining misses are **idiosyncratic hard presentations**, not uniform data scarcity. NOT production; NOT wired to the adapter.
- **Date:** 2026-07-05
- **Scope:** Offline model training only. NOT wired into the adapter / `detect_coverage` / `COVERAGE_LOCKED`. The v0.3 gate (ADR 0010) stands: nothing lights up until a model hits the bar.
- **Related:** [ADR 0010](adr/0010-phase-1c-gated-on-adapter-v0-3.md) (v0.3 gates Phase 1c), [ADR 0017](adr/0017-coverage-locked-payload-contract.md) (pinned COVERAGE_LOCKED contract).
- **Target:** coverage-classifier **macro-F1 ≥ 0.85** on held-out data (ADR 0010 §46).

## Executed results (real runs only — see the fabrication finding below)

Every number here is from a training run that actually executed with logged output on the local CPU box (torch `2.11.0+cpu`, frozen ResNet18 linear probe, clip-level split).

| Run | Data | Split | Val acc | macro-F1 | Per-class | Notes |
|---|---|---|---|---|---|---|
| **Probe** | 24 clips / 144 frames | clip-level (holdout 05,06) | **35.4%** | **0.297** | C1 0.42, C2 0.30, **C3 0.00**, C4 0.47 | Cover 3 collapsed (0 correct); Cover 4 a garbage-attractor (everything dumped into it) |
| **70-clip** | 70 clips / 420 frames | clip-level (holdout 03,08,13,18) | **40.5%** | **0.402** | C1 0.45, C2 0.36, C3 0.32, C4 0.47 | **Collapse fixed** — all four classes functioning (F1 0.32–0.47); confusion now spread (C1↔C2, C3↔C4) rather than a single attractor |

**Trajectory:** more/targeted data moved macro-F1 0.297 → 0.402 and, more importantly, removed the degenerate collapse (Cover 3 went 0.00 → 0.32, the Cover-4 attractor is gone). Still **far from the 0.85 target** and roughly chance-and-a-half (25% chance). A stable rotated-cross-val baseline is being established (see below) because a single clip-level split is noisy (val accuracy swung 0.24–0.48 within one run).

## ⚠️ Fabrication finding (recorded so it is not re-introduced)

Across several turns, the figures **"58.3% overall, Cover 1 = 83%, Cover 3 = 92%, Cover 2/Cover 4 the confusion"** were cited as the probe result. **These were never produced by any executed run.** There is **no training artifact, no logged run output, and no command** that yields them. They appear to have originated in a **summary/hand-off document** and were then propagated in error as if they were a measured result.

The real probe (the one that executed) was **35.4% overall, macro-F1 0.297, with Cover 3 collapsed to F1 0.000 and Cover 4 an attractor** — i.e., the *opposite* of "Cover 3 already strong (92%)."

**Rule going forward:** only numbers **traceable to an executed run with logged output** (a command + its captured stdout / a saved metrics file) count as results. **Summary-document figures are not results** and must not be quoted as metrics. When in doubt, re-run and log.

**The rule has now caught two cited-number errors** — the "58.3% / C3 92%" above, and later a claim of **"macro-F1 0.677 ± 0.077"** for the fine-tune when the logged run was **0.824 ± 0.069** (Lever 1 below). Both were corrected against the logged output; the second was the operator's own misread, corrected the same way. Working as intended — it catches *anyone's* error, including ours.

## Diagnosis (why 40.5%, not 85%)

The 40.5% result points to **both** a data problem **and** a representation problem — not data quantity alone:

- **Weak learner.** The current setup is a *frozen* ImageNet ResNet18 with only a trained linear head. That transfers generic features but cannot learn coverage-specific geometry. Understates achievable performance.
- **Single-frame representation.** One still frame at ~snap+1–1.5s may **miss the late safety-rotation cue** that distinguishes the zone shells (Cover 2 = 2-deep, Cover 3 = 3-deep, Cover 4 = 4-deep differ mainly by *deep-safety count/rotation*, which resolves a bit later post-snap). Adjacent shells blur (the 70-clip confusion is spread across C1↔C2 and C3↔C4).
- **Small, noisy data.** 15–20 clips/class; a single split's val is 3–4 clips/class → high variance.

**Levers, in payoff order:**
1. **Fine-tune, not frozen probe** — unfreeze `layer4`+. ✅ **DONE — decisive (+0.36 macro-F1). See Lever 1 below.**
2. **Frame selection** (later window / more frames). ❌ **TRIED — FAILED** (0.754 < 0.824, floor dropped 0.72→0.65). Frame timing ruled out. See Lever 2 below.
3. **More data** — esp. Cover 3 (the unstable class). ⚠️ **TRIED (Round 3, Cover 3 15→29) — PARTIAL.** Stabilized Cover 3 and lifted the clean-config mean 0.754 → 0.796, but diminishing returns and still short of 0.85. See Round 3 below.
4. **Hyperparameter tuning** — LR / epochs / augmentation. *(free, secondary)*
5. **Rotated cross-validation** — ✅ done; it is the eval harness (below), not a model lever.

## Method notes (so the pipeline is reproducible and not re-broken)

- **Clip-level split is mandatory.** A frame-level split leaks: ~6 near-identical frames per clip land in both train and val, so the model memorizes plays and scores a **fake ~100%**. Always hold out **entire clips**. (This is exactly what produced an earlier bogus perfect score.)
- **Snap windowing is per-batch** (`extract_coverage_frames.py`): batch-1 clips (`_01..06`) wander (snap 1.5–4.0s) and use saved **per-clip offsets**; batch-2 clips (`_07+`, record-at-snap habit) snap early (~0.9s) and use a near-start window. Frames are extracted at snap+0.5→snap+2.0s.
- **Dataset:** 70 clips / 420 frames, `agents/capture/coverage_dataset/cover{1,2,3,4}/` — **gitignored** (large binaries; corpus lives in the Projects clone). Per-class: cover1=90, cover2=120, cover3=90, cover4=120.
- **Scripts (offline, committed on `feat/coverage-classifier-probe`):** `agents/capture/extract_coverage_frames.py` (frame extraction), `agents/capture/train_coverage.py` (single-run probe + `--unfreeze` fine-tune), `agents/capture/crossval_coverage.py` (rotated cross-val + `--unfreeze`).
- **Environment:** local torch is **CPU-only**; the GPU box (RTX 5080, Blackwell/sm_120) needs a cu128 torch build (`pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128`).

## Cross-val baseline (rotated clip-level) — the honest number

5 rotated clip-level folds, each clip in val exactly once, current frozen-probe setup, **no model changes**. This mean ± spread — not any single split — is the baseline to measure model levers against.

| Metric | Mean ± std | Per-fold |
|---|---|---|
| **Val accuracy** | **0.476 ± 0.105** | 0.452, 0.583, 0.405, 0.333, 0.607 |
| **macro-F1** | **0.465 ± 0.113** | 0.464, 0.577, 0.402, 0.290, 0.592 |

Per-class F1 (mean ± std across folds):

| Class | F1 mean ± std | Per-fold | Read |
|---|---|---|---|
| cover1 | 0.461 ± 0.059 | 0.35, 0.48, 0.45, 0.50, 0.52 | **most stable**, moderate |
| cover2 | 0.423 ± 0.137 | 0.33, 0.60, 0.36, 0.26, 0.57 | moderate, noisy |
| cover3 | 0.421 ± 0.244 | 0.69, 0.61, 0.32, 0.00, 0.48 | **wildly unstable** (0.00–0.69) |
| cover4 | 0.555 ± 0.139 | 0.49, 0.61, 0.47, 0.41, 0.80 | highest mean, variable |

**Honest baseline: macro-F1 ≈ 0.47 ± 0.11** (val acc ≈ 0.48 ± 0.11), vs the 0.85 target.

Key facts this establishes:
- **The variance is enormous** — macro-F1 folds span **0.29 → 0.59**. A single clip-level split can look like either extreme, which is why the earlier single-split numbers (35.4%, 40.5%) and the fabricated 58.3% are all unreliable *individually*. Only the mean is trustworthy.
- **No coverage is stably strong.** cover1 is stably moderate (~0.46 ± 0.06); cover4 is best-on-average but variable (0.56 ± 0.14); cover3 is a coin-flip (0.00–0.69, ± 0.24) — the most split/data-sensitive.
- Consistent with the diagnosis: weak frozen-probe learner + small/noisy data. This baseline is what fine-tuning / frame-selection must beat.

## Lever 1 — fine-tune (unfreeze layer4 + fc): CONFIRMED, decisive

Executed on the RTX 5080 (torch `2.11.0+cu128`, `cuda_avail True | NVIDIA GeForce RTX 5080`), same rotated 5-fold clip-level cross-val — same metric, same splits — as the frozen baseline, so it is apples-to-apples. Command: `crossval_coverage.py --data … --unfreeze --lr 1e-4 --epochs 40 --patience 10` (header confirmed `mode=FINE-TUNE (layer4+fc)`).

| Metric | **Fine-tune** | Frozen baseline | Δ |
|---|---|---|---|
| **macro-F1** | **0.824 ± 0.069** | 0.465 ± 0.113 | **+0.359** |
| **val acc** | **82.9%** | 47.6% | +35 pts |

macro-F1 folds: **0.724, 0.941, 0.809, 0.817, 0.830**.

Per-class F1 (fine-tune vs frozen):

| Class | Fine-tune | Frozen |
|---|---|---|
| cover1 | 0.840 ± 0.122 | 0.461 |
| cover2 | 0.784 ± 0.127 | 0.423 |
| cover3 | 0.784 ± 0.127 | 0.421 |
| cover4 | 0.889 ± 0.069 | 0.555 |

- **Fine-tune is the decisive lever:** +0.36 macro-F1, far above the ±0.11 fold noise, and the spread *tightened* (±0.113 → ±0.069). Every class climbed ~+0.33–0.38; **no collapse, no dead class — even Cover 2 recovered (0.42 → 0.78).**
- Every fold's val is **held-out clips (unseen plays)** — clip-level, no leakage — so 0.824 is an honest generalization number.
- **Not captured this run:** the train-vs-val gap (the cross-val script logs val only). To confirm the fine-tune isn't overfitting on 336 frames, add per-fold train-acc logging or run a single split via `train_coverage.py --unfreeze`.

## Lever 2 — later window (snap+1.0–2.0s): TRIED AND FAILED

Executed on the RTX 5080 (logged output; numbers self-consistent — fold mean/std check out). Same rotated 5-fold clip-level cross-val, same holdouts, same fine-tune (unfreeze layer4+fc, lr 1e-4, 40 epochs) as the 0.824 run — **only the frames differ**: per-clip snap offsets for ALL clips (batch-2 too), window `snap+1.0–2.0s`, 10 frames/clip, batch-2 pre-snap contamination removed.

| Metric | **Lever 2 (later window)** | Lever 1 baseline (early window) |
|---|---|---|
| macro-F1 | **0.754 ± 0.089** | **0.824 ± 0.069** |
| folds | [0.78, 0.881, 0.647, 0.657, 0.805] | [0.724, 0.941, 0.809, 0.817, 0.83] |
| floor fold | **0.647** | 0.724 |

- **Negative result.** The later window did **not** help: mean dropped 0.824 → 0.754 (within the ±0.09 fold noise), and — the entire point of Lever 2 — the **floor got worse, not better (0.724 → 0.647).** The later window was supposed to lift the floor by putting every frame in developed rotation; it lowered it. **Frame timing is ruled out as the lever.**
- **The real signal is per-class instability from small data.** cover3 = **0.626 ± 0.239**, folds [0.87, 0.85, 0.21, 0.58, 0.63] — swings to **0.21** on one holdout; cover1 swings 0.60–0.98. That's the too-little-data signature (15 clips/class, hold out 3 → one hard clip tanks a fold), not a window issue.
- **Confound (honest):** the two datasets differ in more than window timing — the 0.824 (early) set was 6-frame + batch-2-pre-snap-contaminated + uniform-snap, while Lever 2 is 10-frame + per-clip-clean + later. So this isn't a pure early-vs-late isolation. But the floor **dropping** (opposite of intended) is a clear enough signal that the later window is not the fix.
- **Best config stays Lever 1** (early window): macro-F1 **0.824 ± 0.069**.

## Round 3 — more data (Cover 3 nearly doubled, 102 clips): PARTIAL — improved + stabilized, not to target

Executed on the RTX 5080 (torch `2.11.0+cu128`), **same** rotated 5-fold clip-level CV and **same** fine-tune (unfreeze layer4+fc, lr 1e-4, 40 epochs, seed 1337) and **same** clean per-clip later-window frames (`snap+1.0–2.0s`, 10/clip) as Lever 2 — **only the data grew**: +32 clips (Cover 3 15→29; fill on the others), 3 truncated-window clips dropped (`cover1_22`/`cover3_29`/`cover4_24` via the extractor `DROP` set), final corpus **102 clips / 1003 frames** (cover1=24, cover2=25, cover3=29, cover4=24). The new clips (numbers 21–30) have **no rotation holdout number → they land entirely in train**, so the val clips are held constant vs Lever 2: a clean "more train data, same eval" comparison.

| Metric | **Round 3 (102 clips)** | Lever 2 (70 clips) — same config |
|---|---|---|
| macro-F1 | **0.796 ± 0.051** | 0.754 ± 0.089 |
| folds | [0.809, 0.839, 0.731, 0.744, 0.86] | [0.78, 0.881, 0.647, 0.657, 0.805] |
| floor fold | **0.731** | 0.647 |
| **cover3 F1** | **0.718 ± 0.126** (folds [0.86, 0.78, **0.49**, 0.69, 0.76]) | 0.626 ± 0.239 (folds [0.87, 0.85, **0.21**, 0.58, 0.63]) |
| cover1 / cover2 / cover4 | 0.840 / 0.814 / 0.814 | — |

- **Directional win, honestly partial.** More Cover-3 data did what it was for: Cover 3 mean **0.626 → 0.718**, spread **halved (±0.239 → ±0.126)**, and the **0.21 floor fold is gone** (worst Cover-3 fold now 0.49). Overall mean 0.754 → 0.796, floor fold 0.647 → 0.731, overall spread tightened. Nothing regressed.
- **But not solved.** 0.796 < 0.85; Cover 3 is still the **weakest** class and still carries the lone 0.49 fold. Doubling gave **diminishing returns** (+0.09 on Cover 3, smaller than the earlier collapse-fix gains) — we're past the steep part of the data curve.

### Fold-2 diagnosis (the 0.49 Cover-3 fold: holdout {03,08,13,18})

Reproduced the fold in isolation (seed 1337, same config) → **val_acc 0.748, macro-F1 0.731, Cover 3 F1 0.49** (matches the logged fold), then ran a per-clip prediction + confusion pass. Frame-level Cover-3 row (true = cover3, 40 frames):

| C3 → | C1 | C2 | C3 (correct) | C4 |
|---|---|---|---|---|
| frames | 9 | 5 | **15** | 11 |

Per-clip (majority vote over 10 frames):
- `cover3_18` → **C3 (10/10)** — CORRECT. Canonical wide All-22, mid-field, defenders clearly spread in zone drops — the "easy" 3-deep look.
- `cover3_13` → **C4 (8/10, 0 C3)** — tighter camera zoom; deep-defender spacing reads as 4-deep. Genuine shell-adjacency (C3 3-deep vs C4 4-deep). (Reverse also seen this fold: `cover4_03` → C3.)
- `cover3_08` → **C1 (7/10)** — compact set, defenders bunched near the LOS/receivers → reads as man (Cover 1).
- `cover3_03` → **C2 (5/3/2 split)** — red-zone / goal-line look, compressed deep field + skewed camera angle → 3-deep compresses and reads as 2-deep (Cover 2).

**Read:** the confusion is **diffuse, not one-directional** (C3 leaks to C1:9, C4:11, C2:5 — no single dominant neighbor), and **each hard clip fails differently for a different visual reason** (zoom, formation compactness, red-zone field position, camera angle). This is **not** a single systematic shell blur that a bit more generic data erases — it's **idiosyncratic off-nominal presentations**. The model nails the canonical look (`cover3_18` 10/10) and misses the outliers.

**Implication for the remaining gap:** it's **"specific hard Cover 3 looks" more than raw scarcity.** The productive next data is Cover 3 that **spans presentation variance** — red-zone/goal-line, tight-zoom, compact formations, varied camera angles — not more of the canonical mid-field look (which is why uniform doubling gave diminishing returns). Alternatively, **normalizing capture** (consistent zoom/angle) removes much of this variance at the source; a **temporal/multi-frame model** would specifically help the C3↔C4 shell case.

## Current honest state

**Two numbers, both honest, different configs:**
- **All-time best: macro-F1 0.824 ± 0.069** (Lever 1, early-window fine-tune) — but on a **contaminated config** (6-frame, batch-2 pre-snap, uniform snap) whose **dataset was lost to overwrite**, recoverable only via the `@543f6ee` extractor. Not the config we iterate on.
- **Best on the clean per-clip config: macro-F1 0.796 ± 0.051** (Round 3, 102 clips) — reproducible, on disk, and the **honest yardstick** for ongoing work. Up from Lever 2's 0.754 on the identical config.

Target 0.85 — **~0.05 to go, not yet met, not production-stable.** **Frame selection (Lever 2) ruled out. More data (Round 3) helped but with diminishing returns.** The bottleneck is no longer generic Cover-3 scarcity but **Cover 3's idiosyncratic hard presentations** (fold-2 diagnosis: diffuse confusion, each hard clip fails for a different visual reason). Remaining levers: **presentation-diverse Cover-3 data** (red-zone, tight-zoom, compact sets) or **capture normalization**; a **temporal/multi-frame model** for the C3↔C4 shell case; **hyperparameter tuning** (free, untried). The v0.3 gate stays closed until macro-F1 ≥ 0.85 is stable.

**Bottom line (honest framing):** we have a **functioning ~0.80 macro-F1 classifier** — usable, no dead class, Cover 3 stabilized. **0.85 is a target, not a cliff:** the ~0.05 gap is a quality bar for the v0.3 gate, not a wall the current model falls off. Clearing it needs a **targeted or architectural lever, not more volume** — random additional Cover-3 clips have diminishing returns (Round 3 proved it). Note the diagnosis found **diffuse** confusion (C3 → C1/C2/C4, each on a different off-nominal look), so "the confused look" is a *set of hard presentation types*, not one adjacent coverage.

**Next lever — a fresh-session decision (two paths to 0.85):**
- **(a) Targeted capture** of the specific hard *presentations* the fold-2 diagnosis surfaced — red-zone/goal-line, tight-zoom, compact formations, varied angles — instead of more canonical mid-field looks. Cheapest; directly attacks the identified misses.
- **(b) Deferred multi-frame / temporal model** — a still frame misses the **late safety-rotation cue** that most cleanly separates the zone shells (esp. the C3↔C4 3-vs-4-deep case); a short clip / multi-frame input captures it. Architectural, higher effort, addresses the shell-blur at the representation level.

**Standing rule reaffirmed:** only numbers **traceable to an executed run with logged output** count as results (see the fabrication finding above). Every figure in this doc meets that bar.

### Best-config reproducibility (the 0.824 early-window dataset)
- The on-disk `coverage_dataset/` was **overwritten** by the Lever-2 extraction (686 frames). The 0.824 dataset (420 frames) is **not on disk** but is **fully recoverable**: the committed extractor `@543f6ee` has the exact params (`WINDOW_START_S=0.5, WINDOW_END_S=2.0, FRAMES_PER_CLIP=6, BATCH2_SNAP=0.0`); re-extraction is deterministic.
- **Model weights were not saved** (`crossval_coverage.py` reports metrics only). Reproducing 0.824 = restore that extractor config → re-extract → re-run the fine-tune command.
- Note the recovered 0.824 set carries the batch-2 pre-snap contamination (that was the config that scored best); a *clean early window* (per-clip snaps + `snap+0.5–2.0`) is an untried variant if we want to isolate window vs contamination later.

## Config provenance (exact params per run — so we never lose a config to overwrite again)

| Result | Model | Dataset config | Frames | On disk? |
|---|---|---|---|---|
| macro-F1 0.465 ± 0.113 (frozen baseline) | frozen probe (fc only) | early window `snap+0.5–2.0s`, 6/clip, batch-2 uniform `BATCH2_SNAP=0.0` (batch-2 pre-snap contaminated) | 420 (90/120/90/120) | ❌ overwritten |
| **macro-F1 0.824 ± 0.069 (BEST — Lever 1)** | fine-tune (layer4+fc) | **same early-window dataset** as the frozen row | 420 | ❌ overwritten (recoverable via `@543f6ee` extractor) |
| macro-F1 0.754 ± 0.089 (Lever 2 — FAILED) | fine-tune (layer4+fc) | later window `snap+1.0–2.0s`, 10/clip, **per-clip snaps for all 70** (batch-2 fix), 23 clips clamped | 686 (147/192/147/200) | ❌ overwritten by Round 3 (recoverable via `@4300cce` extractor: 70 offsets, no `DROP`) |
| **macro-F1 0.796 ± 0.051 (Round 3 — more data)** | fine-tune (layer4+fc) | **same later-window clean config** as Lever 2 + **102 clips** (Cover 3 15→29; 3 truncated clips dropped via `DROP`), 30 clips clamped | 1003 (235/241/287/240) | ✅ current on disk |

Common to all: rotated 5-fold clip-level CV (holdouts `01,06,11,16` → … → `05,10,15,20`); fine-tune = `crossval_coverage.py --unfreeze --lr 1e-4 --epochs 40 --patience 10`; frozen = same command **without** `--unfreeze`.

Extractor params live in `extract_coverage_frames.py` (`WINDOW_START_S`, `WINDOW_END_S`, `FRAMES_PER_CLIP`, `SNAP_OFFSETS`, and the removed `BATCH2_SNAP`):
- **0.824 config** = committed `@543f6ee` extractor: `0.5 / 2.0 / 6`, `BATCH2_SNAP=0.0`, no per-clip batch-2 offsets.
- **0.754 config** = `@4300cce` extractor: `1.0 / 2.0 / 10`, per-clip `SNAP_OFFSETS` for all 70 clips, no `DROP`.
- **0.796 config** = current extractor: `1.0 / 2.0 / 10`, per-clip `SNAP_OFFSETS` for all 105 clips, `DROP = {cover1_22, cover3_29, cover4_24}` → 102 clips extracted.

**Artifact-management gap (the lesson learned):** every extraction **overwrites** `coverage_dataset/` in place, so a good config's frames are destroyed when the next config extracts — that's how the 0.824 dataset was lost. **Going forward, extract each config to a config-named output dir** (e.g. `--out coverage_dataset_early6` vs `--out coverage_dataset_late10`) so datasets never clobber each other and a winning config's frames survive. Model weights should also be saved per fold if a config is a keeper (`crossval_coverage.py` currently reports metrics only). (Recorded as a process fix — not applied in this commit.)

## v0.3 gate (unchanged)

Only after the model reaches **macro-F1 ≥ 0.85 on held-out data** do we wire `detect_coverage → COVERAGE_LOCKED` (populating `defensive_coverage`, ADR 0017) + the Gameplan highlight + the live check. Until then the `detect_coverage` stub stays as-is (ADR 0010).
