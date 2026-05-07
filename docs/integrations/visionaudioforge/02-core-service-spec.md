# VisionAudioForge Core Service — Specification

> Companion: [01-capture-agent-spec.md](01-capture-agent-spec.md), [03-event-bus-contract.md](03-event-bus-contract.md), [04-madden26-adapter-spec.md](04-madden26-adapter-spec.md).
> The core service is the hub. Frames in, typed events out. **No title-specific logic lives in the core** — that's the adapters' job.

## Purpose

The core service is the only component that talks to the capture agent and the only component that loads adapters. It owns:

1. WebSocket frame ingestion from agents.
2. Per-session integrity-mode gating (consults EsportsForge backend).
3. Title detection (which game is the player playing right now?).
4. Adapter routing (hand frames to the right adapter).
5. Event publishing (typed events out to subscribers).
6. Observability (per-session metrics, structured logs).

The core does **not** OCR. Does **not** know what a Cover 3 is. Does **not** read scoreboards. Adapters do all of that.

## Recommendation: stack and deployment

**Stack: FastAPI + asyncio + Pydantic, deployed as a separate ECS service.**

Why FastAPI:
- Same stack as the EsportsForge backend → zero new ops surface, shared Pydantic schemas, shared logging infra.
- WebSockets + async are first-class.
- Existing Dockerfile pattern in the repo translates directly.

Why a separate service (not part of the EsportsForge backend):
- Different scaling profile. The EsportsForge backend serves request/response API traffic; the core service handles long-lived WS connections with steady CPU load. Mixing them on one container leads to head-of-line blocking.
- Independent deploy cadence. Adapters change weekly; the EsportsForge API changes much less. Keeping them separate lets each ship without the other's regression risk.
- Anti-cheat blast radius. The core handles raw frame data. Quarantining it in its own service simplifies the threat model and audit story.

