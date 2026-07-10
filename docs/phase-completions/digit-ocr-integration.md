# Digit-OCR Pass — Clock-Seconds Reader Integrated into ocr_pipeline

Wires the proven style-aware digit reader
([digit-ocr-reader-result.md](digit-ocr-reader-result.md)) into the live OCR pipeline
for the **game-clock-seconds** field, fixing the ADR-0019 `1↔7` symptom
(`:17`→`:11`) in production. Clock **minutes** stay on the existing EasyOCR path,
untouched. Distance is not wired (verdict still PENDING — one glyph view per digit).

## What changed (3 files)

- **`digit_reader.py`** — refactored to a patch-based contract. `read_patch(patch)`
  reads an **already-cropped** field patch; `is_corrupt_patch` / `field_present_patch`
  / `segment_patch` operate on the patch. Frame+spec wrappers (`read`, `segment`, …)
  kept so the standalone eval/gate still runs. The reader never touches the full frame
  in the pipeline path — the pipeline owns the crop.
- **`hud_regions.json`** — added `clock_seconds: [1383,1013,68,40]` under
  `scoreboard.subregions` (the SS sub-crop of the `clock` box `[1352,1002,92,42]`),
  plus a calibration note. This is the coordinate contract: the zone lives in
  hud_regions, one place.
- **`ocr_pipeline.py`** — `OCRPipeline.__init__` loads the reader from
  `digit_templates/gcsec_templates.npz` (graceful no-op if absent). In `read_fields`
  (the **live cadence path**, `adapter.py:190`), when `clock` is due:
  `_reader_clock_seconds(frame, rc["clock"])` crops the `clock_seconds` zone via the
  pipeline's own `_crop`, calls `read_patch`, and **splices the two seconds digits
  onto the EasyOCR minutes** (`f"{minutes}:{secs}"`). Reader abstains → clock `None`.

## Abstain-over-guess is preserved end-to-end

- Reader unsure → `read_patch` returns `None` → `_reader_clock_seconds` returns clock
  `None` → **never a guessed digit**.
- The adapter (`adapter.py:192-197`) treats a null field as "couldn't read this frame"
  → **carries the last good cached clock forward**; only non-null reads are "fresh"
  (smoothed + trigger SNAPSHOT). So the `string_clock` mode-vote smoother **only ever
  votes over the reader's confident reads** — a reader-abstain holds the last correct
  value, never emits a wrong one. This is clock-agnostic and identical to how EasyOCR
  was handled; the change only makes the values accurate and the nulls principled.

## Live verification (gate + read_fields path)

- **Zone gate (fresh live frame):** the `clock_seconds` zone render-verified live —
  green box lands exactly on the seconds, excludes minutes/colon (x=1626 was proven to
  be the *distance* field and rejected). Reader read `2:00`→`00` and running clock
  seconds cleanly.
- **Running-clock read (live):** captured a live countdown `39→38→37→…→27`; the reader
  read **every second correct**, incl. **`:37`→`37`, `:31`→`31`, `:27`→`27`** — the
  exact `1↔7` symptom class, live. Re-confirmed `:37`→`37` at NCC 1.0.
- **Wired `read_fields` path (the live method) on live frames:** EasyOCR's blanket
  `7→1` sub emitted `:37→:31` and `:27→:21`; the wired reader **corrected them to
  `:37` / `:27`**, left genuine `:31` / `:39` unchanged, abstained on transition
  frames, and **quarter / down / distance read unchanged**.

## What was NOT run, and why

A full live-**services** run (capture agent → VAF `:8100` → subscriber, real-time) was
**not** performed. The two layers that could differ from the saved-frame proof were
closed by inspection instead:
- **Resolution/zone:** the capture agent uses the same `HdmiCaptureSource` — native
  1920×1080, no resize (`hdmi_capture.py`) — identical geometry to the saved frames, so
  the zone lands the same live.
- **Smoother/cadence/null-handling:** carry-last on null, smooth on confident reads
  (adapter.py:192-197) — clock-agnostic, verified by code.

The only thing a services run would uniquely exercise is real-time SNAPSHOT emission +
timing under concurrent load — low-risk existing infra that a sub-millisecond,
every-10-frames change does not stress. (Also blocked on a missing HDMI-source config:
`config.dev.toml` is set to `source="test-video"`.) Banked as an optional follow-up.

## Status

- **Clock-seconds `1↔7`: FIXED in the pipeline** (`read_fields` path), proven on live
  pixels through the pipeline's own method.
- **Minutes / quarter / down / distance:** untouched, existing path.
- **Distance `1↔7`:** reader built, verdict still PENDING (one glyph view per digit).
- **Scores:** still blocked (Phase-2 scoring campaign).
- **Optional follow-up:** a real-time live-services run to watch SNAPSHOT emission under
  load; `read_frame` (non-live path) could take the same seconds override for symmetry.
