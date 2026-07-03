# ADR 0016 — File-Mode Ingestion Reuses the Live Capture → WS Transport Path

- **Status:** Accepted
- **Date:** 2026-07-03
- **Reference:** [CLAUDE.md](../../CLAUDE.md) — project development context. Aligns with the Forge "extend without core changes" principle (Rule 5): file-mode is a new `CaptureSource` implementation registered like any source; the WS transport, VAF core ingest, dispatcher, OCR pipeline, and subscriber surface are untouched. (Capture-source protocol, `agents/capture/capture_agent/capture/__init__.py`: "add a source = new module + registry entry, no agent-core changes." The canonical `FORGE_ARCHITECTURE_PATTERN.md` is referenced repo-wide but not yet committed — tracked debt, see ADR 0013 followups.)
- **Establishing case:** Phase 1a Day 0 Stream B (`824cd6b`) — `FilePlaybackSource` (`agents/capture/capture_agent/capture/file_playback.py`).
- **Modifies:** [specs/01 §2](../specs/01-capture-agent.md) (capture sources — adds `file`).
- **Related:** [ADR 0013](0013-hud-calibration-recurring-maintenance.md) (HUD re-calibration — the per-footage gap file-mode surfaced), [ADR 0014](0014-ocr-overlay-over-cnn-for-formation-signals.md) (OCR-of-overlay — the events file-mode carries), [ADR 0015](0015-tiered-budget-and-sampled-ocr-cadence.md) (tiered budget + sampled cadence — how those events flow), [ADR 0005](0005-per-adapter-frame-rate-override.md) (per-adapter frame rate — the cadence file-mode replays at), [Phase 1a state report](../phase-kickoffs/1a-kickoff-state-report.md) §5 (solo-corpus validation) + §7.1 (file-mode in scope).

## Context

Phase 1a validates the Drill Lab cutover from mocked vision to the real VAF pipeline. The plan of record (state report §5) reframes that validation for a **solo founder with no alpha cohort and no live PS5/HDMI capture rig**: instead of live play by a staff cohort, the pipeline is exercised against curated recorded Madden 26 clips. Live-capture sources (capture-card via `cv2.CAP_DSHOW`, pc-monitor via `mss`) are Phase 1.1 M1-final work — they need hardware and a cohort to exercise, so they cannot be the Phase 1a validation vehicle.

Phase 0 already shipped `agents/capture/real_footage_harness.py`, which plays an MP4 into the pipeline — but it **deliberately bypasses the WebSocket transport**: it constructs a `SessionContext` + `Dispatcher` in-process and feeds frames directly (to sidestep the `:8001/:8002` dev-port issues and network jitter). That validates the adapter + OCR, but it leaves the **production transport** — capture agent → WS `frame_batch` → VAF core `/ws/ingest` → dispatcher → events → subscriber — **untested on recorded footage**. A transport path that only ever runs when capture hardware plus a cohort exist is exactly the kind of untested seam a cutover should not ship on ("no live-capture-only paths for Phase 1a validation").

## Decision

**File-mode ingestion is a first-class `CaptureSource` that feeds the same production transport a live capture would — not a bypass.** The validated path is end-to-end identical to live capture except for the frame origin:

```
file (MP4) → capture agent [FilePlaybackSource] → WS frame_batch
           → VAF core /ws/ingest → dispatcher → Madden OCR/adapter
           → events (SNAPSHOT / FORMATION_LOCKED) → subscriber
```

1. `FilePlaybackSource` implements the existing `CaptureSource` protocol and is selected via config `source = "file"`. It reuses `transport/ws_client.py`'s `frame_batch` encoding **unchanged** — byte-identical wire format to a live capture. Nothing in `core/`, the transport, the OCR pipeline, or the subscriber is file-aware; the only file-specific code is the source module.
2. Deltas from the Phase 0 `TestVideoSource` (documented in the source): **play-once + EOF** (per-clip pass/fail tally — `TestVideoSource` loops forever), **configurable playback rate**, and **1080p resolution normalization** so non-1080p footage aligns with the HUD regions calibrated at 1080p (ADR 0013).
3. Live-capture sources remain the production runtime for real users; file-mode is the **validation-time** driver for the same transport, and shares it verbatim.

