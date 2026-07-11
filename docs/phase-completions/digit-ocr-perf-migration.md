# Digit-OCR — EasyOCR → patch-NCC Throughput Migration

Replaces the EasyOCR wide `right_cluster` read (the live throughput ceiling banked in
[digit-ocr-live-services-verify.md](digit-ocr-live-services-verify.md)) with per-field
patch-NCC readers for **quarter / clock / down / distance**. EasyOCR is no longer called
on the cluster.

## The payoff

| | before | after |
|---|---|---|
| `read_fields(cluster)` | **703 ms** (194 ms over the 500 ms ocr-tier budget → dispatcher drops the frame → 0 SNAPSHOTs live) | **4.2 ms** (120× under budget) |

The earlier live run lagged ~40 s and dropped the socket; at 4.2 ms the pipeline keeps
real time.

## How

- **quarter, down (leading digit) and clock-minutes reuse the existing clock-seconds
  (gcsec) templates** — all white-on-dark, the same style (the gcsec set already reads
  0–9 at 228/228 as seconds). Validated held-out cross-field: **down 96% (157/165)**,
  **quarter 8/8** (1st), **minutes** correct on 3/4/5 @ NCC 0.81–0.93. No new templates —
  just zones (`quarter_digit`, `clock_minutes`, `down_digit`) + a `read_patch` `n_slots`
  override so the shared set reads a 1-digit field.
- **clock** = minutes (1 digit) + seconds (2 digits), both patch-NCC → `M:SS`. Live-
  verified: read a running clock `3:15 → 3:01` correctly through the full services path.
- **distance** now covers **0–9** (captured live `& 4 / & 8 / & 9 / & 10`; `& 10` also
  supplied the `0` and the missing down-`1`). Read via **connected-component
  segmentation** (1–2 digits; component crops keep the narrow `1` undistorted where an
  equal-column split stretches it) + a **1–25 validity** rule. **τ lowered to 0.45** — a
  narrow `1` legitimately has low best-NCC (~0.5) but a clean margin. Multi-digit
  `& 10 → 10` validated on 8/8 live frames; single-digit 165/173 correct, 1 wrong.
- `distance_field` zone `[1693,1010,62,44]`. play_clock (dark-on-white) stays null —
  its own reader is deferred (not in the payload today).

## Honest caveat — distance safety

Dropping EasyOCR removed the distance agreement cross-check (the old `_reader_distance`
gate). Distance is now **standalone** — safety rests on abstain (τ/δ) + the 1–25 validity
rule + the live smoother/cadence. Residual **~1 wrong / 165** on a mis-segmented marginal
frame (the confusable `3/5/6/8` cluster). A small regression from the gated version's
0-wrong, mitigated by the smoother; the `1<->7` fix is intrinsic (reads the real glyph).

## Status

- **Cluster fields on patch-NCC; EasyOCR dropped from `read_fields`.** Throughput ceiling
  eliminated (703 ms → 4.2 ms). Standalone gcsec eval regression-clean (228/228, 0/31 &
  0/10 `1<->7`).
- Live-verified: clock runs correctly live; `& 10` reads on live pixels through the
  pipeline method.
- **Follow-ups:** play-clock reader (dark-on-white); scores (Phase-2); the `read_frame`
  (non-live) path still uses EasyOCR.
