# Phase 0 Real-Footage Validation (D3 + D4 Pre-Merge Review)

- **Status:** Run 1 complete — surfaced 5 failed Phase 0 acceptance criteria. Re-runs follow each Phase 0 remainder milestone (M4.5, M5c, OCR cadence reform). See [Phase 0 status](0-vaf-foundation.md) and [remaining milestones](0-vaf-remaining-milestones.md).
- **Date:** 2026-05-07 (Run 1)
- **Source clip:** Madden 26 gameplay, 1080p59.94, 2:00 duration, AV1 encoded. Downloaded from publicly-available YouTube footage via `yt-dlp`. **Fixture is gitignored** — see "Reproduction" below for the exact regeneration command.
- **Harness:** `agents/capture/real_footage_harness.py` — feeds raw OpenCV-decoded frames directly into `Dispatcher.process_frame`, bypassing the websocket transport. Records per-frame adapter latency, sampled OCR readings, sampled events.
- **Run config:** 200 dispatched frames, frame-stride 5 (≈12 fps from a 60 fps source — matches the Madden adapter's preferred base FPS), Madden hint enabled, integrity mode `OFFLINE_LAB`.

## Reproduction

The fixture `agents/capture/fixtures/real/madden26.mp4` is gitignored (`.gitignore` covers `agents/capture/fixtures/real/*.mp4`). To regenerate it locally, run from the repo root with `yt-dlp` available (`pip install yt-dlp`):

```bash
yt-dlp \
  -f "bv*[height>=720][height<=1080][ext=mp4]+ba[ext=m4a]/b[height>=720][height<=1080][ext=mp4]/b[height>=720][height<=1080]" \
  --merge-output-format mp4 \
  -o "agents/capture/fixtures/real/madden26.mp4" \
  --no-playlist \
  --download-sections "*0:00-2:00" \
  "https://www.youtube.com/watch?v=3lQQJALgsPE"
```

Expected output:
- File: `agents/capture/fixtures/real/madden26.mp4`
- Size: ~45 MB (±5 MB depending on yt-dlp's selected stream)
- Duration: 2:00 (`--download-sections "*0:00-2:00"` clips to the first two minutes)
- Resolution: 1920×1080
- Frame rate: 59.94 fps
- Codec: AV1 video / AAC audio

If the source URL is taken down, swap in any 1080p Madden 26 gameplay clip from a public archive — the harness is resolution-aware (`hud_regions.json` scales bbox coords to non-1080p frames) but the calibration was done against this specific clip's HUD rendering, so swapping clips may shift OCR success rates until M4.5 re-runs against the new source.

After downloading, re-run the harness:

```bash
# From the EsportsForge repo root, with the backend venv (which has cv2 + easyocr) active:
python agents/capture/real_footage_harness.py \
  --video agents/capture/fixtures/real/madden26.mp4 \
  --max-frames 200 \
  --frame-stride 5 \
  --report agents/capture/fixtures/real/report_runN.json
```

The report JSON is small (~5 KB) and **is** committed to the repo as evidence per the milestone breakdown.

## Headline numbers

| Metric | Value | vs. spec |
| --- | --- | --- |
| Title locked | `madden26` (via hint path) | ✅ — locked on frame 1, confidence 0.9 |
| Time to lock (wallclock) | 5.28 s | ⚠️ Dominated by EasyOCR cold start |
| Per-frame latency p50 | **250 ms** | ❌ ADR 0006 budget = 80 ms |
| Per-frame latency p95 | **359 ms** | ❌ |
| Per-frame latency p99 | **485 ms** | ❌ |
| Max single-frame latency | 5,172 ms | ⚠️ First-frame EasyOCR model load |
| Mean latency | 285 ms | ❌ |
| Frames dispatched | 200 | — |
| Frames over 80 ms budget | **200 / 200 (100%)** | ❌ Every frame is breached |
| Adapter exceptions | 0 | ✅ |
| Events emitted | 0 | ❌ — every event was dropped at the budget gate |

## What this means

**Finding 1 — The 80 ms ADR-0006 budget is not achievable with EasyOCR on CPU.** Median per-frame cost (250 ms) is more than 3× the budget. Worst-case frames are 6× over. This isn't tunable — EasyOCR's per-region inference is the floor, and we have 8 OCR regions per frame in the current pipeline.

**Finding 2 — `hud_regions.json` bbox coordinates do not match real Madden 26 HUD.** Three of five sampled frames returned all-null OCR readings; the one partial reading (frame 995) read confidence 0.423 with a single garbage character ("I"). The bbox coords were authored from spec, not from actual footage measurement. They need to be re-derived from real frames before any of this is useful.

**Finding 3 — Title detection's "real" path was never exercised.** The session locked via the hint path (player's `active_title` setting passed at session-open). No `hud_signature.png` files have been curated for any title yet, so the heuristic + ORB paths return "no templates registered → use hint or unknown." This was working as designed — but it means the signature-based detection paths only have synthetic-frame test coverage, not real-frame validation.

## Concrete implications for Phase 1a

### Latency budget — three options, must pick one

1. **OCR cadence change.** Run OCR not every frame but only on detected events (post-snap → read score; pre-snap → read down/distance). Drops OCR from 12 reads/sec to ~1–3 reads/sec. **Cheapest fix; ships in a day.** Cost: stale readings between events, but for a HUD that updates ~once per play (every 25–40 s) that's fine.
2. **OCR replacement.** Move from EasyOCR to a lightweight ONNX digit-classifier (a 5-class CNN over each digit region). Per-region cost drops from ~30 ms to ~2 ms. **2–3 days of work; ships before M5c.** Highest quality option.
3. **Loosen the budget.** Revise ADR 0006 to 300 ms p95 for v0.1 on CPU. **Cheapest in code, expensive in product.** A 300 ms latency means every event reaches consumers a third of a second late — Drill Lab's "we just saw your formation" feel is degraded but still usable; War Room's mid-play banner becomes unworkable. Not recommended past v0.1.

**Recommendation:** Adopt option 1 (cadence change) immediately as Phase 1a Day 0 work. Path it forward to option 2 in M5c so v0.2 + v0.3 ship at the original budget. Do **not** loosen ADR 0006 — the budget is part of the consumer contract.

### HUD region calibration

Add a new milestone before M5: **M4.5 — HUD region calibration**. One day. Capture 5 representative real-frame screenshots, manually outline each region in an annotation tool, regenerate `hud_regions.json`. Without this, OCR is unusable on real footage regardless of which OCR engine we run.

### Title detection — signature curation

Add to M3 (or M4) — **collect 3–5 representative HUD frames per title, render a canonical 1080p signature crop to `app/adapters/<title>/hud_signature.png`**. Until those land, the hint path is the only working detection route. The hint path is fine for normal sessions but offers zero defense against a player launching the wrong title (e.g., Madden 25) — the system would happily try to read Madden 25's HUD with Madden 26's bboxes. Detection-via-signature catches that.

## What we couldn't measure (and why)

- **Formation classification accuracy.** The Madden adapter's `FormationDetector.detect_offensive` returns a stable stub (`shotgun_trips`, confidence 0.5) per the Phase 0 spec. Real classifier ships in Phase 1 M5c. Until then, formation accuracy is undefined regardless of footage source.
- **End-to-end latency including webhook publish.** The harness measures adapter time only. Webhook delivery + EsportsForge backend ingest add 5–25 ms in production. Not relevant for the 80 ms adapter budget but worth measuring once the full Phase 0 e2e smoke runs against real footage.
- **OCR accuracy ground-truth.** With three of five sampled OCRs returning all-null, ground-truth comparison is moot. Re-run after M4.5 calibration lands.

## Test artifacts

- Footage: `agents/capture/fixtures/real/madden26.mp4`
- Harness script: `agents/capture/real_footage_harness.py`
- Raw run report: `agents/capture/fixtures/real/report_run1.json`
- Reproduce: `python agents/capture/real_footage_harness.py --video agents/capture/fixtures/real/madden26.mp4 --max-frames 200 --frame-stride 5 --report agents/capture/fixtures/real/report_runN.json`
