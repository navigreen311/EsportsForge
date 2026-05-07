# Madden 26 Adapter — Specification

> Companion: [02-core-service-spec.md](02-core-service-spec.md), [03-event-bus-contract.md](03-event-bus-contract.md).
> Madden 26 is the **first** adapter, not the only one. The patterns this spec establishes (HUD region maps, OCR pipeline, formation detection, state assembler) are the template every other adapter follows. CFB 26 will reuse 70%+ of this code.

## Purpose

Turn Madden 26 frames into typed `Madden26Payload` events on the bus. Cover the gameplay states EsportsForge agents need to reason about:

- Score, clock, quarter
- Down and distance, field position
- Offensive formation, defensive formation
- Snap detection (PLAY_STARTED), play resolution (PLAY_ENDED)
- Score changes, possession changes, turnovers

Out of scope for the v1 Madden adapter:
- Pre-snap audible recognition (player calls in real time — too fast and too dependent on user-controlled UI overlays)
- Route running / coverage breakdown (post-snap action recognition is a v2 problem; v1 emits formation only)
- Replay menu OCR (player exits to replays after a play; v1 just emits `MENU_DETECTED` and pauses)
- Player-attribute reads from the HUD (ratings overlay; rare in live play)

## Architecture

The adapter is a Python package under:

```
backend/app/services/integrations/visionaudio/adapters/madden26/
├── __init__.py
├── adapter.py              # Madden26Adapter class — entry point
├── hud_regions.json        # pixel coords for every HUD element we read
├── ocr_pipeline.py         # title-specific text extraction
├── formation_detector.py   # offensive + defensive formation classification
├── snap_detector.py        # frame-difference + camera-motion based
├── state_assembler.py      # builds Madden26Payload + emits events
├── models/
│   ├── formation_classifier.onnx   # bundled with the package
│   └── hud_signature.png           # used by core's title detector
└── tests/
    ├── fixtures/                   # short MP4s for repro testing
    └── test_*.py
```

The adapter exports one class:

```python
class Madden26Adapter:
    """Implements TitleAdapter (see Doc #02)."""

    title = TitleEnum.MADDEN26
    version = "0.1.0"           # bumped per release
    max_processing_ms = 80

    def __init__(self) -> None:
        self.ocr = OCRPipeline()
        self.formations = FormationDetector(model_path=...)
        self.snap = SnapDetector()
        self.assembler = StateAssembler()

    def process_frame(
        self,
        frame: np.ndarray,
        session: SessionContext,
    ) -> list[GameStateEvent]:
        ...
```

## HUD region map (`hud_regions.json`)

Madden's broadcast HUD is stable across game modes (Franchise, Online H2H, MUT, Ranked). The 1080p coordinate map for v1:

```json
{
  "schema_version": "1.0.0",
  "resolution": [1920, 1080],
  "regions": {
    "scoreboard": {
      "bbox": [40, 30, 380, 90],
      "subregions": {
        "team_home_abbr": [60, 50, 55, 30],
        "score_home":     [120, 50, 60, 30],
        "team_away_abbr": [205, 50, 55, 30],
        "score_away":     [265, 50, 60, 30],
        "quarter":        [60, 75, 60, 25],
        "clock":          [125, 75, 100, 25]
      }
    },
    "down_distance": {
      "bbox": [800, 30, 320, 60],
      "subregions": {
        "down":          [810, 35, 50, 50],
        "distance":      [870, 35, 110, 50],
        "field_position":[1010, 35, 100, 50]
      }
    },
    "play_clock": {
      "bbox": [1750, 50, 80, 80]
    },
    "formation_overlay_pre_snap": {
      "bbox": [400, 900, 1120, 150],
      "appears": "during pre-snap, fades after motion or snap"
    }
  }
}
```

