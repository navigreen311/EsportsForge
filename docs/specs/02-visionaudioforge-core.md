# Spec — VisionAudioForge Core Service

> **Reference:** [docs/FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md). This is the canonical Forge for vision processing. The pattern's five rules govern every architectural decision below.
> **Companion specs:** [docs/specs/01-capture-agent.md](01-capture-agent.md), [docs/specs/03-mock-removal-and-page-wiring.md](03-mock-removal-and-page-wiring.md). Deeper architectural context (capture agent details, full event-bus schema with all 8 sport-archetype payloads, Madden 26 adapter detail, Phase 1 milestones) lives in [docs/integrations/visionaudioforge/](../integrations/visionaudioforge/).
> **Status:** Specification only. No implementation code.

## Purpose

The VisionAudioForge core service replaces the simulated pipeline at `backend/app/services/integrations/visionaudio/vision_client.py:132`. It owns:

1. Frame ingestion from one or more capture agents.
2. Per-session integrity-mode gating (consults EsportsForge backend for the user's current mode).
3. Title detection — identifies the active game from frame content.
4. Title routing — dispatches frames to the matching title adapter.
5. Event publishing — typed, sport-archetype-shaped events flow to subscribers.
6. Anti-cheat enforcement — gating happens server-side, never trusted to the agent.

The service is **multi-title from day one** via an adapter pattern. Madden 26 ships first; CFB, NBA, EA FC, MLB, Warzone, Fortnite, UFC 5, Undisputed, PGA TOUR 2K25, Video Poker each get their own adapter under `adapters/`.

---

## 1. Core service responsibilities

### Frame ingestion

- WebSocket endpoint `/ws/ingest` accepts authenticated agent connections.
- Validates `Authorization: Bearer <api_key>` against EsportsForge backend's `/api/v1/auth/validate-capture-key`.
- Maintains a `SessionContext` per connection: session_id, user_id_hash, active title (once locked), integrity mode, frame history ring, adapter state.
- Decodes JPEG frames to numpy arrays (RGB, 1080p assumed; resize upstream of dispatch if not).

### Integrity-mode gating (frame-level)

For every frame:

```
if integrity_mode == TOURNAMENT:
    drop_frame(reason="integrity_tournament_blocks_capture")
elif integrity_mode == RANKED and title in RANKED_BLOCKED_TITLES:
    drop_frame(reason="ranked_blocks_anti_cheat_titles")
elif integrity_mode == BROADCAST and frame_contains_opponent_data:
    process_with_opponent_redaction()
else:
    process_normally()
```

Mode is consulted from the session context (set at session open, refreshed on `POST /api/v1/sessions/{id}/integrity-mode`). The agent never decides — it sends every frame. The core decides whether to process.

### Title detection

Once-per-session. Inputs: a small frame buffer (first ~5 frames). Output: `(title, confidence)`.

**v1 implementation: heuristic / template-match HUD signature.** Each adapter ships a `hud_signature.png` — a small (~280×60 px) crop of a stable HUD region that uniquely identifies the title. The detector slides each signature across the frame using normalized cross-correlation (or ORB feature matching for low-quality captures); the title with the highest match score above 0.85 wins.

If no confident match within 30 s, the core notifies the agent via a `session_open` amendment (`active_title: null`, `capture_allowed: false`) and the dashboard surfaces "Couldn't detect game — verify capture source."

The `active_title` hint from `/sessions/open` is a tiebreaker for close scores, not authoritative.

### Title routing

Single registry:

```python
ADAPTERS: dict[TitleEnum, type[TitleAdapter]] = {
    TitleEnum.MADDEN26: Madden26Adapter,
    TitleEnum.CFB26: CFB26Adapter,
    TitleEnum.NBA2K26: NBA2K26Adapter,
    # ... all 11 titles, populated as each adapter ships
}
```

Once title is locked, every subsequent frame in the session dispatches to `ADAPTERS[session.title].process_frame(frame, session)`. Adapters return a list of events; the core publishes them.

### Event publishing

Typed events flow to two destinations:

- **EsportsForge backend webhook** — batched POSTs to `/api/v1/visionaudio/events` every 250 ms or 32 events, whichever first. Backend persists what it cares about and dispatches to the relevant agents (GameplanAgent, OpponentScout, etc.).
- **WebSocket subscribers** — `/ws/events/{session_id}` for the live dashboard overlay.

Events conform to the universal envelope + sport-archetype payload schema (Section 3 below).

### Anti-cheat gating logic per Integrity Mode (Section 6)

Gating decisions are made server-side, applied frame-by-frame and event-by-event. Detail in §6.

---

## 2. Adapter pattern

Each title gets a self-contained module under `backend/app/services/integrations/visionaudio/adapters/<title>/`:

```
adapters/madden26/
├── __init__.py
├── adapter.py                # Madden26Adapter — implements TitleAdapter protocol
├── hud_regions.json          # pixel coords for every HUD element
├── hud_signature.png         # used by core's title detector
├── ocr_pipeline.py           # title-specific text extraction (Tesseract config + region crops)
├── formation_detector.py     # offensive/defensive formation classification
├── snap_detector.py          # frame-difference + camera-motion based snap state machine
├── state_assembler.py        # builds canonical events from OCR + formation + snap outputs
├── models/
│   └── formation_classifier.onnx
└── tests/
    ├── fixtures/             # short MP4 fixtures for repro testing
    └── test_*.py
```

### Adapter contract (`TitleAdapter` protocol)

```python
class TitleAdapter(Protocol):
    title: TitleEnum
    version: str                              # "madden26@0.3.1"
    max_processing_ms: int                    # default 80

    integrity_rules: dict[IntegrityMode, IntegrityPolicy]   # adapter declares its own gating

    def process_frame(
        self,
        frame: np.ndarray,
        session: SessionContext,
    ) -> list[GameStateEvent]:
        ...
```

### Hard requirements on adapters

- **Pure function semantics.** No network calls, no DB writes. State (last formation seen, frame-difference state) lives in `session.adapter_state`, owned by the core.
- **Bounded latency.** Every adapter declares `max_processing_ms`. The core enforces it; if an adapter exceeds budget, the frame drops and the breach is logged.
- **No model loads in `process_frame`.** Adapters lazy-load ONNX models in `__init__`; the core constructs the adapter once per worker.
- **Bring your own HUD.** `hud_regions.json` is the adapter's coordinate map. Patches to a game's HUD are handled by shipping a new `hud_regions.json` with a bumped `schema_version` — no adapter binary release required.

### Per-adapter components

Each adapter owns four concerns (the four modules listed above):

- **HUD regions (`hud_regions.json`)** — pixel-coord crops for every HUD element the adapter reads (scoreboard, clock, down/distance, formation overlay, etc.). At 1080p; the core resizes other resolutions upstream.
- **OCR pipeline (`ocr_pipeline.py`)** — Tesseract or PaddleOCR with title-specific configs (numeric whitelists for clock/score, alphanumeric for team abbreviations and field-position text). Confidence-gated; below threshold, retain the prior good value.
- **Formation/state detector (`formation_detector.py` for football, sport-equivalent for others)** — classifier on the relevant HUD region. Sport-equivalent variants:
  - Basketball: pick-roll detection, defensive scheme overlay (ICE, drop, switch, blitz)
  - Soccer: formation overlay, pressing intensity meter
  - Baseball: pitcher set, batter stance
  - FPS / BR: loadout, weapon ID, zone phase, minimap state
  - Combat: stance, damage state, round overlay
  - Golf: lie, wind, distance to pin
  - Card: dealt hand, hold state, paytable
- **State assembler (`state_assembler.py`)** — glues OCR + classifier outputs into the universal event-bus contract; emits `SCORE_CHANGE`, `FORMATION_LOCKED`, `KILL_CONFIRMED`, etc., per the universal taxonomy.

### Adding a new adapter

Register it in the title-adapter registry, ship its `hud_signature.png` to the title detector, and authoring + QA the new title's vocabulary mappings. **Zero core changes required.** This is the architecture's load-bearing property.

---

## 3. Universal event bus contract

Locked surface. Adapter authors emit events conforming to this; consumers (EsportsForge agents, frontend pages) subscribe against this. Every event has the same envelope; the payload is title-specific via Pydantic discriminated union.

### Envelope (universal across all 11 titles)

```json
{
  "event_id":         "01HXXX...",
  "session_id":       "ses_01HXXX",
  "user_id_hash":     "abc123...",
  "title":            "madden26",
  "timestamp":        "2026-05-06T22:31:14.812Z",
  "captured_at":      "2026-05-06T22:31:14.760Z",
  "confidence":       0.94,
  "adapter_version":  "madden26@0.3.1",
  "event_type":       "FORMATION_LOCKED",
  "payload":          { ... title-specific shape ... }
}
```

### Event taxonomy (universal across all 11 titles)

The complete v1 set. Adapters emit a subset; new types require a contract version bump.

| Event type | Sports that emit |
|---|---|
| `SESSION_STARTED`, `MATCH_STARTED`, `MATCH_ENDED` | all |
| `SCORE_CHANGE`, `POSSESSION_CHANGE` | football, basketball, soccer, baseball |
| `DOWN_AND_DISTANCE` | football |
| `PLAY_STARTED`, `PLAY_ENDED` | football, baseball, basketball |
| `FORMATION_LOCKED`, `COVERAGE_LOCKED` | football, basketball |
| `KILL_CONFIRMED`, `DOWN_CONFIRMED`, `DEATH_CONFIRMED` | FPS, BR, combat |
| `LOOT_PICKED_UP`, `ZONE_PHASE_CHANGE`, `LOADOUT_CHANGE` | BR, FPS |
| `ROUND_STARTED`, `ROUND_ENDED`, `DAMAGE_DEALT`, `DAMAGE_TAKEN`, `STANCE_CHANGE` | combat |
| `STROKE_TAKEN`, `HOLE_COMPLETED` | golf |
| `HAND_COMPLETED` | card |
| `MENU_DETECTED`, `INTEGRITY_DROP`, `SNAPSHOT` | all (debug / state) |

### Sport-archetype payload bases

Eight base classes for 11 titles (FPS and BR share). Every title's payload extends one of these:

| Base | Titles | Core fields |
|---|---|---|
| `FootballPayload` | Madden 26, CFB 26 | score, clock, quarter, down, distance, field_position, possession, offensive_formation, defensive_formation |
| `BasketballPayload` | NBA 2K26 | score, clock, quarter, shot_clock, possession, offensive_action, defensive_scheme |
| `SoccerPayload` | EA FC 26 | score, clock, half, possession, formation_home, formation_away, last_action |
| `BaseballPayload` | MLB The Show 26 | score, inning, outs, count, base_state, batter, pitcher |
| `BattleRoyalePayload` | Warzone, Fortnite | health, armor, weapons, zone_phase, zone_timer, teammates_alive, kills |
| `CombatSportPayload` | UFC 5, Undisputed | round, round_clock, fighter_health (own + opp), stance, damage_state, last_strike |
| `GolfPayload` | PGA TOUR 2K25 | hole_number, par, current_stroke, distance_to_pin, lie, wind, score_to_par |
| `CardPayload` | Video Poker | hand_id, dealt_hand, held_cards, paytable_state, credits, bet |

### JSON schema example — football (Madden 26)

```json
{
  "event_id":        "01HXXX...",
  "session_id":      "ses_01HXXX",
  "user_id_hash":    "abc123...",
  "title":           "madden26",
  "timestamp":       "2026-05-06T22:31:14.812Z",
  "captured_at":     "2026-05-06T22:31:14.760Z",
  "confidence":      0.94,
  "adapter_version": "madden26@0.3.1",
  "event_type":      "SNAPSHOT",
  "payload": {
    "title":                "madden26",
    "score_home":           14,
    "score_away":           10,
    "quarter":              3,
    "clock":                "8:34",
    "down":                 2,
    "distance":             7,
    "field_position":       "OWN_35",
    "possession":           "home",
    "offensive_formation":  "Shotgun Trips",
    "defensive_formation":  "Cover 3"
  }
}
```

Equivalent shapes exist per archetype; full enumeration in [docs/integrations/visionaudioforge/03-event-bus-contract.md](../integrations/visionaudioforge/03-event-bus-contract.md).

### Subscription patterns

Consumers subscribe via predicate filters on the envelope:

```python
# All events for one session
sub.subscribe(filter=lambda e: e.session_id == "ses_01HXXX")

# All football events across Madden + CFB
sub.subscribe(filter=lambda e: e.title in {"madden26", "cfb26"})

# Score changes globally for a live ticker
sub.subscribe(filter=lambda e: e.event_type == "SCORE_CHANGE")
```

This is the property that lets one consumer (e.g., GameplanAgent) work for both football titles without per-title branching.

---

## 4. Madden 26 adapter spec (proves the pattern)

The reference adapter. Detail in [docs/integrations/visionaudioforge/04-madden26-adapter-spec.md](../integrations/visionaudioforge/04-madden26-adapter-spec.md). Summary here for spec-completeness:

### HUD region map

`hud_regions.json` at 1080p covers:

- Scoreboard (40,30,380×90): team abbreviations, scores, quarter, clock.
- Down-and-distance bar (800,30,320×60): down, distance, field position.
- Play clock (1750,50,80×80): countdown timer.
- Formation overlay (400,900,1120×150): pre-snap offensive personnel.

### OCR pipeline

Three sub-tasks:

- **Numeric** — Tesseract with `tessedit_char_whitelist=0123456789:`. Adaptive threshold preprocessing. Bounded validation (score 0–199, down 1–4, distance 0–99). Confidence gate at 0.85.
- **Field position** — Tesseract with alphanumeric whitelist; regex post-process for `^(OWN|OPP|MIDFIELD)( (\d{1,2}))?$`.
- **Team abbreviations** — Tesseract; cross-check against the 32 NFL abbrev list; cache for the session.

### Formation detector

- **Offensive:** MobileNetV3-Small (11M params), 24-class (Shotgun Trips/Bunch/Empty/.../Goal Line). Trained on ~5000 labeled frames per class via active-learning bootstrap. ONNX runtime, ~15 ms per inference. Macro-F1 target ≥ 0.92 at v0.3; ≥ 0.85 at v0.1 with the top-8 most common formations.
- **Defensive:** Two heads on the same backbone — pre-snap defensive front (3-4, 4-3, Nickel, Dime, etc., 10 classes) + post-snap coverage (Cover 0/1/2/3/4, Tampa 2, Cover 6, Man, etc., 8 classes). Coverage detection at 1.5 s post-snap. Defers to v0.3.

### Snap detector

State machine over play-clock OCR + frame-difference in the central play region. Cheap (<5 ms). 95% recall, ±200 ms precision on snap-time accuracy.

### State assembler

Reads outputs from OCR + classifier + snap detector; diffs against `session.adapter_state` to emit `SCORE_CHANGE`, `DOWN_AND_DISTANCE`, `FORMATION_LOCKED`, `PLAY_STARTED`, `PLAY_ENDED` events.

### Performance budget per frame (80 ms)

| Step | Budget | Actual (target) |
|---|---|---|
| HUD crops | 5 ms | ~3 ms |
| OCR (numeric) | 25 ms | ~20 ms cached / ~30 ms cold |
| OCR (field position) | 10 ms | ~8 ms |
| Snap detector | 10 ms | ~5 ms |
| Formation detector (offense) | 20 ms | ~15 ms |
| Formation detector (defense) | 20 ms | ~25 ms (post-Phase-1) |
| Assembler | 5 ms | ~2 ms |
| **Total v0.1** | 80 ms | **~58 ms** ✓ |
| **Total v0.3 (with defense)** | 80 ms | **~88 ms** — needs the mitigation below |

If v0.3 exceeds budget: run formation detector every other frame (15 fps adapter cadence, 30 fps capture cadence), drop CNN input from 224×224 to 192×192. Both options preserve event quality.

---

## 5. Caching strategy and TTLs

The adapter is a hot path. Caching reduces redundant work:

| Cache | Key | TTL | Eviction |
|---|---|---|---|
| **OCR result cache** | hash of cropped HUD region | 1 s OR until next frame whose diff vs prior > threshold | Per-session LRU, 100 entries |
| **Formation classifier output** | `(session_id, frame_id)` | Until snap detected (state machine cleared) | Cleared on `PLAY_STARTED` event |
| **Title signature templates** | `title_enum` | service lifetime | Reload on adapter version bump |
| **Event de-duplication window** | `(session_id, event_type, payload_hash)` | 250 ms | Per-session ring buffer |
| **Webhook delivery batches** | none — micro-batched in-memory | 250 ms or 32 events | Flushed on send |

OCR cache hit rate target: >60% in steady state (clock and down/distance change rarely between frames).

### Frame retention

**No frame storage in v1.** Frames are processed and dropped. Events flow to the EsportsForge backend; backend stores what it stores per its retention policy. The core service's only persistent state is per-session (in-memory) until the session closes.

This is a privacy-by-default decision. Phase 2+ may add an opt-in frame retention behind a feature flag for replay-debugging, gated by Integrity Mode (Offline Lab only — see §6 cross-cutting rule).

---

## 6. Anti-cheat gating logic per Integrity Mode

Gating happens in the core, not the agent. The agent sends every frame; the core decides whether to process based on the player's current Integrity Mode.

### Frame-level gating (before adapter dispatch)

```python
if integrity_mode == IntegrityMode.TOURNAMENT:
    drop_frame(reason="integrity_tournament_blocks_capture")
    return
elif integrity_mode == IntegrityMode.RANKED:
    if session.title in {TitleEnum.WARZONE, TitleEnum.FORTNITE, TitleEnum.VALORANT}:
        drop_frame(reason="ranked_blocks_anti_cheat_titles")
        return
    # else: process normally; adapter applies its own per-event gates below
elif integrity_mode == IntegrityMode.BROADCAST:
    # process normally; opponent-data redaction applied at event-emission stage
    pass
elif integrity_mode == IntegrityMode.OFFLINE_LAB:
    # full access
    pass
```

### Event-level gating (per-adapter declaration)

Each adapter declares its own integrity policy:

```python
class Madden26Adapter:
    integrity_rules: dict[IntegrityMode, IntegrityPolicy] = {
        IntegrityMode.OFFLINE_LAB: IntegrityPolicy.UNRESTRICTED,
        IntegrityMode.RANKED:      IntegrityPolicy(
            disable_event_types={EventType.FORMATION_LOCKED}   # no real-time formation reveal
        ),
        IntegrityMode.TOURNAMENT:  IntegrityPolicy.NO_PROCESSING,
        IntegrityMode.BROADCAST:   IntegrityPolicy(opponent_data_redacted=True),
    }
```

Effects:
- **OFFLINE_LAB** — all events emitted.
- **RANKED** — `FORMATION_LOCKED` events suppressed (no live formation reveal during ranked H2H). Score / clock / down OCR still runs and emits.
- **TOURNAMENT** — adapter doesn't run at all (frames already dropped at the frame-level gate above).
- **BROADCAST** — events emit with `broadcast_safe: false` flag if they would expose opponent-side data; subscribers decide whether to render. Also supports payload redaction at the assembler.

### Mid-session mode change

Player switches mode → EsportsForge backend POSTs `/api/v1/sessions/{id}/integrity-mode`. Core:
1. Updates session context.
2. Re-evaluates the in-flight frame and any queued events under the new policy.
3. Sends `capture_pause` / `capture_resume` to the agent if the new mode requires it.

### Audit trail

Every gate decision logs:

```json
{
  "session_id": "...",
  "user_id_hash": "...",
  "mode": "tournament",
  "decision": "drop_frame",
  "reason": "integrity_tournament_blocks_capture",
  "ts": "..."
}
```

Retained for 90 days. Tournament organisers can request the trail per player.

---

## 7. Performance targets

| Metric | Target | How measured |
|---|---|---|
| **Capture-to-event latency p99** | <2 s | Time from `frame.captured_at` to webhook POST. Tracked per session. |
| **Adapter processing time p95** | <80 ms | Per `process_frame` call. Budget enforced; breaches drop the frame and log. |
| **OCR p50 / p95** | <25 ms / <40 ms | Tesseract call timing per region. Cache hits ~5 ms. |
| **Formation detector p95** | <20 ms (offense), <25 ms (defense post-Phase-1) | ONNX inference. |
| **Title detection lock time** | <5 s with confidence ≥0.85 | Time from session open to title-locked event. |
| **Webhook delivery success rate** | ≥99.5% | EsportsForge webhook returns 2xx. Up to 5 retries with exponential backoff before drop. |
| **Concurrent sessions per service instance** | ≥100 | t3.medium ECS task. Scale horizontally beyond. |
| **Event throughput per session** | 5–15 events/sec sustained | At 12 fps capture × ~1 event per frame post-deduplication. |
| **Frame drop rate (gating-driven)** | <1% in Offline Lab; mode-dependent in Ranked / Tournament | Log-derived, alarmable. |

### Latency budget breakdown (capture → dashboard)

| Stage | Budget | Notes |
|---|---|---|
| Capture agent (encode + batch) | 350 ms | 4 frames × 83 ms at 12 fps |
| Network (WS) | 50–200 ms | Public internet to ECS region |
| Adapter processing | 80 ms | Per-frame budget |
| Event publish to EsportsForge | 50–100 ms | Webhook POST |
| EsportsForge agents → frontend WS | 50–150 ms | DB write + WS push |
| **Total p99 capture-to-dashboard** | <2 s | End-to-end target |

---

## 8. Failure modes and graceful degradation

| Failure | Effect | Behaviour | Recovery |
|---|---|---|---|
| **Title detection fails for >30 s** | No adapter dispatch | Core sends `session_open` amendment to agent: `active_title: null, capture_allowed: false`. Frontend banner: "Couldn't detect game — verify capture source." | Player adjusts capture source; detection re-runs on reconnect. |
| **Adapter exceeds latency budget** | Frame dropped | Frame skipped, breach logged. Subsequent frames continue. If breaches >5% over 60 s, alarm. | Operator investigation; possibly reduce adapter cadence (every other frame). |
| **OCR engine crashes** | Pipeline blocked | Adapter wrapped in `try / except` per stage; OCR failure causes that stage's value to retain its prior good value. Adapter still emits events with stale OCR fields flagged via `confidence < 0.5`. | OCR auto-recovers per frame (Tesseract subprocess restart on persistent failures). |
| **Webhook delivery failure** | Events queue, may drop | Retry up to 5x with exponential backoff (250 ms, 500 ms, 1 s, 2 s, 4 s). After 5 failures, drop with reason `webhook_dlq`. | Operator investigates EsportsForge backend health; events lost are not durable in v1 (see Open Question on event-bus durability in [docs/integrations/visionaudioforge/02-core-service-spec.md](../integrations/visionaudioforge/02-core-service-spec.md)). |
| **Capture agent disconnect** | Session pauses | Core retains session state for 5 minutes awaiting reconnect. After timeout, session closes; agent reconnect creates a new session. | Agent reconnect within window resumes seamlessly. |
| **Service-level OOM / crash** | All sessions die | ECS health check fails; task restarts; agents reconnect (per their own backoff logic) into new sessions. | Auto-recovery in <30 s. Lost: in-memory event queue contents. |
| **EsportsForge backend down** | Webhooks fail | Per "Webhook delivery failure" above. | EsportsForge backend recovers; in-flight events lost (acceptable in v1). |
| **Adapter ML model corrupt** | Adapter raises on init | Core fails to load that title's adapter. Sessions for that title get `capture_allowed: false`. Other titles unaffected. | Operator ships replacement model; adapter reload on next deploy. |

### Graceful degradation principle

Every failure mode preserves either a **partial signal** (events emit with degraded confidence) or a **clear unavailable state** (frontend banner, capture-allowed false). The core never silently emits low-quality events without flagging them, and never blocks the agent from connecting.

---

## Compliance with FORGE_ARCHITECTURE_PATTERN.md

| Rule | How this spec satisfies it |
|---|---|
| **1. Multi-dimensional from day one.** | The adapter pattern covers all 11 titles from day one. Madden 26 ships first; the registry and dispatch path support every title. Adding CFB / NBA / etc. requires zero core code changes. |
| **2. Consumers never call external APIs directly.** | The capture agent talks only to this core's WS endpoint. EsportsForge agents and frontend pages consume via the event bus and webhook surface. No consumer (page, agent, or downstream service) calls Tesseract, ONNX, OpenCV, or any ML provider directly — the core owns those contracts. |
| **3. Logic lives in the Forge, not the consumer.** | OCR, formation detection, snap detection, state assembly, integrity gating, event de-duplication — all of it in the core or its adapters. Consumer pages just subscribe to typed events. The reference proof: [docs/specs/03-mock-removal-and-page-wiring.md](03-mock-removal-and-page-wiring.md) documents how each page becomes a thin event subscriber. |
| **4. Events are structured and canonical.** | Universal envelope, 8 sport-archetype payload bases, fixed event taxonomy, Pydantic-typed throughout. Discriminated union by `title` lets consumers pattern-match without losing type safety. New event types require a versioned contract bump, not silent extensions. |
| **5. Adapters are added without core changes.** | Adapters are self-contained modules under `adapters/<title>/`. Adding a new title means: drop a new module, register it in the `ADAPTERS` dict, ship its `hud_signature.png`. No router edits, no event schema edits, no core re-deploy beyond shipping the new adapter package. |

This spec is ready for engineering kickoff once the open architectural questions in [docs/integrations/visionaudioforge/02-core-service-spec.md §"Open architectural questions"](../integrations/visionaudioforge/02-core-service-spec.md) are signed off.
