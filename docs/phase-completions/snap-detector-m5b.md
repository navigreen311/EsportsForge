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

## Validation (offline, against the 3 labelled clips)

**Recall 23/27 ≈ 85 % (≈92 % adjusting for 2 likely-mislabelled GT entries), 1 FP.**
The signal + gates hold across camera angles, field positions, tempo (mostly no-huddle),
and the edge cases. Delay-of-game is cleanly rejected (clip 3: 6/6, 0 FP).

## Honest state / follow-ups (not yet at the ±200 ms / ≥95 % spec bar)

- **Recall ~85–92 %, target ≥95 %.** The residual misses are tick-detection edges (the
  online rising-threshold occasionally skips a countdown tick vs the offline peak
  detector). A peak-based online tick (1-frame lookahead) should recover them.
- **1 FP** — a play-call screen with a grass backdrop that fools `ContextDetector`
  (labels it `live_gameplay`). Needs better play-call detection, not a snap-detector fix.
- **Snap-time granularity is ~1 s** (the tick interval), not yet ±200 ms. Fine for the
  coverage-frame-grab use case (the snap confirms at ~snap+1.5 s, inside the snap+1–2 s
  window), but tightening to ±200 ms needs a finer within-second cue.
- Validation set is 3 clips / ~27 snaps — thin for a ≥95 % claim; `--record` makes more a
  90 s ask each.

This lands the detector from an inert stub to a working, camera-independent v0.1 with a
clear path to spec. Downstream (`detect_coverage` → `COVERAGE_LOCKED`, ADR 0010/0017) is
still gated on the coverage model reaching 0.85 (the temporal-architecture effort).