Default port: **8100** (matches the constant already in `vision_client.py`'s `_DEFAULT_ENDPOINT`). In dev: `http://localhost:8100`. In prod: `wss://vision.esportsforge.gg` (separate ECR repo, separate ECS service, behind the same ALB as the API with a hostname split).

## Service surfaces

### WebSocket: `/ws/ingest`

Capture agents connect here. See Doc #01 for the wire protocol. Auth is `Authorization: Bearer <api_key>` on the upgrade. The core validates the key against EsportsForge backend's `/api/v1/auth/validate-capture-key` (new endpoint to add in EsportsForge backend, see "External dependencies").

### WebSocket: `/ws/events/{session_id}`

Subscribers (the EsportsForge frontend, debug clients) listen for events on this socket. Auth is the standard NextAuth session JWT. Read-only.

The EsportsForge backend does **not** subscribe via WS — it receives events via webhook (see below) so it doesn't need to maintain stateful connections.

### HTTP: `POST /api/v1/sessions/open`

Called by the EsportsForge backend when a player starts a vision session (e.g., presses "Start session" in the dashboard). Body:

```json
{
  "user_id": "5041bbe7-...",
  "active_title": "madden26",   // hint, not authoritative
  "integrity_mode": "ranked",   // current Integrity Mode at session start
  "webhook_url": "https://api.esportsforge.gg/api/v1/visionaudio/events"
}
```

Returns:

```json
{
  "session_id": "ses_01HXXX",
  "agent_endpoint": "wss://vision.esportsforge.gg/ws/ingest",
  "expires_at": "2026-05-06T23:30:00Z"
}
```

The session_id is what the agent's `Authorization: Bearer <api_key>` is later bound to. The session has a TTL (default 4h, refreshed via heartbeat).

### HTTP: `POST /api/v1/sessions/{session_id}/integrity-mode`

Called by EsportsForge backend when the player changes Integrity Mode mid-session. Triggers `capture_pause` / `capture_resume` to the agent.

### HTTP: `POST /api/v1/sessions/{session_id}/close`

Idempotent session teardown.

### HTTP: `GET /api/health`

Standard health check. Returns `{"status": "healthy", "active_sessions": N}`.

### Outbound webhook: events → EsportsForge backend

Events from the bus are POSTed in batches to the `webhook_url` provided at session open. Batches every 250ms or every 32 events, whichever first.

```json
{
  "session_id": "ses_01HXXX",
  "user_id": "5041bbe7-...",
  "events": [
    { /* see 03-event-bus-contract.md for shape */ },
    ...
  ]
}
```

EsportsForge backend acks 200; on non-2xx the core retries with exponential backoff up to 5 attempts then drops (events are not durable in v1 — see Open Question #4).

## Frame processing pipeline

For each frame received from an agent:

```
1. Validate session    ─→ reject if session expired / closed
2. Check integrity gate ─→ drop frame if mode disallows capture
3. Decode JPEG          ─→ numpy array (1080p RGB)
4. Title detect         ─→ if session.title_locked is None: run detector
                          if locked: skip
5. Adapter dispatch     ─→ adapters[session.title].process(frame, session_ctx)
6. Publish events       ─→ enqueue adapter outputs to event bus
7. Drop frame           ─→ no frame retention by default (see Open Question #5)
```

Steps 3–6 are CPU-bound. Run on a thread pool (or process pool for adapters that load ML models) to avoid blocking the asyncio event loop.

Per-session ordering: events from a single session preserve causal order (all from one worker queue per session). Events from different sessions can interleave freely.

## Title detection

A separate component invoked once per session (not per frame). Inputs: a frame buffer (the first ~5 frames from the agent). Outputs: `(title: TitleEnum, confidence: float)`.

**Recommendation v1: heuristic / template-match HUD signature.**

Each adapter ships a `hud_signature.png` — a small (~200×60 px) crop of a stable HUD region that uniquely identifies the title (Madden's down-and-distance bar, Warzone's circle timer, NBA 2K's shot clock, etc.). The detector slides each signature across the frame using ORB feature matching or simple normalized cross-correlation. The title with the highest match score above a threshold wins.

Why heuristic over CNN:
- 11 distinct HUDs, each with a stable signature element. This is a textbook template-match problem.
- No training data required for v1.
- Latency: <50ms per detection on CPU. Acceptable for a once-per-session call.
- We can graduate to a CNN classifier later if title coverage expands or HUD overlays change between game updates.

Confidence threshold: **0.85** to lock. Below 0.85, the detector retries on the next batch of frames. After 30s without confident detection, the core notifies the agent (`session_open` is amended to `active_title: null, capture_allowed: false`) and the dashboard surfaces "Couldn't detect game — please verify the capture source."

The `active_title` hint from `/sessions/open` is used as a tiebreaker when scores are close, not as authoritative truth (player may have launched a different game).

## Adapter contract

Adapters implement a single class:

```python
# Pseudocode — see Doc #04 for the Madden 26 implementation.
class TitleAdapter(Protocol):
    title: TitleEnum
    version: str

    def process_frame(
        self,
        frame: np.ndarray,             # RGB, 1080p assumed (resize upstream if not)
        session: SessionContext,       # frame history, last events, user identity hash
    ) -> list[GameStateEvent]:
        ...
```

Hard requirements on adapters:
- **Pure function semantics.** No network calls, no DB writes, no logging side effects beyond the structured logger passed in via `session.logger`.
- **No process state.** Anything stateful (last formation seen, frame-difference for snap detection) lives in `session` which the core owns.
- **Bounded latency.** Each adapter declares a `max_processing_ms` budget. The core enforces it: if an adapter exceeds budget, the frame is dropped and the breach is logged. Default budget: 80ms.
- **No model loads in `process_frame`.** Adapters lazy-load ML models in their `__init__`; the core constructs them once per worker.

Adapters are loaded via Python entry points or a registry module:

```python
# backend/app/services/integrations/visionaudio/adapters/__init__.py
ADAPTERS: dict[TitleEnum, type[TitleAdapter]] = {
    TitleEnum.MADDEN26: Madden26Adapter,
    TitleEnum.CFB26: CFB26Adapter,
    # ... populated as each adapter ships
}
```

## Anti-cheat / Integrity Mode gating

The core is the gatekeeper. Every frame goes through:

```python
if session.integrity_mode == IntegrityMode.TOURNAMENT:
    drop_frame(reason="integrity_mode_tournament_blocks_capture")
elif session.integrity_mode == IntegrityMode.RANKED:
    if session.title in RANKED_BLOCKED_TITLES:        # Warzone, Fortnite, Valorant
        drop_frame(reason="title_x_ranked_blocks_capture")
    elif not session.is_post_snap and frame_is_pre_snap(frame, session):
        drop_frame(reason="ranked_blocks_pre_snap_capture")
elif session.integrity_mode == IntegrityMode.BROADCAST:
    if session.expose_opponent_data:
        drop_frame(reason="broadcast_mode_hides_opponent_data")
elif session.integrity_mode == IntegrityMode.OFFLINE_LAB:
    pass  # full access
```

(`is_post_snap` etc. are adapter-specific signals; the adapter declares which integrity-mode rules apply.)

If the player switches Integrity Mode mid-session, EsportsForge backend POSTs to `/api/v1/sessions/{id}/integrity-mode` and the core sends `capture_pause` / `capture_resume` to the agent and re-evaluates routing.

This logic is centralised in the core, not the agent (Doc #01 §"Security and trust model" explains why).

## Event bus

**Recommendation v1: in-process asyncio.Queue per session, with a fan-out task that publishes to subscribers (WS subscribers + the EsportsForge webhook).**

Why not Redis Streams / NATS in v1:
- Single-instance deployment is fine for the player counts in Phase 1 (few hundred concurrent sessions).
- In-process queues add zero ops complexity.
- We retain the event schema (Doc #03) so the migration to a durable bus is a transport swap, not a refactor.

When to migrate:
- > 1000 concurrent sessions, OR
- > 1 core service instance behind the LB, OR
- need to retain events for replay/debugging beyond the in-flight window.

At that point: Redis Streams. Same envelope schema; the core publishes to a stream per `session_id`; subscribers (including the webhook publisher) consume from streams.

## State per session

```python
@dataclass
class SessionContext:
    session_id: str
    user_id: str
    user_id_hash: str             # one-way hash, passed to adapters; protects PII
    integrity_mode: IntegrityMode
    title: TitleEnum | None
    title_confidence: float
    title_locked_at: datetime | None
    opened_at: datetime
    last_heartbeat_at: datetime
    frame_count: int
    last_event_id: str | None

    # Adapter-owned state, opaque to core
    adapter_state: dict[str, Any]   # adapter writes/reads this freely

    # Frame history for adapters that need temporal features
    frame_history: deque[FrameRef]   # ring of last N frames, default N=30
```

State is in-memory only. On core restart, all sessions die — the agent reconnects, the core opens a new session, the EsportsForge backend re-creates session metadata. No durability target in v1.

## External dependencies

The core service depends on:

| External | Surface | Owned by |
|---|---|---|
| EsportsForge backend `/api/v1/auth/validate-capture-key` | New endpoint to add — validates an agent's API key | EsportsForge backend team |
| EsportsForge backend `/api/v1/visionaudio/events` | New endpoint to add — receives event webhooks | EsportsForge backend team |
| EsportsForge backend `/api/v1/users/me/integrity-mode` | Existing — read current Integrity Mode | shared |
| Frontend `/dashboard?vision=live` | Subscribes to `/ws/events/{session_id}` for live overlay | frontend team |
| ECS / ALB / Route53 | `vision.esportsforge.gg` hostname split | infra |

These get tracked as Phase 1 dependencies in Doc #05.

## Observability

- Structured logs via `structlog` (same setup as EsportsForge backend, see `app/core/logging.py`).
- Per-session metrics: frames received, frames processed, frames dropped (by reason), event-bus emit rate, adapter processing time p50/p95/p99.
- Per-adapter metrics: which adapter handled this session, detection confidence at lock, processing-budget breaches.
- Health endpoint exposes `active_sessions` and `adapter_versions` so a smoke test can verify a deploy loaded the right adapters.

CloudWatch (or wherever ECS logs go) is the destination. No separate Prometheus in v1.

## Open architectural questions

These deferred from Doc #00. Resolutions for v1:

| # | Question | v1 decision |
|---|---|---|
| 1 | Capture agent distribution | See Doc #01 — Python + PyInstaller, signed Windows installer. |
| 2 | Core deployment | Separate ECS service. Same ALB, hostname split (`vision.*`). |
| 3 | Title detector model | Heuristic / template-match HUD signature. CNN deferred. |
| 4 | Event bus durability | In-process asyncio queues. Redis Streams once we cross thresholds. |
| 5 | Frame storage | **No persistence in v1.** Frames are processed and dropped. Event payloads (which contain only typed game state, never pixels) flow to the EsportsForge backend and persist there per its own retention policy. Privacy-by-default. |

## What this spec does not decide

- **Adapter implementation details.** Each adapter has its own spec doc (Doc #04 for Madden 26 is the template).
- **Event payload shapes.** That's Doc #03's job.
- **Phase 1 timeline.** That's Doc #05.
