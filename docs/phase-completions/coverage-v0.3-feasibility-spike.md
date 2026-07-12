# Coverage classifier v0.3 — feasibility spike

- **Question:** Is the Madden v0.3 post-snap coverage classifier (`detect_coverage` →
  `COVERAGE_LOCKED`, ADR 0010/0017) **plumbing** (wire the existing ~0.86 classifier into
  the adapter) or a **research arc** (the classifier won't survive live production frames)?
- **Date:** 2026-07-12
- **Verdict (CORRECTED 2026-07-12 — see below):** The original verdict of "research arc"
  rested on a **false premise** — that All-22 is replay-only and never appears in the live
  feed. The operator confirmed **All-22 is a selectable LIVE gameplay camera** on this setup.
  That reverses the core finding: with production able to run All-22, the domain gap and
  detail-adequacy blockers **dissolve**, and v0.3 is **plausibly feasible / largely plumbing**,
  pending (a) validating the ~0.86 classifier on *live* All-22 frames and (b) a playable-camera
  fallback experiment. The original analysis is kept below as the honest record; the correction
  section restates the current position.

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
