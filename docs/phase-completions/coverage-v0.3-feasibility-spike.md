# Coverage classifier v0.3 — feasibility spike

- **Question:** Is the Madden v0.3 post-snap coverage classifier (`detect_coverage` →
  `COVERAGE_LOCKED`, ADR 0010/0017) **plumbing** (wire the existing ~0.86 classifier into
  the adapter) or a **research arc** (the classifier won't survive live production frames)?
- **Date:** 2026-07-12
- **Verdict:** **Research arc — NOT plumbing.** Do not open a v0.3 code session against the
  current classifier. Three compounding, independently-blocking problems below. The snap
  detector (M5b) and the play-clock reset-vs-resume de-FP (this session) are necessary
  prerequisites that are now built, but they are **not sufficient**.

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
