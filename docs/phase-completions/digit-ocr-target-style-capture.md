# Digit-OCR Pass — Target-Style Capture Campaign (the ADR-0020 unblock)

Live capture campaign that collects the **target-style** broadcast-bar digits
[ADR 0020](../adr/0020-digit-ocr-is-data-bound-defer-until-target-style-capture.md)
declared the hard prerequisite for the `1↔7` fix banked in
[ADR 0019](../adr/0019-live-feed-hud-recal-and-glyph-ocr-limit.md). Standalone work on
`ai-feature/digit-ocr`; **capture only — no reader built, nothing wired in.** Frames
live outside the repo (`~/madden-recal-refs` convention); this doc is the committed record.

## BLOCKER BROKEN — real target-style `1`s AND `7`s in both symptom fields

ADR 0020's conclusion was that the fix is **data-bound**: the target-style digits
(game-clock-seconds and single-digit distance, white-on-dark) simply did not exist in
the captured set — distance had `{3,5}` only, **zero `1`, zero `7`**, and game-clock
seconds had no target-style `7`. The play clock (dark-on-white-box) is the wrong style
and cannot seed them. **Only live gameplay dealing those situations could produce them.**

This campaign captured exactly that. The `1↔7` quartet — the entire purpose of the pass —
is now covered in the correct style, all frames verified by eyeball off the maintainer's TV:

| Field (white-on-dark target style) | `7` captured | `1` captured |
|---|---|---|
| **Game-clock seconds** | `:07 :17 :27 :47 :57` | `:01 :11 :21 :31` (+ all `:10–:19`) |
| **Single-digit distance** | `2ND & 7` (verified, HUD steady) | `2ND & 1` (verified, HUD steady) |

The exact data ADR 0020 said only live capture could produce now exists. **The fix is
DATA-unblocked.**

## Full dataset (verified counts + GT)

Frames at `C:\Users\ivann\madden-recal-refs\digit-campaign\ts_*\` — **524 total**,
namespaced `ts_` (target-style) to keep them separate from the Phase-1 subdirs.

| Subdir | Frames | Ground truth | Notes |
|---|---|---|---|
| `ts_clock_run` | 362 | **game-clock seconds 0–9 COMPLETE** (both digit positions) | two 90s running-clock bursts (`3:22→2:40`, `4:32→3:50`); units sweep 0–9, tens 0–5 complete. Also holds an incidental `3RD & 1`. |
| `ts_2nd_and_1` | 12 (~4 HUD) | distance **`1`** | the critical `1` — one situation |
| `ts_2nd_and_7` | 12 | distance **`7`** | the critical `7` — one situation |
| `ts_2nd_and_3` | 24 | distance `3` | two plays |
| `ts_2nd_and_5` | 12 | distance `5` | |
| `ts_2nd_and_6` | 12 | distance `6` | |
| `ts_3rd_and_2` | 24 | distance `2` | two plays |
| `ts_3rd_and_5` | 12 | distance `5` | |
| `ts_3rd_and_6` | 24 | distance `6` | two plays |
| `ts_4th_and_2` | 12 | distance `2` | |
| `ts_4th_and_3` | 12 | distance `3` | |
| `ts_4th_and_5` | 6 | distance `5` | |

**Distance digit coverage (target style):** `1 2 3 5 6 7` captured; `4 8 9` not yet
(non-critical). **Game-clock seconds:** complete `0–9` with heavy redundancy.

## The `dist` zone recalibration (record for the reader build)

Spot-checks against this live feed showed the Phase-1 distance zone
`dist = [1700, 1013, 54, 40]` is **mis-framed**: the single distance digit sits ~10px
left of it and the box is too wide, so the glyph clips against the left edge with dead
box to the right. **Corrected for this feed: the distance digit sits at ~`x=1686`**
(single-digit zone ≈ `[1686, 1013, ~40, 40]`; may want +2–3px right to exclude the `&`
tail — finalize at reader-build). The **`gcsec = [1383, 1013, 68, 40]`** zone was
verified only ~2–3px tight (essentially correct). The reader build MUST use the
corrected `dist` x — the old `1700` will clip the digit.

## Honest thinness caveat (do not overstate)

- **Distance `1` and distance `7` are each ONE situation** (~4–6 near-duplicate frames =
  effectively **one glyph view apiece**). They are **thin CONFIRMATION cases**, not a
  training corpus.
- **Same-style `1`s/`7`s are NOT thin** — the running clock gives many game-clock-seconds
  `:X1`/`:X7` across the 362 frames.
- **Verdict:** sufficient to **ATTEMPT the reader** now. Distance-`1`/`7` should be
  **thickened opportunistically from different field positions** during normal future
  play (a 2nd/3rd situation each) — **NOT a blocker** to starting the build.

## 4th-down capture lesson (record so it is not re-learned)

- **4th down cuts to punt / field-goal / replay cameras and drops the broadcast bar
  exactly when you fire.** Capture single-digit distance on **1st / 2nd / 3rd down**,
  with the bar steady, and use **`--shots 12`** to ride out brief HUD flicker.
- **The brightness guard cannot detect "no HUD."** A dark transition (mean ~38) *and* a
  bright grass-field cutaway (mean ~92) both pass the >3.0 black-check with **no bar
  present**. Mean brightness ≠ HUD present — every distance grab was eyeball-verified
  (wide HUD crop) before its label was trusted.
- Concrete cost: a `ts_4th_and_1` attempt (12 frames, **not one** containing the bar)
  was captured and **deleted**; several other bursts caught snap/transition darks or
  HDMI green-static glitches and were deleted after verification. Mislabels were also
  caught this way (e.g. a called `2nd & 4` that the bar actually showed as `4TH & 5`).

## Capture tooling

Standalone `HdmiCaptureSource` tap (no VAF core / no WebSocket), device `"USB3.0 Video"`,
1920×1080, per-frame brightness printed + black-frame skip/abort. Tool at
`~/madden-recal-refs/digit-campaign/grab_live.py` (wrappers `grab.sh` / `grab.cmd`).
Preflight this session: card found, non-black signal, 1080p confirmed. **Preserve;
promote to `scripts/` at reader-build.**

## Next session — build the style-aware reader

The `1↔7` fix is now **DATA-unblocked**. Build the reader against this dataset
(same-style patch-NCC is the proven technique — see
[digit-ocr-reader-build-eval.md](digit-ocr-reader-build-eval.md) — now with target-style
templates that actually exist). **Success bar unchanged from ADR 0019/0020:**

- **HEADLINE: the target-style `1`-vs-`7` confusion rate** (game-clock-seconds +
  single-digit distance), reported first, with the thin-sample caveat stated (distance
  `1`/`7` = one situation each).
- **Abstain-over-guess preserved** (never-fabricate): a null beats a wrong digit.
- **Guardrail:** no regression on the fields/styles the reader trains on.
- Use the **corrected `dist` zone (~x=1686)**.
