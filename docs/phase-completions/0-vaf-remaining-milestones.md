# Phase 0 — Remaining Milestones

- **Status:** Plan, not yet started. Implementation begins after sign-off.
- **Date:** 2026-05-07
- **Source:** Pre-merge review of PR #62 / PR #63. Real-footage validation surfaced 5 failed acceptance criteria; this doc breaks the remaining work into committable milestones that close them.
- **Reference:** [Phase 0 status doc](0-vaf-foundation.md), [real-footage validation report](0-real-footage-validation.md), [ADR 0006 — tiered per-frame budget](../adr/0006-tiered-per-frame-budget.md), [ADR 0007 — title detection fallback](../adr/0007-title-detection-fallback.md), [Madden 26 adapter spec](../specs/02-visionaudioforge-core.md).

## Scope

Five sequenced milestones. Each commits to PR #62 incrementally. After the final milestone, real-footage validation re-runs and Phase 0 acceptance returns.

| # | Milestone | Estimate | Closes acceptance criteria | Depends on |
|---|---|---|---|---|
| 1 | **M4.5 — HUD region calibration** | 3 days | 6 (OCR readings) | — |
| 2 | **M5c — Real formation classifier training** | 3–5 days | 4 (title primary path), 8 (ORB / tiebreaker on real) | M4.5 (correct crops) |
| 3 | **OCR cadence reform** | 1 day | 5 (latency p95), 7 (event emission) | M4.5, M5c |
| 4 | **Real-footage validation re-run** | 0.5 day | All 8 (verification) | 1, 2, 3 |
| 5 | **Phase 0 status doc → completion sign-off** | 0.5 day | — | 4 |

**Total: 8–10 working days.** Sequential by default — calendar shifts only if a milestone slips.

The ADR 0006 80 ms per-frame budget is **not** revised. The original budget was set with knowledge of expected OCR + classifier costs. Real EasyOCR-on-CPU at ~30 ms × 8 regions per frame violates the budget by an arithmetic that the design never tolerated; the response is to fix the OCR approach (Milestone 3), not to relax the contract. If, after Milestones 1–3, the budget is genuinely unreachable, a superseding ADR is the right move at that time. Not before.

---

## Milestone 1 — M4.5: HUD region calibration

**Estimate:** 3 days

**Why:** real-footage validation showed 3 of 5 sampled OCR reads returning all-null. `hud_regions.json` was authored from spec, not from measured frames; the bbox coordinates do not align with Madden 26's actual HUD.

**Closes:** acceptance criterion 6 (OCR readings on real HUD).

### Day 1 — capture & label

- Pull 5 representative frames from `agents/capture/fixtures/real/madden26.mp4`:
  - Frame A: pre-snap, scoreboard fully visible.
  - Frame B: mid-play, score visible, down/distance changing.
  - Frame C: post-score (scoreboard refresh).
  - Frame D: halftime (scoreboard format may differ).
  - Frame E: replay (HUD may animate or fade).
- For each frame, hand-outline every subregion in an annotation tool: `team_home_abbr`, `score_home`, `team_away_abbr`, `score_away`, `quarter`, `clock`, `down`, `distance`, `field_position`, `play_clock`, `formation_overlay_pre_snap`.
- Store the labels as `agents/capture/fixtures/real/hud_calibration_frames.json` — pixel coordinates per region per frame.

### Day 2 — regenerate hud_regions.json

- Compare per-frame labels; choose the bbox that fits all 5 frames (typically the union or the most conservative crop).
- Update `services/visionaudioforge/app/adapters/madden26/hud_regions.json` with the calibrated coords.
- Write a unit test in `services/visionaudioforge/tests/test_hud_regions.py` that loads each calibration frame and asserts each subregion crops to a non-empty image with expected aspect-ratio bounds.

### Day 3 — validate

- Run `real_footage_harness.py --max-frames 50 --frame-stride 12` (≈4 seconds of footage).
- Acceptance: ≥ 3 of 5 sampled OCR snapshots return at least 4 of `score_home`, `score_away`, `quarter`, `clock`, `down`, `distance` as non-null.
- If acceptance fails, iterate on bbox coords from Day 1 labels.

**Commit plan:**

- One commit on `feat/visionaudioforge-phase-0`: `feat(madden26): calibrate hud_regions.json against real footage (M4.5)`. Files: `hud_regions.json`, `tests/test_hud_regions.py`, `agents/capture/fixtures/real/hud_calibration_frames.json` (calibration labels — small JSON, OK to commit).

**Deliverables:**

- Updated `hud_regions.json` with measured coordinates.
- Calibration label file checked in.
- Unit test enforcing region validity.
- Day-3 harness output snippet pasted into the M4.5 PR comment showing OCR success rate.

### M4.5 status — actual numbers (2026-05-07)

