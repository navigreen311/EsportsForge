# M5c Implementation Plan — Real Madden 26 Formation Classifier + Temporal Consistency

- **Status:** Plan v2 (post-approval revisions, 2026-05-07). Revisions per user sign-off feedback: clock smoothing rationale, sub-task 6.5 added, labeling tool design specified, calendar widened to 5.5 days.
- **Date:** 2026-05-07
- **Milestone:** M5c (Phase 0 remainder, replaces synthetic-data MobileNetV3 stub)
- **References:** [docs/specs/02-visionaudioforge-core.md §"Madden 26 adapter v0.1"](../specs/02-visionaudioforge-core.md), [Phase 0 remaining milestones](0-vaf-remaining-milestones.md), [HUD calibration methodology](../integrations/visionaudioforge/madden26-hud-calibration-methodology.md), [ADR 0006 — tiered per-frame budget](../adr/0006-tiered-per-frame-budget.md), [ADR 0010 — Phase 1c gating](../adr/0010-phase-1c-gated-on-adapter-v0-3.md).

## Goal

Real Madden 26 offensive formation classifier with **macro-F1 ≥ 0.85** on the v0.1 top-8 formations against a held-out real-footage test set. Inference latency **p95 ≤ 20 ms** per the formation-detector budget in the spec table (Doc #02 §"Per-frame budget"). Plus title-agnostic temporal-consistency infrastructure that closes the M4.5 `field_position` gap (71.4% → ≥80%) as a free byproduct.

The 8 v0.1 formations (per `services/visionaudioforge/app/adapters/madden26/formation_detector.py:TOP_8_FORMATIONS`):
`shotgun_trips, shotgun_bunch, shotgun_empty, i_form_pro, singleback_ace, pistol_strong, shotgun_doubles, singleback_wing`.

## Calendar

5.5 working days end-to-end (revised from 5.0 — adds 0.5-day buffer at sub-task 6.5 per user sign-off). Each sub-task commits to PR #62 incrementally. Status checks before sub-tasks 4, 5, 7, and now 7 (post-6.5) per the user's gating rules.

| Day | Sub-task | Output |
| --- | --- | --- |
| 0.5 | 1 — Training data sourcing | 5–8 additional Madden 26 clips, gitignored, URLs documented |
| 1.0 | 2 — Frame labeling (1,200–1,600 frames) | `formation_labels.csv` + labeling tool script |
| 0.25 | 3 — Train/val/test split | `formation_split.json` with match-level disjoint splits |
| 1.0 | 4 — Training pipeline + ONNX export + parity check | `training/train_formation.py`, `formation_v0_1.onnx`, `train_log.json` |
| 0.5 | 5 — Acceptance evaluation | macro-F1, per-class P/R, confusion matrix, latency p50/p95/p99 |
| 1.0 | 6 — Temporal consistency infrastructure | `app/core/temporal.py`, dispatcher integration, methodology doc |
| 0.5 | **6.5 — Smoothing regression check (NEW)** | M4.5 harness re-run with smoothing ON vs OFF; regression-free confirmation |
| 0.5 | 7 — Phase 0 acceptance re-validation (all 8 criteria) + hud_signature curation | `phase0_final_validation.json` + status report |

**Total: 5.25 working days ≈ 5.5 days**, slightly past the original 3–5 day estimate. The 0.5-day slip is called out openly in the standup-after-sub-task-6 — no silent compression.

### Calendar slip — sub-task 1 sourcing path pivoted 2026-05-07/08

**Status:** YouTube sourcing path **permanently abandoned** for this milestone. Pivoted to Option C (local Madden 26 capture via PS5 + capture card).

**Sub-task-1 timeline of escalation (record for future-adapter retros):**

1. **2026-05-07 ~16:00 local** — first sourcing-script run, default yt-dlp args. ~100 MB of `madden26_patriots_vs_bills.mp4.part` downloaded before being prematurely killed at the 9-min mark.
2. **2026-05-07 ~16:30** — second run with `android_creator` extractor client. Format extraction succeeded; zero bytes downloaded. Pattern: YouTube rate-limit on the dev IP after rapid back-to-back yt-dlp invocations.
3. **2026-05-07 ~17:00** — third run, default args, 12-min/clip budget. Same zero-byte result. User decision: pause, retry tomorrow morning.
4. **2026-05-07 evening** — defensive-posture commit (`483d76b`). 180s inter-request sleep, idempotent cache check, invocation logging.
5. **2026-05-08 ~08:25** — first retry under defensive posture. Zero bytes after 6 minutes on the first clip. Rate-limit still active.
6. **2026-05-08 ~10:00** — Phase 1 (cookies/auth) attempt. Initial export was anonymous-session preferences only; second export with HTTP-only cookies enabled contained all 22 expected auth tokens. yt-dlp accepted the auth (anti-bot challenge cleared) but YouTube silently downgraded responses to `tv downgraded player API JSON` returning only thumbnail tile sequences instead of video formats. **Diagnosis: account-level pattern detection on the dev YouTube account, not IP-level rate-limit.** Waiting would not clear it.
7. **2026-05-08 ~11:00** — security cleanup (cookie file deletion + Recycle Bin empty + recommended Google account password rotation). Pivoted to local capture per the user's pre-defined Option C fallback.

**Why Option C is the right pivot:**

- The hardware pipeline is proven (M4.5 fixture `madden26.mp4` was captured through the same setup).
- Account-level YouTube flag is unlikely to clear without a different account; not a calendar-budget-friendly path.
- Captures controlled by the operator give cleaner training data — no streamer overlays, no facecams, no commentary watermarks.

**YouTube sourcing script status:** `scripts/hud_calibration/sample_training_clips.py` is preserved but deprecated for this milestone. Header explains why; runtime guard refuses to run unless `ALLOW_DEPRECATED_YT_SOURCING=1` is set. Reusable for future title adapters with fresh (un-flagged) accounts.

**Local capture protocol:** [docs/integrations/visionaudioforge/madden26-local-capture-protocol.md](../integrations/visionaudioforge/madden26-local-capture-protocol.md) — captures the same per-clip and matchup-diversity requirements with the new sourcing path.

**Calendar effect:** **M5c shifts by an additional 2–3 calendar days** beyond the original 5.5-working-day estimate, accounting for Madden 26 purchase + install + capture work on the operator's side. Cumulative slip from M5c plan v2 baseline:

| Slip | Cause | Magnitude |
| --- | --- | --- |
| Sub-task 6.5 buffer | Smoothing regression check (planned at v2 sign-off) | +0.5 working day |
| Sub-task 1 rate-limit | YouTube IP throttle (2026-05-07) | +1 calendar day |
| Sub-task 1 path pivot | YouTube account flag (2026-05-08) → local capture | +2–3 calendar days |

**Revised end-of-M5c projection: 2026-05-18** (vs. original 2026-05-14, vs. v2-after-rate-limit 2026-05-15). Phase 0 close projection: **2026-05-19** (one calendar day after M5c close, accounting for Phase 0 status doc finalisation).

The slip is documented honestly here — no silent compression. If clip delivery moves faster than expected, M5c may close earlier; the revised projection is the conservative side.

## Sub-task 1 — Training data collection

**Estimate:** 0.5 day.

### How much footage beyond the 2-min M4.5 fixture?

The `madden26.mp4` M4.5 fixture yielded ~10 HUD-bearing gameplay frames across 7 unique pre-snap states in 2 minutes. Pre-snap windows in NFL gameplay average 5–8 seconds; offensive formations change every play (~30–40 seconds total); each formation may show ~30–60 stable frames during pre-snap.

To reach 1,200–1,600 labeled frames covering 8 formations with realistic class balance:

- **Target: ~1,400 labeled frames total** (~175 per class).
- **Per-clip yield**: ~80–120 pre-snap-stable frames (assuming a 2-min clip with ~3–4 plays).
- **Need: ~12–18 additional 2-min clips** OR ~5–8 longer clips (5–10 minutes each).

I recommend the **5–8 longer clips** path. Longer clips give more match diversity and reduce the per-clip download/setup overhead.

### Single-source vs multi-source?

**Multi-source. Single-source is a documented overfit risk.** Different teams, jerseys, stadium lighting, broadcast presentation, and camera angles all matter for generalization. Concretely:

- **5 distinct matchups minimum** (different team pairs).
- **Mix of day/dome lighting** if achievable from public clips.
- **Skip exhibition/practice modes** — HUD differs.

Realistic plan: source 5–8 YouTube clips of Madden 26 ranked or franchise gameplay, 5–10 minutes each, varied team matchups. Document each clip's URL + matchup + duration in a regeneration script alongside the existing `madden26.mp4` reference.

### Sourcing strategy

**Active path (2026-05-08 onward): Option C — local Madden 26 capture.** PS5 + capture card + dev workstation. Same hardware pipeline that produced the M4.5 fixture (`agents/capture/fixtures/real/madden26.mp4`). Protocol: [docs/integrations/visionaudioforge/madden26-local-capture-protocol.md](../integrations/visionaudioforge/madden26-local-capture-protocol.md). Operator delivers .mp4 files to `agents/capture/fixtures/real/`; verification harness runs on each on operator instruction.

**Deprecated path (Option A — YouTube yt-dlp sourcing).** Permanently abandoned for this milestone after the 2026-05-08 account-level pattern flag on the dev YouTube account. Script at `scripts/hud_calibration/sample_training_clips.py` is preserved but guarded against accidental run. See "Calendar slip — sub-task 1 sourcing path pivoted" section below for full timeline.

**Original (deprecated) Option A strategy follows for reference and for future adapter reuse:**

Public YouTube Madden 26 ranked / franchise / MUT gameplay clips, found by searching "Madden 26 ranked gameplay" / "Madden 26 franchise" / "Madden 26 best plays". Same `yt-dlp` toolchain proven in M4.5 (already in the backend venv).

**Selection criteria** (in priority order):

1. Clip is ≥ 3 minutes of continuous gameplay (not highlights).
2. Streamer is using Madden's stock HUD (no custom overlays that could mask the bottom band).
3. Resolution ≥ 1080p (the calibration target).
4. Mix of teams — avoid 5 clips of the same team. Aim for ≥ 4 different offensive teams across the 5–8 clips so jersey colour and helmet aren't the dominant feature.
5. Avoid game-mode menus (only gameplay clips with HUD visible).

**URL documentation**: every selected URL goes in `scripts/hud_calibration/sample_training_clips.py` with the `yt-dlp` command pattern from M4.5's `madden26.mp4` regeneration. The script is the canonical regeneration source — committed; the .mp4s themselves stay gitignored.

**Fallback URLs**: for each matchup, list a primary + at least one alternate URL. If a primary 404s during regeneration, the alternate kicks in. Documented in script comments.

### Storage

Same gitignored path: `agents/capture/fixtures/real/`. Naming convention: `madden26_<matchup>_<idx>.mp4` (e.g., `madden26_lac_vs_ari.mp4`, `madden26_kc_vs_buf.mp4`). The .gitignore rule already covers `*.mp4` in this dir.

### Risk: clip availability

Public YouTube footage of Madden 26 ranked matches is plentiful. If a primary URL is removed between commit time and regeneration, the documented alternate URL covers it. If both 404, the script prints a clear error pointing the contributor at the methodology doc to find a new clip with similar properties.

### Risk flag (per user)

If multi-source data sourcing takes >0.5 day (e.g., yt-dlp signed-in requirements, region blocks, mass clip removals), flag in a status update and propose single-source-with-augmentation fallback. Do not silently shrink the matchup count.

## Sub-task 2 — Frame labeling

**Estimate:** 1 working day. **This is the most underestimated step in ML projects** — being honest about it.

### Labeling tool design (specified before Day 1)

**Path**: `scripts/hud_calibration/label_formations.py`. ~120 lines, OpenCV-based, **keyboard-only — no mouse navigation, no separate viewer apps, no typed labels**.

**Per-frame target: ≤ 20 seconds**. With 1,400 frames and 8 working hours (28,800 seconds), 20 s/frame is the budget. The tool design is built around that constraint.

#### Required behaviour

1. **Pre-load all candidate frames into memory at startup.** Downsample to 960×540 (8-bit BGR, ~1.5 MB each → 2 GB for 1,400 frames at full res; downsample → 200 MB, fits in memory). Avoids per-frame disk I/O during labeling.
2. **One frame on screen at a time, full-screen via `cv2.namedWindow(..., cv2.WND_PROP_FULLSCREEN)`.** Frame index + total + current label shown as overlay text.
3. **Keymap (single keypress → immediate save + advance):**

   | Key | Action |
   | --- | --- |
   | `1` | Label as `shotgun_trips`, write CSV row, advance to next |
   | `2` | Label as `shotgun_bunch`, write, advance |
   | `3` | Label as `shotgun_empty`, write, advance |
   | `4` | Label as `i_form_pro`, write, advance |
   | `5` | Label as `singleback_ace`, write, advance |
   | `6` | Label as `pistol_strong`, write, advance |
   | `7` | Label as `shotgun_doubles`, write, advance |
   | `8` | Label as `singleback_wing`, write, advance |
   | Space | Skip frame (label_quality=`skip`, doesn't enter training set), advance |
   | `←` (arrow) | Backtrack: revisit previous frame; the next labeling action overwrites its previous label |
   | `→` (arrow) | Skip ahead (don't write a label); useful if a frame range is irrelevant |
   | `m` | Mark current frame as `medium`-quality (still labeled with last keyed class but flagged for review) |
   | `q` | Save and quit |

4. **Incremental CSV writes** — every label keypress appends a row to `formation_labels.csv` immediately. A crash mid-session loses at most 1 frame's worth of work.
5. **CSV schema**:
   ```
   clip,frame_idx,ts_sec,formation_class,label_quality
   madden26_lac_vs_ari,4400,73.40,kickoff,skip
   madden26_lac_vs_ari,4538,75.71,shotgun_trips,high
   ```
6. **Resume support** — if `formation_labels.csv` already exists, load existing labels at startup and skip already-labeled frames.

#### Candidate frame selection (pre-tool)

Before the labeling tool runs, a separate `scripts/hud_calibration/sample_pre_snap_candidates.py` script scans each source clip and emits candidate pre-snap frame indices. Heuristic:

- Sample every 30 frames (≈0.5 s at 60 fps).
- Reject frames where the bottom HUD band is missing (`central_std < 50` per the M4.5 detector).
- Reject frames where motion vector magnitude is high (uses `cv2.calcOpticalFlowPyrLK` between consecutive samples; high motion = mid-play, not pre-snap).
- Output: ~2,000 candidate frames across all clips.

The labeling tool consumes this candidate list. ~30% are skipped during labeling (false positives from the heuristic), yielding ~1,400 high+medium quality labels.

#### Per-frame target validation

**If average labeling time exceeds 30 seconds per frame within the first 50 labeled frames, flag as a Day 1 blocker.** Two responses:

1. **Reduce per-class target** from 175 to 100 frames (= 800 total). Acceptable per the spec's "≥ 0.85 macro-F1 at v0.1 with top-8". MobileNetV3-Small can converge with that volume given ImageNet pretraining.
2. **Extend labeling window** to 1.5 working days. Pushes M5c calendar to 6 working days. Status update to user.

User decides between (1) and (2). Default if no response: option (1) (faster, preserves 5.5-day calendar).

#### Output

- `agents/capture/fixtures/real/formation_labels.csv` — committed to PR #62.
- `scripts/hud_calibration/label_formations.py` — committed.
- `scripts/hud_calibration/sample_pre_snap_candidates.py` — committed.

### Estimated frames + labeling time

- **Target labeled set**: ~1,400 frames after filtering for label quality.
- **Candidate frames inspected**: ~2,000 (some skipped as ambiguous / not pre-snap).
- **Per-frame label time**: 8–15 seconds (faster on clear formations, longer on ambiguous ones — `pistol_strong` vs `singleback_strong` is genuinely close).
- **Honest total**: 6–8 working hours including breaks. ≈ 1 full working day.

### Quality control

- **Spot-check protocol**: re-label 10% of frames (~140) blindly two days later; compute agreement. Target ≥ 90% intra-annotator agreement.
- **Ambiguous-formation log**: any frame flagged as "medium" quality stays in the dataset but goes into a "discuss" bucket. If >5% of training frames are medium, the formation taxonomy or per-class definition needs sharpening before training.
- **Per-class minimum**: ≥ 100 frames per class. If any class falls short, label more before split (sub-task 3).

### Risk flag (per user)

If labeling exceeds 1.5 days, flag as a status update. Common cause: too-aggressive candidate-frame heuristic (too many false-positive pre-snap candidates rejected). Fix: tighten the candidate selector first.

## Sub-task 3 — Train/validation/test split

**Estimate:** 0.25 day.

### Disjoint splits, no game-level leakage

**Split by clip (not by frame).** Frame-level splits leak because consecutive frames within a play are visually nearly identical. Match-level splits prevent the classifier from memorizing a specific stadium / jersey / camera angle.

- **70% train / 15% val / 15% test** by clip count.
- With 5–8 clips: 4–6 train, 1 val, 1 test.
- Test-set clip is held-out from training entirely; training never sees its frames.

### Class balance per split

Stratified sampling: each split must have ≥ 15 examples per class. With 1,400 total:
- Train: ~980 frames, ≥110 per class.
- Val: ~210 frames, ≥25 per class.
- Test: ~210 frames, ≥25 per class.

If a class is underrepresented after the clip-level split, oversample within the train set during training (no test-set oversampling — that would inflate measured F1).

### Output artifact

`agents/capture/fixtures/real/formation_split.json`:

```json
{
  "version": "1.0.0",
  "train_clips": ["madden26_lac_vs_ari", "madden26_kc_vs_buf", ...],
  "val_clips": ["madden26_..."],
  "test_clips": ["madden26_..."],
  "per_split_class_counts": {"train": {"shotgun_trips": 124, ...}, ...}
}
```

## Sub-task 4 — Training pipeline

**Estimate:** 1 day.

### Location

`services/visionaudioforge/training/` (new directory).

```
services/visionaudioforge/training/
├── __init__.py
├── train_formation.py        # main training entry point
├── dataset.py                # FormationDataset (CSV-driven)
├── augment.py                # transforms (rotation, brightness; NO h-flip)
├── export_onnx.py            # PyTorch → ONNX with parity check
└── eval_formation.py         # used by sub-task 5
```

### Architecture

**MobileNetV3-Small** from `torchvision.models.mobilenet_v3_small(pretrained=True)`. Replace final classifier (1000-way ImageNet head) with 8-way head. Freeze the early feature extractor for the first 5 epochs; unfreeze for fine-tuning.

### Hyperparameter starting points

| Param | Value | Rationale |
| --- | --- | --- |
| Optimizer | Adam | Standard for transfer learning |
| LR | 1e-3 | With ReduceLROnPlateau on val_macro_f1 |
| Batch size | 32 | Fits comfortably on CPU + small GPU |
| Epochs | 30 max | Early-stop on val plateau |
| Image size | 224×224 | Standard MobileNetV3 input |
| Augmentation | rotation ±5°, brightness ±15%, color jitter ±0.05, **no horizontal flip** | Formation orientation is left/right-meaningful (e.g., trips-left vs trips-right) |
| Class-weighted loss | Yes if any class < 100 examples in train | CrossEntropyLoss with weights = inverse frequency |

### ONNX export with verification

`export_onnx.py`:

1. Load best-val checkpoint.
2. `torch.onnx.export(..., opset_version=17, dynamic_axes=None, do_constant_folding=True)`.
3. Output to `services/visionaudioforge/app/adapters/madden26/models/formation_v0_1.onnx`.
4. **Parity check** (this is non-negotiable per the user's silent-divergence flag):
   - Load both PyTorch model (eval mode) and ONNX session (CPUExecutionProvider).
   - Run inference on 50 random test-set frames.
   - Assert `max(abs(pytorch_logits - onnx_logits)) < 1e-4` per frame.
   - If divergence > tolerance, FAIL and stop. Common causes: BatchNorm in train mode during export, dynamic shape issues, opset incompatibility.

### Reproducibility

- `torch.manual_seed(42)`, `numpy.random.seed(42)`, `random.seed(42)`.
- `torch.use_deterministic_algorithms(True)` — may slow training slightly; worth it for repeatability.
- Pin PyTorch + torchvision exact versions in `services/visionaudioforge/requirements.txt`.
- Save `train_log.json` with: hyperparams, per-epoch train/val loss + F1, final test F1, environment hash (Python version, torch version, GPU model if applicable).

### Risk flag (per user)

If 20 ms p95 inference budget is unreachable on real footage:
1. Try the spec's documented fallback: drop input from 224×224 to 192×192 (Doc #02 §"Per-frame budget" §308).
2. If still over, try MobileNetV3-Small **fp16** ONNX (needs ORT-with-CUDA on production though).
3. If still over after both, **stop and propose superseding ADR** with measured numbers per the constraint. Do not silently relax the budget.

## Sub-task 5 — Acceptance evaluation

**Estimate:** 0.5 day.

### Metrics

`services/visionaudioforge/training/eval_formation.py`:

- **Macro-F1** across all 8 classes (primary acceptance metric, target ≥ 0.85).
- **Per-class precision, recall, F1** — surfaces class-imbalance issues.
- **Confusion matrix** (8×8) saved as PNG and as JSON (raw counts).
- **Inference latency** measured on CPU (the v0.1 deployment target):
  - 50 trials per frame size (224×224, plus 192×192 if fallback needed).
  - Report p50, p95, p99 in ms.
  - Test against the **20 ms p95** budget from Doc #02 §"Per-frame budget".

### Output artifact

`agents/capture/fixtures/real/m5c_eval_report.json`:

```json
{
  "milestone": "M5c sub-task 5",
  "macro_f1": 0.87,
  "per_class": {
    "shotgun_trips": {"precision": 0.91, "recall": 0.88, "f1": 0.89, "support": 25},
    ...
  },
  "confusion_matrix": [[...], ...],
  "latency_ms": {"p50": 11.2, "p95": 17.4, "p99": 19.1, "n_trials": 50},
  "model_path": "services/visionaudioforge/app/adapters/madden26/models/formation_v0_1.onnx",
  "model_size_mb": 9.4,
  "git_lfs_required": false
}
```

### Acceptance gates

- macro-F1 ≥ 0.85 (per spec).
- Inference latency p95 ≤ 20 ms (per ADR 0006 + Doc #02 budget).
- No class with F1 < 0.65 (catches class-imbalance leakage).

### If acceptance fails

- macro-F1 between 0.78–0.84: expand training data in worst class; retrain (cost: +1 day).
- macro-F1 < 0.78: structural issue (label noise, class collision). Stop; report; user decides.
- Latency over budget: try input-size fallback (192×192). If still over, see "Risk flag" in sub-task 4.

## Sub-task 6 — Temporal consistency infrastructure

**Estimate:** 1 day. **This is the field_position remediation that closes M4.5's last gap.**

### Design

New module `services/visionaudioforge/app/core/temporal.py`. Title-agnostic `TemporalSmoother` class. Tracks rolling windows of recent values per (session, field) pair and applies a smoothing function.

```python
class TemporalSmoother:
    """Title-agnostic per-session value smoother.

    Handles two value families:
      - Categorical (formation, possession): mode/majority-vote across window.
      - Numeric (field_position, distance, score): median across window.

    Per-field configuration: window_size, value_kind, min_window_for_emit.
    Each adapter declares its smoothing schema; dispatcher applies it
    between adapter output and event emission.
    """
```

### Where it lives

Wired into `Dispatcher.process_frame` between the adapter's `process_frame` call and event emission. Adapter declares its smoothing schema as a class attribute:

```python
class Madden26Adapter:
    smoothing_schema = {
        "offensive_formation": {"kind": "categorical", "window": 5, "min_window": 3},
        "field_position":      {"kind": "numeric",     "window": 7, "min_window": 4},
        "score_home":          {"kind": "numeric",     "window": 3, "min_window": 1},
        "score_away":          {"kind": "numeric",     "window": 3, "min_window": 1},
        "down":                {"kind": "categorical", "window": 5, "min_window": 3},
        "distance":            {"kind": "numeric",     "window": 5, "min_window": 3},
        "play_clock":          {"kind": "numeric",     "window": 3, "min_window": 1},
        "clock":               {"kind": "string_clock", "window": 3, "min_window": 2},
        # team abbrevs: NOT smoothed — they don't change mid-game.
    }
```

#### Clock smoothing rationale (per user item 4 sign-off)

**Decision: smooth clock with window=3, min_window=2.** The earlier plan's "clock NOT smoothed" was wrong — both rationales the user listed apply but neither prevents smoothing:

1. **Reliability rationale (clock at 85.7% in M4.5)**: real, but smoothing the 1↔7 misread fixes the wrong-but-valid value problem the same way it does for field_position. A 3-frame window catches single-frame OCR errors via mode-of-strings logic without affecting normal ticks.
2. **Lag rationale**: at 60 fps capture, a 3-frame window introduces 50 ms (3 frames × ~16 ms) of effective lag. The game clock ticks once per second (1,000 ms). 50 ms lag on a value that updates every 1,000 ms is below human-perception threshold and well below the >2 s end-to-end latency budget in Doc #02 §"Per-frame budget".

The `string_clock` smoothing kind is purpose-built: takes the mode of the last N parsed clock strings ("3:18" / "3:17" / etc). When the read is monotonically decreasing (normal ticking), mode trails by 1 frame — fine. When a frame mis-reads "3:18" as "3:78", the mode of [3:18, 3:78, 3:17] = (no mode → fall back to median by parsed seconds → 3:17 / 3:18). Concrete logic in the methodology doc.

The methodology doc explains both rationales so future adapters know when smoothing is wrong (e.g., for SCORE_CHANGE event timestamps — those are one-shot, never smoothed).

### Integration with field_position

The dispatcher applies smoothing to the OCR output before it enters the event payload. This is the same path field_position takes — so the M4.5 gap closes for free. The exact frame where EasyOCR misreads "+41" as "+47" gets median-filtered out by the surrounding 6 frames that read "+41" correctly.

### Title-agnostic

The smoother lives in `core/`, not in any adapter. Future adapters (CFB 26, NBA 2K26, EAFC 26) declare their own `smoothing_schema` — no other code change. Verifies Forge Rule 5 (adapters added without core changes).

### Re-run M4.5 OCR validation with smoothing

Add `--temporal-smoothing` flag to `scripts/hud_calibration/validate_ocr.py`. With smoothing enabled, run on the same 7 play-state frames extended to 7-frame windows (sample neighbouring frames). Verify:

- field_position success rate climbs from 71.4% to ≥ 80%.
- No regression in the other 9 elements.

### Methodology doc

`docs/integrations/visionaudioforge/temporal-consistency-pattern.md`. Explains:

- When to smooth (categorical: classifier outputs prone to single-frame errors; numeric: OCR readings with bounded change rate).
- When NOT to smooth (high-frequency change like game clock ticks; one-shot events like SCORE_CHANGE).
- How to pick window size (proportional to expected change rate × tolerance for staleness).
- How to wire `smoothing_schema` for a new adapter.

Reusable pattern for every future title.

### Risk flag (per user)

If temporal smoothing introduces measurable lag visible to consumers (e.g., SCORE_CHANGE event fires 5 frames late), tune per-field windows down. The schema makes per-field tuning a 1-line change.

## Sub-task 6.5 — Smoothing regression check (NEW per user item 5)

**Estimate:** 0.5 day. **This is the gate before sub-task 7.** No Phase 0 final validation runs until smoothing is regression-free.

### What it does

Re-run the M4.5 OCR validation harness twice with explicit control:

1. **Smoothing OFF** — `validate_ocr.py --temporal-smoothing=off` (control). Confirms M4.5 baseline numbers reproduce on the post-M5c codebase. If any element regresses below its M4.5 success rate, **stop** — non-smoothing changes broke something downstream.
2. **Smoothing ON** — `validate_ocr.py --temporal-smoothing=on`. Confirms field_position climbs from 71.4% to ≥ 80%, and confirms no other element falls below its M4.5 baseline.

### Acceptance gates

- **Smoothing OFF baseline matches M4.5 within ±2%** per element. Within-noise tolerance — different OCR pre-runs may vary slightly due to non-determinism in EasyOCR's recognition, but a >2% drop signals a real regression.
- **Smoothing ON: field_position ≥ 80%** (closing the M4.5 gap).
- **Smoothing ON: no element regresses** below its smoothing-OFF baseline. If smoothing reduces an element's success rate (e.g., if smoothing windows are too aggressive and over-smooth), tune that element's window down and retry.

### Output artifact

`agents/capture/fixtures/real/m65_smoothing_regression.json`:

```json
{
  "milestone": "M5c sub-task 6.5",
  "smoothing_off": {
    "team_home_abbr": 100.0,
    ...
    "field_position": 71.4
  },
  "smoothing_on": {
    "team_home_abbr": 100.0,
    ...
    "field_position": 85.7
  },
  "regressions": [],   // empty if all elements held or improved
  "field_position_passes_80": true
}
```

### Methodology doc captures findings

The temporal-consistency methodology doc (`docs/integrations/visionaudioforge/temporal-consistency-pattern.md`) gets a "Tested interactions" section listing any unexpected behaviour:

- Did clock smoothing introduce visible lag in any test frame?
- Did smoothing windows interact with the OCR variant chain in unexpected ways?
- Are there field combinations where smoothing one breaks another (e.g., score_home median being inconsistent with score_away median across the same window)?

Document each finding even if benign — the next adapter author needs to know.

### If regression found

**Stop. Do NOT proceed to sub-task 7.** Diagnose:

- If single-element regression: tune that field's smoothing window. Re-run regression check.
- If broad regression: rollback temporal smoother integration. Investigate dispatcher integration path. Re-deploy without smoothing. Re-run smoothing-OFF baseline.

Time-box debug to 0.5 day. If unfixable in that window, escalate to user — temporal infrastructure may need deeper rework before Phase 0 closes.

### Status check (NEW per user item 8)

After this sub-task lands a commit, status check before sub-task 7 begins:

- Smoothing ON vs OFF comparison numbers per element
- field_position regression test result (pass/fail vs 80% bar)
- Any unexpected interactions found

User signs off on smoothing infrastructure before sub-task 7 begins. No Phase 0 final-validation work proceeds without that approval.

## Sub-task 7 — Real-footage validation against Phase 0 acceptance

**Estimate:** 0.5 day.

Re-runs `agents/capture/real_footage_harness.py` end-to-end after sub-tasks 4, 5, 6 land. Validates each of the 8 original Phase 0 acceptance criteria with measured evidence.

### Phase 0 criteria checklist

| # | Criterion | How verified | Pass/fail |
|---|---|---|---|
| 1 | VAF core service boots, exposes `/api/v1`, `/ws/*` routes | `curl http://127.0.0.1:8100/health` returns 200; route inventory matches spec | TBD |
| 2 | Capture agent connects, streams JPEG batches, receives session_open handshake | `agents/capture/capture_agent` connects to core; smoke test logs handshake | TBD |
| 3 | EventEnvelope shape validates against discriminated-union contract | Pydantic discriminator passes on every emitted event | TBD |
| 4 | Title detection locks via primary path (heuristic + signature) on real HUD frames | Test with hint disabled; verify heuristic + ORB fallback exercised | **Critical — needs hud_signature.png curation as part of M5c (or noted gap)** |
| 5 | Adapter per-frame latency p95 ≤ 80 ms on real footage | Measured by harness; latency_percentiles() | TBD |
| 6 | OCR pipeline reads HUD regions accurately | M4.5 + temporal smoothing closes this | TBD (expecting 10/10 with smoothing) |
| 7 | Events emitted at expected per-frame cadence | Harness reports frames_dispatched vs events_emitted | TBD |
| 8 | ORB fallback + Madden/CFB tiebreaker exercised on at least one real-footage path | Test with hud_signature.png present + hint absent | Same as #4 — depends on signature curation |

### Output artifact

`agents/capture/fixtures/real/phase0_final_validation.json`:

```json
{
  "milestone": "Phase 0 close",
  "harness_run": {...},
  "criteria": {
    "1": {"description": "...", "status": "pass", "evidence": "..."},
    ...
    "8": {...}
  },
  "all_pass": true | false
}
```

### What happens if criterion 4 / 8 don't pass

Criteria 4 and 8 require `hud_signature.png` files for at least Madden 26 (and ideally CFB 26 as the tiebreaker partner). Approved per user item 7: **bundle hud_signature curation into sub-task 7 (~0.25 day)**.

The work is small — pull a 200×80 crop of the stable HUD-band region (EA SPORTS / MADDEN logo on the bottom-left) from a calibration frame, save as `services/visionaudioforge/app/adapters/madden26/hud_signature.png`, validate that the title detector now locks via the heuristic path on a real-footage frame.

### Awareness — sub-task 7 slippage handling (per user item 7)

If hud_signature curation slips beyond 0.25 days (e.g., signature crop fails to lock detection on real frames, requires multi-frame averaging, or reveals a cross-resolution scaling issue), **escalate as sub-task 7a with its own time estimate**. Do **NOT** silently compress sub-task 7's other work (criteria 1–3, 5–7 verification) to absorb the slip.

Sub-task 7a, if it happens, gets:

- Its own commit on PR #62.
- Its own status update.
- A revised end-of-M5c-calendar number reflecting the slip.

This is the same discipline as M4.5: when work expands beyond estimate, the calendar moves, not the deliverable scope.

### Acceptance gates

- All 8 criteria status = "pass".
- Measured numbers documented inline.
- One status report committed to PR #62 alongside the validation JSON.

## Risks (consolidated)

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Multi-source clip sourcing fails | Higher overfit risk on single match | Single-source + heavy augmentation fallback. Flag to user before proceeding. |
| Labeling exceeds 1.5 days | Calendar slip | Status update at end of day 1; offer to reduce target frames per class to 100. |
| macro-F1 lands 0.78–0.84 | Below acceptance | Expand training data in worst class; retrain (+1 day). |
| ONNX divergence from PyTorch | Silent production breakage | Hard-fail parity check in export step. |
| 20 ms inference budget unreachable | Spec violation | Try 192×192 fallback; if still over, propose superseding ADR with measured rationale. |
| Temporal smoothing introduces user-visible lag | Bad UX | Per-field window tuning; verify no SCORE_CHANGE delays > 1 frame. |
| Criteria 4/8 require hud_signature curation | Phase 0 acceptance blocked | Bundle signature curation into sub-task 7 (0.25 day). |

## Status check cadence

Per the user's gating workflow (revised with item 8 — new check after sub-task 6.5):

| When | What user sees | Decision needed |
|---|---|---|
| After sub-task 2 commits | Labeled dataset stats, per-class counts, label-quality distribution | Approve to start training |
| After sub-task 4 commits | Training/validation loss curves, sanity-check inference on 5–10 real frames | Approve to start evaluation |
| After sub-task 5 commits | macro-F1 number + confusion matrix + per-class P/R + latency report | Approve to start temporal-consistency work |
| **After sub-task 6.5 commits (NEW)** | Smoothing ON vs OFF comparison; field_position regression test result; any unexpected interactions | **Approve smoothing infrastructure → start sub-task 7** |
| After sub-task 7 commits | Full Phase 0 acceptance status report (all 8 criteria) | Sign off Phase 0 closure → PR #62 + #63 ready for merge |

End-of-session standup at every work-session close, regardless of sub-task boundary.

## Constraint compliance summary

| Constraint | Compliance |
|---|---|
| Branch: `feat/visionaudioforge-phase-0` (PR #62) | ✓ All commits target this branch |
| Single commit per sub-task, conventional commits | ✓ 7 commits planned |
| Each commit references milestone + sub-task + spec/ADR | ✓ Pattern from M4.5 commit; same structure |
| Test coverage ≥80% adapter, ≥60% core | ✓ New unit tests for `temporal.py` + `formation_detector.py` |
| ONNX > 25 MB → Git LFS | MobileNetV3-Small ≈ 9 MB; LFS not needed unless quantization adds debug data |
| Temporal infrastructure title-agnostic | ✓ Lives in `core/`, schema-driven |
| 20 ms budget preserved | ✓ Spec table unchanged; budget enforced in eval, escalation path documented |

## Sign-off path

1. User reviews this plan.
2. User approves OR requests adjustments to:
   - Frame target (1,400 → another number)
   - Multi-source vs single-source
   - Smoothing schema initial values
   - Sub-task ordering
   - Inclusion of hud_signature curation in sub-task 7
3. User approves.
4. Sub-task 1 begins.

No implementation work starts before step 3.