### Sequence vs. real-time

Two playback modes make the tradeoff explicit:

- **`realtime`** (default) — paces emission to `target_fps`, mimicking live HDMI cadence. Files play at **real time, not accelerated**: a 27-minute clip takes 27 minutes and exercises the real-time cadence + tiered-budget behavior of ADR 0015 exactly as production would.
- **`max`** — yields unthrottled for throughput validation (acceptance criterion #4: sustain ≥30 fps-equivalent on file input); it measures pipeline throughput but does **not** reproduce real-time cadence.

`realtime` is the fidelity default; `max` is the throughput instrument.

## Alternatives considered

1. **Keep validating via `real_footage_harness.py` (in-process, WS-bypass).** Rejected: it leaves the production transport untested on recorded footage, so the cutover would ship a live-capture-only seam. The harness is retained as a fast adapter/OCR probe, not the cutover-validation vehicle.
2. **Block Phase 1a validation until live capture hardware + an alpha cohort exist.** Rejected: no cohort is available (solo founder, state report §5), so this stalls Phase 1a indefinitely — the entire §5 reframe exists to avoid that dependency.
3. **Reuse/extend `TestVideoSource` directly.** Rejected as-is: it loops forever (no EOF), so per-clip validation cannot tally a clean pass/fail, and it is the synthetic-smoke driver. `FilePlaybackSource` is a distinct source; `TestVideoSource` is retained for the Phase 0 synthetic smoke.
4. **Accelerated-only playback (`max` mode only).** Rejected as default: production runs the tiered budget + sampled-OCR cadence (ADR 0015) against real-time frame arrival; validating only at accelerated speed would not reproduce that. `max` is offered additionally, not exclusively.

## Consequences

- The production transport (agent → WS → core → OCR → events → subscriber) is now exercised by recorded-footage validation; there is **no live-capture-only code path** left untested before the cutover.
- Solo-corpus validation (state report §5) is unblocked without capture hardware or a cohort.
- Play-once + EOF give per-clip pass/fail tallying. In `realtime` mode, validation wall-clock ≈ clip length (full-corpus runs are batch/overnight; use `max` for quick throughput checks) — the per-clip windowing cap is a pending refinement (state report Q2).
- File-mode requires a decodable codec. YouTube AV1 defeats some OpenCV builds, so procurement downloads **H.264 mp4** and `FilePlaybackSource.open()` raises a clear codec error otherwise.
- **Surfaced limitation (honest).** The first file-mode run on a real broadcast YouTube clip (`madden26_yt_ocr_ravens.mp4`) confirmed clean transport and events flowing (113 `SNAPSHOT` in a gameplay window, zero errors) but produced **0 `FORMATION_LOCKED`**: the Phase 0 `hud_regions.json` calibration does not align with an arbitrary broadcast HUD, so OCR read ~null. File-mode did its job and revealed a real **downstream calibration gap** (ADR 0013), not a transport defect. Diverse footage needs per-style HUD calibration before it yields formation events.

## Followups

- **HUD recalibration for broadcast footage** (ADR 0013 recurring-calibration) — the open item from the Stream B ravens smoke; required before the diverse corpus yields `FORMATION_LOCKED`.
- **Full WS-path E2E.** Stream B's validation to date is source-level checks + in-process dispatch (harness-style); running the true E2E against a live core service over the WS transport on a clip remains to be exercised.
- **Live-capture sources** (capture-card / pc-monitor) still land in Phase 1.1 M1-final; file-mode shares the transport they will use.
- **Per-clip cap / windowing** for `FilePlaybackSource` (avoid processing full 20–90 min clips end-to-end) — state report Q2, pending.
