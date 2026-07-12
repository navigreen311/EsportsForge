# Play-clock reader — capture plan (v0.3 data collection)

**Goal:** push the play-clock reader past its current **77% exact** (held-out) by adding
more real countdown data. This is the only remaining lever — the tick-aware windowing
lever is spent, and a controlled A/B proved re-labeling the existing 8 clips does not
help. Expected payoff from ~6 more clips (8→14): exact **77% → mid-80s**,
reset-vs-resume **94% → ~97%**.

**Why more clips (not more tuning):** the play-clock is an opaque white HUD box, so the
digits look near-identical across clips — the ceiling is genuine *data volume* and
per-value coverage, not model capacity.

---

## Ground rules (read once)

- [ ] White play-clock range is **:10–:40** only — it turns **red at :09**, so there are
      no white single-digit values to chase.
- [ ] The single most valuable habit: **let the play-clock visibly tick DOWN before you
      snap** — into the teens where you can. Early snaps at :35 give few distinct values;
      full countdowns densely cover :10–:40 including the confusable 20s/30s.
- [ ] Vary matchup / stadium / time-of-day across the six clips (free compression
      diversity — the box is identical, but capture-card compression varies).
- [ ] Avoid long replay / cutscene / timeout stretches — they just become unreadable
      "?" seconds and waste labeling.
- [ ] Each clip is ~90 s. Record with the VAF venv python from
      `~/madden-recal-refs/digit-campaign`.

## Pre-flight

- [ ] PS5 on, capture card feeding, VB-CABLE/HDMI signal live.
- [ ] Sanity a single-frame grab or `--preflight` so you know the feed is not black:
      `python grab_live.py --preflight --label _check`

## Capture the six clips

Run each, ~90 s, during live offensive drives:

- [ ] **pcv_full1** — normal offense, matchup A
      `python grab_live.py --record --label pcv_full1 --seconds 90`
- [ ] **pcv_full2** — normal offense, matchup B (different teams/stadium)
      `python grab_live.py --record --label pcv_full2 --seconds 90`
- [ ] **pcv_full3** — normal offense, night game if available
      `python grab_live.py --record --label pcv_full3 --seconds 90`
- [ ] **pcv_full4** — normal offense, matchup C
      `python grab_live.py --record --label pcv_full4 --seconds 90`
- [ ] **pcv_nohud2** — no-huddle / hurry-up (more :40/:38 resets, tempo variety)
      `python grab_live.py --record --label pcv_nohud2 --seconds 90`
- [ ] **pcv_mix1** — mixed; deliberately let the clock run LOW (into the teens) before
      snapping on most plays
      `python grab_live.py --record --label pcv_mix1 --seconds 90`

> If the device rejects the default capture rate, retry with `--fps 30` (or `--fps 60`).
> Output lands at `~/madden-recal-refs/digit-campaign/<label>/<label>.mp4`.

## Verify each recording

- [ ] Each `<label>/<label>.mp4` exists and is ~90 s / non-trivial size.
- [ ] Spot-play one — confirm the play-clock box is visible and countdowns are present
      (not one long huddle/replay).

## Hand off to me

- [ ] Tell me the labels you recorded (e.g. "got pcv_full1..4, pcv_nohud2, pcv_mix1").

Then I run the turnkey ingestion — no further work from you:
1. Generate 1–2 fps contact sheets per clip.
2. Parallel subagent reads → dense labels.
3. Retrain with **tick-aware windowing** on all clips (existing 8 + new).
4. Held-out re-eval, export **play_clock_v0_3.onnx**, PR → merge.

---

*Context: reader lives at `app/adapters/madden26/play_clock_reader.py`; trainer +
labels here in `tools/play_clock/`. See `docs/phase-completions/play-clock-reader-findings.md`.*