10 HUD-bearing frames calibrated (3 kickoff, 7 play). OCR success rate per element on play-state frames:

| Element | Success rate (play state) | vs. 80% bar |
| --- | --- | --- |
| `team_home_abbr` | **100%** (7/7) | ✅ |
| `team_away_abbr` | **100%** (7/7) | ✅ |
| `score_home` | **100%** (7/7) | ✅ |
| `score_away` | **100%** (7/7) | ✅ |
| `quarter` | **100%** (7/7) | ✅ |
| `clock` | **85.7%** (6/7) | ✅ |
| `play_clock` | **85.7%** (6/7) | ✅ |
| `down` | **100%** (7/7) | ✅ |
| `distance` | **100%** (7/7) | ✅ |
| `field_position` | **71.4%** (5/7) | ❌ — below 80% |

**9 of 10 elements meet the M4.5 acceptance threshold.** One (`field_position`) is at 71.4% — below the 80% bar.

**Why field_position misses:** EasyOCR systematically reads Madden 26's stylized `1` digit as `7` in two of seven play-state frames (5900: `+41` reads as `+47`; 7000: `+10` reads as `+70`). The wrong reading is itself a valid yard-line value (47 and 70 are both legal field positions), so no parser variant logic can recover the correct value. The same digit confusion affected `clock` and `play_clock` on frame 5900 (recovered for clock and play_clock by the variant fallbacks; `field_position` has no equivalent fallback because its valid range covers all confusion outcomes).

**Path forward (M5c-adjacent):**

1. **Multi-frame temporal consistency** — field_position changes ≤1 yard per real-time second. Aggregating reads across consecutive frames + rejecting outliers (median filter) would catch the 1↔7 flips. Adds ~50 lines to `Madden26Adapter.process_frame`. Recommended for M5c.
2. **Custom digit classifier** — train a 10-class CNN on Madden's stylized digits. ~1 day if labels are bootstrapped from the calibration frames (currently labeled). Higher-quality fix; addresses similar issues in other adapter HUDs.

**Recommendation:** treat M4.5 as 9/10 complete. Land this commit. Open a status-check question to user: accept 71.4% on field_position with the M5c temporal-consistency follow-up, or block on a custom digit classifier before M5c kicks off.

Other M4.5 deliverables done:
- `hud_regions.json` v2.0.0 with measured Madden 26 bottom-band coordinates (was at top in v1.0.0 spec).
- 10 calibration frames committed at `scripts/hud_calibration/frames/frame_*.png`.
- `scripts/hud_calibration/{sample_frames,sample_dense_gameplay,extract_hud_strip,annotate_bboxes,validate_ocr}.py` — reusable templates for the next title's calibration.
- `agents/capture/fixtures/real/m45_ocr_validation.json` — full per-frame, per-element evidence.
- `docs/integrations/visionaudioforge/madden26-hud-calibration-methodology.md` — methodology for CFB 26, NBA 2K26, etc.
- OCR pipeline updates: parser variant chains for Madden's "1↔7" font confusion, CLAHE+5× preprocessing, ordinal text handling, play_clock plumbing, field_position regex anchored to trailing digits.

---

## Milestone 2 — M5c: Real formation classifier training

**Estimate:** 3–5 days

**Why:** the Phase 0 stub returns `shotgun_trips`/0.5 regardless of input. Real `FORMATION_LOCKED` events require a working 8-class classifier per the Madden adapter spec.

**Closes:** acceptance criterion 4 (real title detection path can use the assembled-event content), criterion 8 (ORB fallback + tiebreaker on real frames — exercised once the real classifier produces stable scores against varied formations).

### Day 1 — training set construction

- Hand-label ~250 pre-snap formations from `madden26.mp4` plus 1–2 additional public clips. Goal distribution: ≥25 examples per class across the 8 v0.1 formations:
  `shotgun_trips, shotgun_bunch, shotgun_empty, i_form_pro, singleback_ace, pistol_strong, shotgun_doubles, singleback_wing`.
- Crop each pre-snap frame to the `formation_overlay_pre_snap` region (using M4.5 bbox).
- Write labels to `agents/capture/fixtures/real/formation_labels.csv` (frame_idx, formation_class, source_clip).

### Day 2 — train MobileNetV3-Small

- Transfer-learning from ImageNet weights. Single-GPU Colab is sufficient for 8 classes × 250 frames.
- Resize crops to 224×224, standard augmentations (rotation ±5°, brightness ±15%, horizontal flip OFF — formation orientation matters).
- Train 30 epochs; early-stop on validation macro-F1 plateau.

### Day 3 — validate macro-F1 ≥ 0.85

