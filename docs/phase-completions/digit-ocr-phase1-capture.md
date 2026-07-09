# Digit-OCR Pass — Phase 1 Capture + Segmentation Spike (white-style)

Banked follow-up from **[ADR 0017](../adr/0017-live-feed-hud-recal-and-glyph-ocr-limit.md)**:
a dedicated digit-OCR pass for the broadcast-bar italic numerals — one pass to fix
all three symptoms (scores non-detection, clock-seconds `1↔7`, single-digit distance
`1↔7`). This session is **data capture + a font spike only** — no reader built.

- **Branch:** `ai-feature/digit-ocr` (off `hud-recal-live` @ `fbd6c2a`).
- **Approach chosen (recon, prior session):** fixed-template matching (NCC) with
  abstain-over-guess, not a CNN. Two data phases: **Phase 1 = white-style
  (clock/distance/down)**; Phase 2 = score-style (needs a deliberate scoring campaign).

## Goal achieved — white-style glyph library COMPLETE (0-9)

The recon corpus had only `0,1,2,3,4,6,7,8` in the white style (missing **`5`,`9`**).
One 40s live capture of running gameplay closed the gap and then some:

- **Richest source: the play-clock countdown.** It cycles `:40 → :10` — a full
  digit sweep every pre-snap (`:40 :33 :31 :30 :29 :28 :27 :26 :25 :24 :23 :22 :18
  :17 :16 :15 :14 :13 :11 :10`), covering **all of 0-9**. *Note for any future
  capture: the play clock is the fastest way to harvest every white-style digit.*
- Game clock ticked `2:09 → 2:00` (then froze at the 2-minute warning) → `9`, 0,1,2.
- Distance `3RD & 5` → `5`; score `0 × 6` → `6`.

The two missing digits (`5`, `9`) are both confirmed. **White-style library is complete.**

## Segmentation spike (G3) — VERDICT

**Score-style and white-style are the SAME TYPEFACE FAMILY but DIFFERENT STROKE
WEIGHT** (score is bolder), plus different scale and **three polarities**:
- score = **dark-on-light** (center nameplate),
- game clock/distance = **white-on-dark**,
- play clock = **dark-on-white-box** (a third polarity).

The shared letterforms (`0`,`6`,`7` compared across styles) are the same design, but
NCC **cannot bridge the weight gap** even after scale + polarity normalization — a
template of the thin white `7` will not correlate with the bold score `7`.

**Consequences:**
- **Two template sets (per style) — do NOT collapse to one.**
- **The score library CANNOT be seeded from white-style glyphs.** The **Phase-2
  scoring campaign remains a HARD prerequisite** for the scores symptom.
- (A CNN with stroke-width augmentation could span both, but template-matching was
  chosen.)

## Eval set (held-out, GT confirmed off the maintainer's TV)

- `3rd & 5` — single-digit distance (clock_run).
- `4th & 3` — single-digit distance (4th_and_3, frames 3-5).
- **`4th & 1` (the ADR-0017 failure case) was NOT captured** — the game didn't deal
  clean short-yardage bar frames (two `4th & short` attempts hit a glitched frame and
  a delay-of-game blanked box). **Still wanted, not blocking.**

GT sanity-check (maintainer, off TV): score **0-6**, **2nd** quarter, clock
**2:09→2:00**, **3rd & 5** — matches the captured frames.

## Reject set (negatives the reader must NOT read as digits)

Replay-graphic overlay · corrupted/green-static grabs · dark transition frames ·
**empty down-distance box** (delay-of-game) · **red `:00` play clock**.

## New findings for the build

- **(a) The play clock renders RED at expiry (`:00`).** The reader must handle
  **colored digits**, not only white/dark.
- **(b) The down-distance box BLANKS** in the delay-of-game state (play clock `:00`) —
  a legitimate "no reading" state, distinct from a failed read.
- **(c) Per-digit segmentation is FRAGILE.** The play-clock's inverted white box is a
  third polarity, and score glyphs are tight-kerned; naive connected-component
  segmentation grabbed box backgrounds and clipped glyphs during the spike.
  Segmentation needs real care in the build (fixed-slot crops for scores; separator/
  box-aware slicing for the cluster).

## Data manifest

Raw frames are **NOT committed** (145 MB of 1080p PNGs; they live outside the repo
with the other live refs, matching the `~/madden-recal-refs` convention). This doc is
the committed record; the frames + capture tools live at
`C:\Users\ivann\madden-recal-refs\digit-campaign\`.

| Dir | Frames | Contents | Role |
|---|---|---|---|
| `clock_run/` | 41 | play-clock `:40→:10` (all 0-9), game clock `2:09→2:00`, `3RD & 5`, score `0×6`; plus green-static/dark/transition frames | **white-style glyph library** + incidental negatives |
| `4th_and_3/` | 6 | f3-5: `4TH & 3` bar (clock `2:30/2:29`, PC `:32/:31`); f0-2: replay "SMITH" graphic | **eval** (f3-5) + negatives (f0-2) |
| `neg_delayofgame_redplayclock/` | 6 | `4th 5:33`, red `:00` play clock, **empty** down-distance box | **reject** |
| `grab_live.py`, `grab.sh` | — | the standalone HdmiCaptureSource dumper (no VAF core/WS) used for this campaign | tooling (preserve; promote to `scripts/` at Phase-2) |

Superseded/discarded: a first `clock_run` attempt (paused game — frozen clock, wrong
layout) and a first `4th_and_2` attempt (glitched frame reading `& 3`) were cleared;
a mislabeled `4th_and_2` (blanked box) was **renamed** to `neg_delayofgame_redplayclock`
rather than kept under a false GT label.

## Next session (NOT this one)

Build the white-style template reader (segment → normalize → NCC per glyph →
abstain-below-margin), evaluated against the held-out set above. **Headline metric:
the `1`-vs-`7` confusion rate** (overall accuracy can look fine while `1↔7` stays
broken — that pair is the entire point). Report abstain rate alongside accuracy; a
clean negative (templates can't separate `1` from `7` either) is a valid outcome.
Phase 2 (scores) still needs the deliberate scoring campaign.
