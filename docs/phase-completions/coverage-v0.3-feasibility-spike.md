# Coverage classifier v0.3 — feasibility spike

- **Question:** Is the Madden v0.3 post-snap coverage classifier (`detect_coverage` →
  `COVERAGE_LOCKED`, ADR 0010/0017) **plumbing** (wire the existing ~0.86 classifier into
  the adapter) or a **research arc** (the classifier won't survive live production frames)?
- **Date:** 2026-07-12
- **LATEST (2026-07-12) — superseded by BY-GAME validation:** the by-clip numbers below (and the
  T0/T1/T2 tier ladder in `coverage-v0.3-modeling-plan.md`) were all on ONE visual context and do
  **NOT** hold by game (near chance across every approach). Post-snap coverage-from-vision is a
  research arc; **the effort pivoted to OCR-of-play-call** (`coverage-ocr-playcall-pivot.md`). Read
  the below as the honest evolving record up to that point.
- **Verdict (was current — see VALIDATION RESULT below):** Two corrections landed on the original
  "research arc" call. **(1)** All-22 is a **live** camera (not replay-only, as originally
  assumed), which removes the *deployment* blocker. **(2)** But validating the classifier on the
  All-22 corpus (held-out **by clip**) gives macro-F1 **~0.45, not 0.86** — the 0.86 was a
  frame-level **leakage** artifact (the repo's own code flags it). So v0.3 is a **MODELING
  problem, not plumbing**: even on the ideal All-22 input, the current frozen-ResNet18 reader
  doesn't generalize to unseen plays. Do not wire it. The original analysis + the All-22
  correction are kept below as the honest evolving record.

## VALIDATION RESULT (2026-07-12) — the classifier does NOT hold up; the 0.86 was leakage

After the correction below (All-22 is live → "plausibly plumbing, pending validation on live
All-22"), the validation was run — the All-22 corpus was on the dev box after all
(`C:/Users/ivann/Videos/MaddenCaptures/madden26_coverage_cover{1..4}_*`, **120 clips**). Built
the frame dataset (`extract_coverage_frames.py`, 1152 frames) and evaluated **held-out by
clip**. The result overturns the headline number:

| Split | macro-F1 | Note |
|---|---|---|
| repo `crossval_coverage.py` (by-clip), **5-fold mean** | **0.45 ±0.04** | the repo's own honest CV (folds 0.42/0.51/0.48/0.46/0.39) |
| feature-cache leave-one-clip-out (full corpus) | **0.41** | ResNet18 frozen features + linear head |
| per-clip 80/20 | **0.39** | |
| batch-1 only (24 clips), by-clip LOO | **0.40** | not a "small clean set is better" story |
| **per-IMAGE 80/20 (leaky)** | **0.60** | frames from the same play in train AND test |
| coarse **1-high vs 2-high shell**, by-clip | acc **0.63** | vs 0.58 majority baseline — barely above chance |

**The honest held-out-by-clip macro-F1 is ~0.45, not 0.86** — far below the 0.85 target, and
even the *binary* safety-shell is near chance. The **0.86 came from a frame-level split**, which
`train_coverage.py`'s own code labels `"(LEAKS clips across split)"` and whose `clip_level_split`
comment calls clip-level *"the ONLY honest split for this data: ~6 frames/clip are near-identical,
so a frame-level split leaks a play's visual signature into val."* i.e. the 0.86 is a
memorization artifact of ~10 near-duplicate frames per play landing on both sides of the split.

**Revised verdict: v0.3 is a MODELING problem, not plumbing — and not blocked on the camera.**
Even with All-22 live (the best-case input, where the shell is fully visible), a frozen-ResNet18
+ linear-head reader on single post-snap frames does not generalize to unseen plays at this data
scale (120 clips). Do **not** wire the current classifier. Real paths forward (all unproven,
research-scale): substantially more clips (100s–1000s), a **temporal/multi-frame** model over the
whole post-snap rotation (not one frame), **pre-snap + post-snap fusion**, or backbone
fine-tuning (the docstring warns it overfits at this scale). Caveat: this probe used *frozen*
ImageNet features (no fine-tuning) — but that matches the classifier's own frozen-backbone
design, and the repo's by-clip CV agrees (0.42).

**Net across all three findings:** the camera-availability correction (All-22 is live) removed
the *deployment* blocker, but the validation shows the *model* itself doesn't work held-out. So
`COVERAGE_LOCKED` stays dormant (consumer seam already documented-silent), Gameplan-highlight
(1b) + Phase 1c stay gated (ADR 0010), and v0.3 needs a genuine data+modeling effort before it
is wireable. Reproduce: `agents/capture/{extract_coverage_frames,crossval_coverage}.py`.

## CORRECTION (2026-07-12): All-22 is a live camera — verdict revised

The spike's entire "research arc" conclusion hinged on the assumption *"the live PS5 feed
never produces an All-22 frame."* **That assumption was wrong** (asserted from general Madden
knowledge, not verified). The operator can select **All-22 as a live gameplay camera** (not
just a replay angle), and end users could too. Re-evaluating each blocker under that fact:

- **Blocker 1 (view-domain gap) — DISSOLVES if production runs All-22.** The ~0.86 classifier
  trained on All-22; if the live camera is also All-22, train and serve match. No gap.
- **Blocker 2 (detail adequacy) — DISSOLVES.** All-22 shows the full shell; DB depth/spacing
  (the coverage signal) is visible. The ADR-0014 wall was a *broadcast*-view limitation.
- **Blocker 3 (snap-timing / FP) — REMAINS, but is built** (snap detector + play-clock
  reset-vs-resume de-FP). Still needed to sample clean snap+1–2 s frames.

**Revised position: v0.3 is plausibly feasible / largely plumbing.** The remaining *technical*
gap is the normal one — the ~0.86 was on ~150 *curated* All-22 fixture frames, so it must be
validated on **live** All-22 gameplay (stadium/lighting/motion/HUD variation); a same-camera
curated→live gap, tractable, not a research arc. The real open question is now a **product/UX
decision** (is All-22 a camera players will actually run?), not vision feasibility.

**The broadcast-frame evidence below is not wasted — it is repurposed.** It shows that the
*standard/broadcast* cameras likely do NOT expose enough of the secondary, which is exactly
the input to the **playable-camera fallback** question: since some players won't run All-22,
we test (same-play, All-22 label as truth) whether coverage survives in a more playable camera
(standard / broadcast / Madden Classic). See `agents/capture/COVERAGE_CAPTURE_PLAN.md`.

## Revised plan (supersedes the "Recommendation" section below)

1. **Primary — validate on live All-22.** Capture live All-22 with *known* coverage → run the
   ~0.86 classifier on the live frames. If it holds, v0.3 is largely plumbing: retrain/adapt on
   live All-22 if needed, then wire `detect_coverage`.
2. **Playable-camera fallback.** Re-run the *same* practice reps in standard / broadcast /
   Madden Classic (players get a camera choice). Label from the All-22 pass; test which cams
   preserve the coverage signal. Broadcast is the least likely (see below); Madden Classic
   (wider/higher) is the best fallback candidate.

---

*Everything below is the ORIGINAL spike (premise since corrected — read with the correction
above in mind).*

## Method

The existing coverage classifier (`agents/capture/train_coverage.py`,
`crossval_coverage.py`) is a **ResNet18 backbone FROZEN + a trained linear head (512→4)**
over Cover 1/2/3/4, reporting the ~0.86 macro-F1. Its training corpus is **24 All-22
(coaches-film) clips** (`fixtures/coverage/madden26_coverage_cover{1..4}_*.mp4`), windowed
snap+1.0–2.0 s, 10 frames/clip (`extract_coverage_frames.py`). **None of that corpus, the
derived dataset, or a trained checkpoint is on the dev machine** — it lives on the GPU box.
So the spike could not re-run the classifier here; instead it evaluated the *input-domain*
question directly, which is the actual feasibility gate.

The 8 live snap-capture clips (from the M5b snap-detector work) **are** the production input
distribution — real PS5 broadcast/gameplay-camera footage. The `SnapDetector` was run over
all 8; for a sample of detected snaps the frame at **snap+1.5 s** (the middle of the coverage
window) was extracted — i.e. exactly the frames the production `detect_coverage` would see.

## Findings

### 1. View-domain gap: All-22 (training) vs broadcast-behind-offense (production) — decisive

The classifier learned from **All-22** — the high sideline angle that shows all 22 players
and the full defensive shell, where DB depth and left/right spacing (the coverage signal)
are directly visible. The **production feed is the broadcast/gameplay camera** — low, behind
the offense, ball-following. In the extracted snap+1.5 s frames the defensive backs are
**small, distant, foreshortened, and often occluded** by the line/formation; the depth axis
that separates Cover 2/3/4 is exactly what this camera compresses. A frozen-backbone linear
head trained on All-22 shells has no reason to transfer to this view, and — more
fundamentally — **the live PS5 feed never produces an All-22 frame** during normal play, so
the classifier's input distribution can never be matched in production. Re-training would
require broadcast-cam coverage-labelled data, which **does not exist**.

### 2. Detail adequacy unproven and likely inadequate — the ADR-0014 wall, with no escape hatch

This is the same wall that killed the CNN **formation** classifier: broadcast footage did
not expose enough detail for fine formation distinctions, which forced the **OCR-of-overlay
pivot** (ADR 0014). Coverage is **post-snap with no overlay to OCR** (ADR 0017 explicitly
notes this — "no such escape hatch"). At snap+1–2 s in the broadcast view the secondary is
rendered at a scale where even a human struggles to call Cover 2 vs Cover 3 from a single
frame. Until a human can reliably read coverage off these frames, no model can.

### 3. Snap-timing + false-positive contamination — the sampler feeds garbage

Several extracted "snap+1.5 s" frames still showed **pre-snap play-art / audible menus**, or
were **non-plays** (PAT kick, tackle close-up, replay). Cause: the snap detector's ~2-FP/clip
floor (it fires on pre-snap play-clock freezes) plus ~1 s snap-time granularity. A coverage
sampler driven by the current detector grabs a mix of real post-snap frames and pre-snap/FP
frames. The play-clock **reset-vs-resume de-FP** (this session, 94% held-out) and a finer
snap-time cue are prerequisites to even feed clean frames — necessary, not sufficient.

## Recommendation

**Do not wire the current classifier into `detect_coverage`.** It would emit confident-looking
but meaningless `COVERAGE_LOCKED` events off out-of-distribution frames — worse than the
current honest `None`.

**Next step is a data-adequacy experiment, not a code session** (mirrors the M5c formation
decision process before the OCR pivot):

1. Capture a handful of **broadcast-cam** plays with **known** coverage (set the defensive
   coverage in practice mode so the label is ground truth), extract the snap+1–2 s frames.
2. Test **human-readability**: can coverage be called from those broadcast frames at all? If
   a human can't, the broadcast feed lacks the signal and v0.3-as-specified is not buildable
   from it.
3. If (and only if) readable, build a broadcast-cam-native labelled set and train on *that*
   distribution — the All-22 classifier is not reusable.

**If broadcast frames prove unreadable** (the likely outcome), the honest options are: (a) a
**pre-snap safety-shell proxy** (2-high vs 1-high, sometimes readable pre-snap) as a coarser
signal than true coverage; or (b) scope live-feed coverage **out** and keep `COVERAGE_LOCKED`
dormant (the consumer seam, `gameplan/coverageHighlight.ts`, is already documented-silent per
ADR 0017, so downstream degrades gracefully).

**Downstream impact:** Phase 1b Gameplan `COVERAGE_LOCKED` highlight and Phase 1c stay gated
(ADR 0010) until this resolves — but 1a/1b's other work (`FORMATION_LOCKED` display) is not
blocked by it.

## What this spike de-risked / produced

- Established that v0.3 is a **research arc** with three enumerated blockers, before spending
  a code session on doomed plumbing.
- Confirmed the **snap detector + play-clock de-FP** are real prerequisites (built) but not
  the whole story.
- Defined the **cheap next experiment** (known-coverage broadcast capture → human-readability
  test) that decides whether v0.3 is buildable from the live feed at all.