- Held-out 50-frame test set (not seen during training).
- Acceptance: macro-F1 ≥ 0.85 on the test set.
- If first run lands at 0.75–0.84: expand training set by ~50 more labels in the worst-performing classes; retrain. **Do not over-tune hyperparameters.**
- If first run < 0.75: stop, escalate. Possible root causes: wrong crop, mislabeled training set, class imbalance.

### Day 4 — ONNX export + integration

- Export to `services/visionaudioforge/app/adapters/madden26/models/formation_v0_1.onnx`.
- Wire into `FormationDetector.detect_offensive`: load model lazily on first call (same lazy-load pattern as EasyOCR), run inference, argmax + softmax → `FormationReading`.
- Add unit test `services/visionaudioforge/tests/test_formation_detector.py` that loads a known crop, runs the model, asserts a known-class output.

### Day 5 — adapter end-to-end test (buffer)

- Run `real_footage_harness.py` with the real classifier integrated.
- Verify FORMATION_LOCKED events fire with confidence ≥ 0.85 on visible formations.
- Hand-verify ≥ 3 formations match the visual ground truth.
- If anything's off, this day is the buffer for a re-train or label-cleanup pass.

**Commit plan:**

- Commit 1: `feat(madden26): add formation classifier training script (M5c)`. Files: `scripts/train_formation_classifier.py`, `agents/capture/fixtures/real/formation_labels.csv`.
- Commit 2: `feat(madden26): integrate formation_v0_1.onnx into adapter (M5c)`. Files: `services/visionaudioforge/app/adapters/madden26/models/formation_v0_1.onnx` (binary — committed via Git LFS if > 5 MB; expected ~7 MB), `formation_detector.py`, `tests/test_formation_detector.py`.

**Deliverables:**

- Trained ONNX model, version-controlled.
- Training script reproducible from labels CSV.
- Macro-F1 number recorded in the M5c PR comment.
- Hand-verified formation predictions on ≥ 3 real frames.

---

## Milestone 3 — OCR cadence reform

**Estimate:** 1 day

**Why:** real-footage validation showed adapter p50 = 250 ms with EasyOCR running on every frame across 8 regions. The 80 ms ADR 0006 budget is unachievable when 8 OCR calls fire per frame at ~30 ms each. The fix is structural: don't run OCR on every frame.

**Closes:** acceptance criterion 5 (adapter p95 ≤ 80 ms), criterion 7 (events emitted at expected cadence — events stop dropping when latency drops below budget).

### Approach

The HUD updates at human-perceptible rates: clock ticks once per second, down/distance changes once per play (every 25–40 s), score changes ~once per drive. Per-frame OCR is wasteful by 1–2 orders of magnitude.

New cadence rule in `Madden26Adapter.process_frame`:

1. **Snap detector drives OCR.** When `SnapDetector.update` reports a `pre_snap` transition, OCR `down_distance` + `clock`. When it reports a `post_snap_complete`, OCR `scoreboard.score_*`.
2. **Cache last good readings in `session.adapter_state`.** Frames between OCR runs reuse the cached values.
3. **Emit DOWN_AND_DISTANCE / SCORE_CHANGE events only on cache mutation.** No more SNAPSHOTs every frame.

### Tasks

- Refactor `OCRPipeline.read_frame` into `OCRPipeline.read_regions(regions: set[str])` — caller specifies which regions to OCR.
- Update `Madden26Adapter.process_frame` to call `read_regions` conditionally on snap-state transitions.
- Add `session.adapter_state["last_ocr_snapshot"]` cache.
- Update tests in `tests/test_ocr_pipeline.py` (new) covering: targeted region read, cache hit/miss, score-change detection.

### Acceptance

- Run `real_footage_harness.py --max-frames 200 --frame-stride 5`.
- Adapter p95 latency ≤ 80 ms.
- Per-frame OCR call count averages ≤ 1 (vs. 8 before).
- Events emitted on real footage > 0 (target: ≥ 5 DOWN_AND_DISTANCE events across 200 frames).

### Fallback

If snap-event-triggered OCR doesn't land p95 ≤ 80 ms, escalate to **ONNX digit-classifier replacement** (5-class CNN per digit region; ~2 ms per region vs. ~30 ms). Adds 2–3 days. Decision goes to user; this milestone document is the trigger for that conversation.

**Commit plan:**

- One commit: `feat(madden26): snap-event-triggered OCR cadence (M-OCR-reform)`. Files: `ocr_pipeline.py`, `adapter.py`, `tests/test_ocr_pipeline.py`. Comment includes p95 measurement.

**Deliverables:**

- Refactored OCR pipeline with targeted-region API.
- Adapter wires the new cadence; cache lives in `session.adapter_state`.
- Tests covering happy path + cache invalidation.
- p95 latency number from `real_footage_harness.py` pasted into the PR comment.

---

## Milestone 4 — Real-footage validation re-run