Coordinates are in pixels at 1920×1080. Frames at other resolutions are resized in the core before reaching the adapter (Doc #02 §"Frame processing pipeline" step 3 implies this — adapters always see 1080p).

The `formation_overlay_pre_snap` region is where Madden's coaching cam shows the offensive personnel alignment graphic. This is the highest-signal region for formation detection.

`hud_regions.json` ships with the adapter. Updates to Madden's HUD (post-launch patches) require shipping a new `hud_regions.json` with a bumped `schema_version`. The adapter reads this at init time.

## OCR pipeline (`ocr_pipeline.py`)

Three OCR sub-tasks, each with different reliability profiles:

### Numeric (score, down, distance, clock)

- **Engine:** Tesseract 5 with the `-c tessedit_char_whitelist=0123456789:` config.
- **Preprocessing:** crop region → resize to 3× → adaptive threshold → invert if dark-on-light → dilate 1px.
- **Validation:** numeric values bounded (score 0–199, down 1–4, distance 0–99, quarter 1–5 with 5 = OT). Out-of-range reads are dropped silently and the previous value is retained.
- **Confidence:** Tesseract's per-character confidence averaged. Adapter publishes events at >= 0.85; below that, retains last good value.

### Field position

- Format: `OWN 35` / `OPP 22` / `MIDFIELD`.
- Tesseract with `-c tessedit_char_whitelist=OWPNMIDFLEDOPP0123456789` (overinclusive but cheap).
- Post-process: regex `^(OWN|OPP|MIDFIELD)( (\d{1,2}))?$`. If "MIDFIELD", normalize to `field_position: "MIDFIELD"`.

### Team abbreviations

- Tesseract with full-alphabet whitelist; cross-check against a fixed list of 32 NFL abbreviations (`NE`, `KC`, `DAL`, etc.).
- Output `team_home_abbr` / `team_away_abbr` once detected; cache for the session (these don't change mid-game).

The pipeline runs all three on each frame. Total cost target: <30ms (most frames hit the cache and short-circuit).

## Formation detection (`formation_detector.py`)

The hardest part of the adapter. Two classifiers:

### Offensive formation classifier

- **Input:** `formation_overlay_pre_snap` region (1120×150 px crop).
- **Model:** small CNN (MobileNetV3-Small backbone, 11M params), classification head over 24 Madden formations:
  - Singleback (Wing, Ace, Trips Bunch, Y-Slot, Tight, Doubles)
  - I-Form (Pro, Tight, Twin TE, Slot Flex)
  - Strong / Weak
  - Shotgun (Wing Trio, Bunch, Empty, Spread, Trips, Y Off Trips, Tight Slots, Doubles)
  - Pistol (Strong, Weak, Trips, Spread)
  - Goal Line / Hail Mary
- **Training data:** ~5000 labeled frames per formation, harvested from Twitch VODs of competitive Madden play. Bootstrap labeling via active learning — label 50 examples per class manually, train a v0.1 classifier, run it over 100K unlabeled frames, hand-correct the lowest-confidence 1000, retrain. Iterate to >0.92 macro-F1.
- **Inference:** ONNX runtime, ~15ms on CPU.
- **Output:** `(formation: str, confidence: float)`.

### Defensive formation / coverage classifier

- **Input:** Two cuts — pre-snap defensive front (defenders within 5 yards of LOS, derived from gameplay area below the formation overlay) and post-snap zone reveal (1.5s after snap detection).
- **Model:** Two heads on the same backbone — pre-snap "defensive front" (3-4, 4-3, Nickel, Dime, etc., 10 classes) + post-snap "coverage" (Cover 0/1/2/3/4, Tampa 2, Cover 6, Man, etc., 8 classes).
- **Training data:** harder than offense because Madden doesn't surface a defensive overlay. Manual labeling of broadcast-cam frames. ~3000 per class.
- **Output:** `(front: str, coverage: str | None, confidence: float)`. Coverage is `None` until 1.5s after snap detection.

Both classifiers ship as ONNX with the adapter. Total formation-detection cost target: <40ms.

### Bootstrap path for formation detection

We do not need both classifiers ready for the first ship. Sequencing within Phase 1:

1. **Adapter v0.1 (M5 in Phase 1 milestones):** offensive formation only, top-8 most common formations. Defense reports `null`. This is enough to validate the end-to-end loop.
2. **Adapter v0.2 (post-Phase-1):** add remaining offensive formations + pre-snap defensive front.
3. **Adapter v0.3:** add post-snap coverage detection.

The event bus contract has `defensive_formation: str | None` so v0.1 events are valid wire-shape; agents that depend on coverage simply see `None` until v0.3.

## Snap detection (`snap_detector.py`)

The trigger that emits `PLAY_STARTED` and resets per-play state. Approach:

- **Pre-snap signals:** play-clock OCR shows decreasing seconds, formation overlay is visible, scoreboard "down" stable.
- **Snap signals:** play-clock disappears OR formation overlay fades AND camera motion spikes (frame-difference in the central play region exceeds a threshold for 3 consecutive frames).
- **Post-snap state:** lasts until the play-clock reappears OR down-and-distance changes.

Implementation:
- Maintain a small state machine: `PRE_SNAP → SNAP_PENDING → POST_SNAP → BETWEEN_PLAYS`.
- Frame-difference computed only on a downscaled (320×180) version of the central region — cheap (~5ms).

Snap detection is approximate, not perfect. Acceptable error: ±200ms on snap timestamp, ~95% recall on snap events. Misses a snap → next frame's `down_change` event corrects state.

## State assembler (`state_assembler.py`)

Glue. Takes outputs from OCR + formation detector + snap detector and emits events on the contract.

Logic:

```
On every frame:
  ocr_state = ocr.read(frame, hud_regions)
  formations = formation_detector.read(frame, hud_regions)
  snap_state = snap_detector.update(frame, prior_state)

  events = []

  # Snapshot — emit at 1 Hz
  if time_since_last_snapshot >= 1.0s:
    events.append(make_snapshot(ocr_state, formations))

  # Discrete events from state diff
  if ocr_state.score_changed:
    events.append(make_event(SCORE_CHANGE, ...))
  if ocr_state.down_changed:
    events.append(make_event(DOWN_AND_DISTANCE, ...))
  if ocr_state.possession_changed:
    events.append(make_event(POSSESSION_CHANGE, ...))
  if formations.changed and snap_state == PRE_SNAP:
    events.append(make_event(FORMATION_LOCKED, ...))
  if snap_state.transitioned_to(POST_SNAP):
    events.append(make_event(PLAY_STARTED, ...))
  if snap_state.transitioned_to(BETWEEN_PLAYS):
    events.append(make_event(PLAY_ENDED, ...))

  return events
```

The "diff" semantics live in `SessionContext.adapter_state` — assembler reads previous values, compares, writes new values back. Pure function over (frame, session) → list[event].

## Integrity-mode rules Madden declares

Per Doc #02 §"Anti-cheat / Integrity Mode gating", each adapter declares which gates apply. For Madden 26:

| Mode | Behavior |
|---|---|
| `OFFLINE_LAB` | Full processing. All event types emitted. |
| `RANKED` | Pre-snap formation detection **disabled** (no `FORMATION_LOCKED` events). Post-snap analysis allowed. Score/clock/down OCR allowed. This protects against a player using EsportsForge as a real-time formation-revealing exploit in ranked H2H. |
| `TOURNAMENT` | Adapter does not run. Frames are dropped at the integrity gate before reaching us. |
| `BROADCAST` | Full processing, but events with `field_position`, `score_home`, `score_away`, etc. are emitted with a `broadcast_safe: false` flag if they would expose opponent-side information. (Concretely: if the dashboard is also being streamed, we redact opponent-camera reads.) |

The adapter exposes these rules to the core via:

```python
class Madden26Adapter:
    integrity_rules: dict[IntegrityMode, IntegrityPolicy] = {
        IntegrityMode.OFFLINE_LAB: IntegrityPolicy.UNRESTRICTED,
        IntegrityMode.RANKED: IntegrityPolicy(disable_event_types={EventType.FORMATION_LOCKED}),
        IntegrityMode.TOURNAMENT: IntegrityPolicy.NO_PROCESSING,
        IntegrityMode.BROADCAST: IntegrityPolicy(opponent_data_redacted=True),
    }
```

## Title detector signature (`models/hud_signature.png`)

A small 280×60 PNG of Madden's down-and-distance bar, used by the core's title detector (Doc #02). Bundled with the adapter.

The signature must be:
- Cropped from a stable HUD region (down-and-distance bar is unique to football)
- Visually distinct from CFB 26's equivalent (different color palette, font)
- Capable of matching across all Madden game modes (Franchise / Ranked / MUT / Online H2H all share this region)

Curate from production gameplay screenshots; commit alongside the adapter.

## Testing strategy

### Unit tests
- OCR pipeline: pinned input crops → expected text. ~30 fixtures covering edge cases (single-digit scores, double-digit, OT clock, "MIDFIELD" field position).
- Formation detector: confusion matrix on a held-out set; gate CI on macro-F1 ≥ 0.92.
- Snap detector: recall ≥ 0.95, precision ≥ 0.90 on a labeled-snap fixture set.

### Integration tests
- Full adapter: feed a 30-second pre-recorded Madden clip, assert the expected event sequence (specific snaps, score changes, formation locks).
- Run in CI against committed MP4 fixtures (kept small; <50 MB total).

### End-to-end smoke (manual, pre-release)
- Run the capture agent against a real Madden 26 session on a development PS5.
- Verify the dashboard surfaces formation reads in real time.
- Run all four Integrity Modes and confirm gate behavior.

## Performance budget

Per Doc #02, `max_processing_ms = 80`. Breakdown:

| Step | Budget | Actual (target) |
|---|---|---|
| HUD crops | 5ms | ~3ms |
| OCR (numeric) | 25ms | ~20ms cached / ~30ms cold |
| OCR (field pos) | 10ms | ~8ms |
| Snap detector | 10ms | ~5ms |
| Formation detector (offense) | 20ms | ~15ms |
| Formation detector (defense) | 20ms | ~25ms (post-Phase-1) |
| Assembler | 5ms | ~2ms |
| **Total** | **80ms** | **~58ms (v0.1) / ~88ms (v0.3 with both classifiers)** |

V0.3 with both classifiers exceeds budget by 8ms; mitigations (run formation detector every other frame, reduce CNN input size from 224 to 192) are deferred until we measure.

## What this spec does not decide

- **CFB 26 differences.** CFB ships with its own spec doc when its phase starts. We expect ~70% code reuse: same OCR pipeline (different team list), similar formation detector (different formation roster — CFB has option-heavy looks Madden doesn't), shared sport-archetype payload.
- **Audio detection.** v2.
- **Coach mode / Madden Universe / The Yard alternative modes.** v1 targets the standard broadcast HUD; alternative modes get added per-mode if we see usage data.
