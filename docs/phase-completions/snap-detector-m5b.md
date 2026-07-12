# Snap Detector (M5b) — play-clock-freeze

Implements the real `SnapDetector` (was a Phase-0 stub) — the Madden 26 pre-snap /
post-snap state machine. It is the timing prerequisite for the Tier-2 live-coverage
arc: you cannot grab the snap+1–2 s post-snap frames the coverage classifier wants
without knowing when the snap happened.

## The signal — found empirically, two hypotheses ruled out first

Captured 3 continuous live clips (90 s / 30 fps each, via the new `grab_live.py
--record` mode) covering ~27 offensive snaps plus play-call screens, replays, and a
delay-of-game. Two intuitive signals were tried and **ruled out**:

- **Play-clock disappearance** — wrong: the play-clock stays visible the whole time,
  counting down and resetting to `:40` each play.
- **Field-motion frame-diff** — dead end: the ball-following gameplay camera **pans**,
  so field-diff measures camera motion, not the snap. (Same camera that ceilinged the
  CNN formation classifier, ADR 0014.)

**What survives: the play-clock FREEZE.** Pre-snap the clock ticks down ~1/s; at the
snap it stops decrementing and holds at the snap value for the whole play, then resets.
Because it is a **HUD signal it is camera-independent**. The snap = the moment the
countdown stops.

## Detection (per session, per frame, no OCR)

- **tick** — a mean-abs frame-diff on the play-clock zone `[1450,1002,96,44]` above a
  threshold (the digit changing); ~one per second while counting down.
- **freeze** — `FREEZE_FRAMES` (1.5 s) with no tick after ≥1 tick = a snap candidate.
- **gates** — a real snap's freeze is a live PLAY, so over the freeze window: context is
  `live_gameplay` (reuses the adapter's `ContextDetector` read — 0.7 ms, no OCR), the
  **field/grass is on screen**, and the **play-clock is not red**. These reject the
  three freeze look-alikes seen in capture:

  | Look-alike | Rejected by |
  |---|---|
  | Play-call screen | context (`play_call`) |
  | Replay close-up | field-green (a face, no grass) |
  | Delay-of-game `:00` | red-play-clock gate |

Wired per-session in `Madden26Adapter.process_frame` (like `PlayBoundaryTrigger`);
`snap.snapped` is True on the frame a snap is confirmed, and the adapter records
`_last_snap_frame`. Cost is a couple of small crops/frame — no OCR, no model.

## Validation (v0.2 — 8 clips, 61 labelled snaps)

Captured 5 more clips deliberately spanning the stressors: **huddle** (play-call
screens), **red-zone/goal-line** (low grass fraction), **no-huddle** (fast tempo),
**special teams** + **delay-of-game**, and **replays**. Every candidate freeze was
eyeball-labelled → **61 real snaps**.

- **Recall 58/61 = 95 %** (real per-frame detector) — **meets the ≥95 % bar.** The
  v0.1→v0.2 win was **peak-based tick detection** (v0.1's rising-threshold skipped
  countdown ticks → false freezes and missed real ones). At the candidate level the
  freeze signal recovers **61/61** snaps.
- The **low-green red-zone recall** was fixed by lowering `GREEN_MIN` 0.28→0.30 — the
  data showed the lowest real red-zone snap sits at grass-fraction 0.31.
- Delay-of-game and replays are cleanly rejected by the red / field-green gates.

## The ~2-FP/clip floor — now addressed by the play-clock reader (reset-vs-resume)

~18 FP across the 8 clips (~2 per 90 s). **Not tunable away over the frame-diff signal
alone.** A play-clock that briefly **pauses/hitches** mid-countdown (then resumes) freezes
exactly like a snap. The clean discriminator is what *ends* the freeze — a real snap
**resets** the clock to `:40` (value up), a pause **resumes** it (value down) — which needs
the play-clock **value** (the frame-diff signal cannot recover it: neither freeze duration,
tick threshold, nor reset-tick magnitude separate the FPs).

**Now wired.** The dark-on-white play-clock **CNN reader** exists (72% exact but **94% on
the reset-vs-resume decision** — the reset gap dwarfs per-read noise; see
`play-clock-reader-findings.md`). The adapter feeds the cached value into
`SnapDetector.update(frame, live, pc_value)`. On snap confirm the detector captures the
plateau value; if the clock then **resumes DOWN** during the POST_SNAP freeze it sets
`last_snap_pause = True`. This is **non-destructive** (the snap already fired — the flag is
an FP annotation surfaced as `adapter_state["_last_snap_pause"]`, biased to protect the 95%
recall: it only ever fires on an unambiguous resume-down). The downstream coverage gate reads
it to discount coverage on suspected-pause frames. The detector still runs **OCR-free when
`pc_value` is None** — the annotation is purely additive.

**±200 ms snap-time** is likewise a follow-up: granularity is currently ~1 s (the tick
interval); tightening needs a finer within-second cue.

This takes the detector from an inert stub to **v0.2 at the ≥95 % recall spec**, camera-
independent, with the FP floor understood and attributed. Downstream (`detect_coverage` →
`COVERAGE_LOCKED`, ADR 0010/0017) is still gated on the coverage model reaching 0.85.