**Estimate:** 0.5 day

**Why:** independent verification that Milestones 1–3 actually closed the 5 failed criteria.

**Closes:** all 8 criteria — verification step.

### Tasks

- Run `agents/capture/real_footage_harness.py --video agents/capture/fixtures/real/madden26.mp4 --max-frames 600 --frame-stride 5 --report agents/capture/fixtures/real/report_post_phase0_close.json`.
- Inspect the report against the 8 acceptance criteria:
  - 1, 2, 3: already passing — confirm they didn't regress.
  - 4: confirm signature path locks (or hint+heuristic combo); not just hint alone.
  - 5: p50, p95, p99 ≤ 80 ms.
  - 6: OCR success rate ≥ 60% across sampled snapshots.
  - 7: ≥ 5 events emitted across the run (FORMATION_LOCKED + DOWN_AND_DISTANCE).
  - 8: at least one frame triggers ORB fallback OR abbrev tiebreaker on real footage. If neither triggers naturally, hand-craft a frame that does (e.g., a frame where heuristic score is intentionally below 0.85).
- Hand-verify ≥ 3 formations match visual ground truth.
- Hand-verify ≥ 3 OCR readings (score / clock / down) match visual ground truth.

**Acceptance:** all 8 criteria pass. If any criterion still fails, return to its owning milestone and iterate.

**Commit plan:**

- One commit: `chore(phase-0): real-footage validation re-run results`. Files: `agents/capture/fixtures/real/report_post_phase0_close.json` (small JSON, OK to commit), updated `docs/phase-completions/0-real-footage-validation.md` appendix.

---

## Milestone 5 — Phase 0 status doc → completion sign-off

**Estimate:** 0.5 day

**Why:** with the validation passing, the status doc returns to a completion-sign-off state honestly.

### Tasks

- Edit `docs/phase-completions/0-vaf-foundation.md`:
  - Title: re-add "Completion" framing only after the user confirms acceptance.
  - 8-criteria table: every row green for both synthetic and real-footage columns.
  - Sign-off line: re-added by the user (not by Claude).
  - "What is NOT yet verified" section: removed.
  - "What happens next" section: replaced with Phase 1a kickoff link.
- Verify the [Phase 1a kickoff brief](../phase-kickoffs/1a-drill-lab-cutover.md) approvals checklist still reads cleanly with the new prerequisite.
- Verify the [Phase 1 timeline](../phase-kickoffs/phase-1-revised-timeline.md) reflects Phase 0 closing on this date and Phase 1a starting fresh.

**Commit plan:**

- One commit: `docs: Phase 0 completion sign-off (real-footage validation passed)`. This is the merge-ready commit for PR #63 (and PR #62 closes simultaneously).

**Deliverables:**

- Honest "Phase 0 Complete" status doc with measured-passing-criteria evidence.
- PR #62 + PR #63 in mergeable state.

---

## Risks and mitigations

| Risk | Probability | Mitigation |
|---|---|---|
| M5c macro-F1 lands at 0.78 (close, not passing) | Medium | Add ~50 labels in worst classes; retrain. Day 5 buffer absorbs this. |
| OCR cadence reform doesn't drop p95 below 80 ms | Low | Fallback to ONNX digit-classifier (+2–3 days). Decision goes to user. |
| Hand-labeling 250 frames takes longer than 1 day | Medium | Use the existing `agents/capture/real_footage_harness.py` to enumerate pre-snap candidates first; reduces frame-search time. |
| HUD bbox calibration disagrees across frame types (replay vs live) | Medium | Calibrate against the live frame; treat replay HUD as out-of-scope for v0.1 (document as Phase 2 work). |
| Real-footage validation re-run reveals a new criterion failure | Low | Each milestone's PR includes its own measurement; the re-run is a confirmation, not a discovery. |

## Out of scope for Phase 0 remainder

- Madden adapter v0.2 (defensive front) — Phase 1.1 work.
- Madden adapter v0.3 (post-snap coverage) — Phase 1.1 work, Phase 1c gating.
- CFB 26 adapter — Phase 2 work.
- Real screen-capture path (DirectShow / capture cards) for the agent — Phase 1 M1 final.
- VoiceForge integration — separate track.

## Sign-off path

This document is the plan; it does **not** authorise implementation. Implementation starts when:

1. The user reviews this milestone breakdown.
2. The user reviews the revised [Phase 0 status doc](0-vaf-foundation.md), [Phase 1 timeline](../phase-kickoffs/phase-1-revised-timeline.md), and [Phase 1a kickoff brief](../phase-kickoffs/1a-drill-lab-cutover.md).
3. The user signs off on the plan.

Then M4.5 starts on Day 1 of the next working session. Each milestone commits to PR #62 incrementally per its commit plan above.
