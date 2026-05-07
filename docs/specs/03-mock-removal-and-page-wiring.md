# Spec — Mock Removal and Per-Page Adapter Wiring

> **Reference:** [docs/FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md). The migration in this spec is the moment the codebase stops violating Rules 2, 3, and 5 — the simulated `vision_client.py` exists today as a fake adapter that consumers call directly, with logic in pages and a single hardcoded title surface. After this migration, consumers are pure event subscribers.
> **Companion specs:** [docs/specs/01-capture-agent.md](01-capture-agent.md), [docs/specs/02-visionaudioforge-core.md](02-visionaudioforge-core.md).
> **Status:** Specification only. No implementation code.

## Purpose

Replace the simulation mock at `backend/app/services/integrations/visionaudio/vision_client.py:132` with the real VisionAudioForge core service, and rewire every consumer (six pages plus one analytics surface) from direct `vision_client` calls to event subscriptions. Achieve this without breaking the existing UI flows the player sees today.

The mock has been pretending to be a real Forge for months. Today it returns canned game-state when called by `/api/v1/visionaudio/capture` and a few page-level UIs. The migration converts every call site into a subscriber, and once all sites are migrated, the mock module is deleted.

This is a **migration spec**, not a feature spec. The deliverable is a sequence of changes that produce zero player-visible regression while the substrate underneath flips from fake to real.

---

## 1. Exact file changes to remove the simulation mock

### What lives in the repo today

The simulation mock is concentrated in three backend files plus a frontend service module that reaches the backend via REST.

**Backend files involved:**

| File | What it currently does | What changes |
|---|---|---|
| `backend/app/services/integrations/visionaudio/vision_client.py` | Simulated pipeline. Lines 132–172 contain the `# Simulate vision processing pipeline` block that returns hardcoded objects + game_state by title. | **Replaced.** The class `VisionClient` becomes a thin async wrapper over the real VAF core service's HTTP/WS surfaces. The `process_screen_capture` method becomes a single-frame request to the core's `/api/v1/single-shot/analyse` endpoint (a new core surface for one-off frame analysis, used only by legacy consumers during migration). The `process_video_replay` method (also currently simulated, lines 178+) becomes a request to the core's `/api/v1/replay/analyse` endpoint. |
| `backend/app/api/v1/endpoints/visionaudio.py` | Mounts `_vision = VisionClient()` at module load and exposes `/api/v1/visionaudio/connect`, `/capture`, `/replay`, `/anti-cheat`. | **Marked deprecated.** All four endpoints stay but log a structured-warning each invocation: `vision_client_deprecated_call`. The module is removed in a follow-up PR after every consumer is migrated. The router stays mounted for the migration window. |
| `backend/app/api/v1/endpoints/drills_vision.py` | Drill-specific endpoint that proxies to the upstream `VisionAudioForge` service via vision_client. | **Marked deprecated.** Same pattern. Once Drill Lab subscribes via the event bus, this endpoint is removed. |
| `backend/app/services/integrations/visionaudio/film_visual.py`, `formation_recognition.py`, `visual_telemetry.py`, `scene_reader.py`, `clip_export.py` | Sibling stubs imported by `visionaudio.py`. All currently simulation-only. | **Folded into the core.** These five modules' responsibilities migrate into appropriate adapter modules (e.g., formation_recognition → `adapters/madden26/formation_detector.py`). The standalone modules are removed in the same PR as `vision_client.py`. |

**Frontend files involved:**

| File | What it currently does | What changes |
|---|---|---|
| `frontend/src/lib/services/visionaudioforge.ts` | `VisionAudioForgeService` class. Calls REST endpoints on the EsportsForge backend that proxy to the mocked `vision_client.py`. | **Reshaped.** Becomes the WebSocket subscriber to `/ws/events/{session_id}`. Existing imperative methods (`startDrillMonitoring`, etc.) become thin wrappers that return event streams instead of polling REST endpoints. Method signatures preserved so callers compile during migration. |
| `frontend/src/app/(dashboard)/drills/simlab/page.tsx` | Calls `VisionAudioForgeService.startDrillMonitoring`, `isAvailable`, `getCaptureSource`. | **Subscribes to events.** Lines 482–514 get rewritten to subscribe to `PLAY_STARTED` events instead of polling. Visible behaviour unchanged. |
| `frontend/src/components/analytics/FilmRoom.tsx` | References `VisionAudioForge` in the UI banner. No real call site. | **Subscribes to a frame cache.** New behaviour added — see §2 for Analytics Film Room wiring. |
| `frontend/src/app/help/page.tsx`, `frontend/src/app/admin/page.tsx` | Display "VisionAudioForge" status string. | No code changes. Display string stays. |

### Migration sequence inside the codebase

The mock cannot be deleted in one shot because the WS-subscription infrastructure has to exist first. The order of operations:

1. **Parallel build (no deletes).** Ship the real VAF core service per [02-visionaudioforge-core.md](02-visionaudioforge-core.md). It runs alongside the mock; nothing consumes it yet.
2. **Parallel wire (consumers gain dual subscriptions).** Each page is updated to subscribe to the event bus via the new WebSocket. The page emits a feature-flag-gated render: if `VAF_REAL_PIPELINE_ENABLED=true`, render from event bus; otherwise, render from the mocked REST endpoint as today. Both paths are exercised in shadow during this window.
3. **Cutover (per page, gradual).** Flip the feature flag for one page (Drill Lab) for staff users. Monitor. Roll out to all users after observation window. Repeat for SimLab, Gameplan, Arsenal, War Room. Analytics Film Room is the last to cut over because its frame-cache dependency is heavier.
4. **Mock deletion (after cutover stable for 30 days).** Delete `vision_client.py`, the four sibling stub modules, and the deprecated endpoints. Update `router.py` to drop the deprecated routes. Update `frontend/src/lib/services/visionaudioforge.ts` to remove REST polling fallback paths.

### The literal line-132 fix

Before the mock can be deleted, the line 132 block (and the methods that contain it) needs a clean cutover path. The replacement contract for `VisionClient.process_screen_capture` once the real pipeline is enabled:

| Before (today) | After (post-cutover) |
|---|---|
| `await _vision.process_screen_capture(image_bytes, resolution, title, analysis_type)` returns synthetic `ScreenCaptureResult` | `VisionClient` is removed entirely. The method is no longer callable. Any code path that imports `VisionClient` is a deletion target. |
| Mock decides title-specific shape based on `title` parameter | Title is server-detected; consumers don't pass it. Consumer subscribes to bus and pattern-matches on the event's `title` field. |
| Single REST call per frame | Stream of events per session, fan-out to many subscribers, no per-frame REST call from any consumer. |

The block at line 132 is not "fixed" in the sense of being patched in place. It is **removed** along with the surrounding methods, and consumers migrate to a fundamentally different consumption shape (subscriber, not caller). The migration spec below covers how to do that without breaking flows.

---

## 2. Per-page adapter subscriptions to VisionAudioForge events

Each consumer page subscribes to a small, well-defined set of events. The page's existing imperative call site is replaced with an event subscriber that updates the page's React state when matching events arrive.

The frontend hook surface is `useVisionEvents(filter)`, a React hook implemented in `frontend/src/hooks/useVisionEvents.ts` (new file). It opens a WebSocket to `/ws/events/{session_id}`, applies the predicate filter, and returns the latest matching event plus a state machine of "current state" derived from the event stream.

### Drill Lab — `formation_detected` events

**File:** `frontend/src/app/(dashboard)/drills/page.tsx` (and the SimLab counterpart at `drills/simlab/page.tsx`).

**Current behaviour:** During a drill, the player runs a scenario. The page calls `VisionAudioForgeService.startDrillMonitoring` which polls a backend endpoint that polls the mocked `vision_client.py`.

**New behaviour:** The page subscribes to `FORMATION_LOCKED` events for the active session. When a formation is locked, the page records the rep, advances the drill state, and surfaces correction feedback if the formation differs from the drill's target formation.

**Subscription:**

```typescript
const formationEvent = useVisionEvents({
  event_type: "FORMATION_LOCKED",
  // implicit: scoped to current session_id by the hook
});
```

**Reaction:**
- Increment rep counter on each new `FORMATION_LOCKED` event.
- Compare `payload.offensive_formation` to the drill's target formation; if mismatch, push a correction prompt.
- Confidence threshold: only count the rep if `event.confidence >= 0.85`.

**Mock-removal impact:** the existing imperative `startDrillMonitoring(callback)` is replaced by a hook subscription. The page's drill-state machine is otherwise unchanged.

### SimLab — `play_called` events

**File:** `frontend/src/app/(dashboard)/drills/simlab/page.tsx`.

**Current behaviour:** Lines 482–514 call `VisionAudioForgeService.startDrillMonitoring` similarly to Drill Lab. SimLab's "watching mode" auto-detects each rep.

**New behaviour:** Subscribes to `PLAY_STARTED` events (universal across football/baseball/basketball — basketball's "play_called" is the offensive action signal, baseball's is pitch release, football's is the snap). The page's "watching mode" rewires from polling to event-driven.

**Subscription:**

```typescript
const playEvent = useVisionEvents({
  event_type: "PLAY_STARTED",
});
```

**Reaction:**
- Mark the current rep complete on each new `PLAY_STARTED`.
- Stream the post-snap state via `PLAY_ENDED` (or sport-equivalent terminal event) for scenario-branch decisions.
- For SimLab's "scenario preview" feature, consume `FORMATION_LOCKED` events to choose the right preview to play.

**Mock-removal impact:** lines 482–514 of `simlab/page.tsx` are the targeted refactor; the rest of the page (UI rendering, scenario state machine) is untouched.

### Gameplan — `defense_shown` events

**File:** `frontend/src/app/(dashboard)/gameplan/page.tsx`.

**Current behaviour:** Gameplan's kill-sheet view today shows static recommendations. There's no real defensive-detection wiring; the page exists in mock-state-only.

**New behaviour:** Subscribes to `COVERAGE_LOCKED` events (the universal "defense_shown" signal — football's defensive coverage, basketball's defensive scheme). When a coverage is detected, the kill-sheet UI auto-highlights plays known to beat that coverage from the player's gameplan.

**Subscription:**

```typescript
const coverageEvent = useVisionEvents({
  event_type: "COVERAGE_LOCKED",
});
```

**Reaction:**
- Highlight kill-sheet plays whose `beats[]` array (per the play schema) contains the detected coverage.
- Surface a banner: "Cover 3 detected — try Gun Trips Mesh Spot."
- Time-out the highlight after 30 s (post-snap, the coverage is moot).

**Mock-removal impact:** Gameplan's kill-sheet view gains a new real-time overlay that didn't exist before. No mock to remove because Gameplan doesn't currently call `vision_client` — this is greenfield wiring.

### Arsenal — `game_state_changed` events for weapon trigger evaluation

**File:** `frontend/src/app/(dashboard)/arsenal/page.tsx` plus the new service `frontend/src/lib/services/weaponTriggerEvaluator.ts`.

**Current behaviour:** Arsenal weapons declare their trigger conditions in static metadata. There's no live evaluation — the player has to scroll Arsenal manually.

**New behaviour:** Subscribes to a composite of game-state events (`SNAPSHOT`, `FORMATION_LOCKED`, `COVERAGE_LOCKED`, `DOWN_AND_DISTANCE`). A `WeaponTriggerEvaluator` service runs each weapon's trigger predicate against the current state and surfaces "weapons that should fire now" in a banner.

**Subscription:**

```typescript
const gameState = useVisionEvents({
  event_type: ["SNAPSHOT", "FORMATION_LOCKED", "COVERAGE_LOCKED", "DOWN_AND_DISTANCE"],
});
```

**Reaction:**
- The evaluator iterates over the player's owned weapons; for each, runs `weapon.shouldFireFor(currentState)`.
- Weapons that match get visually elevated in the Arsenal grid (border glow, sort-to-top).
- Optional VoiceForge cue: "Cover 3, third and long, your secret weapon is Gun Trips Mesh Spot." (Wired through VoiceForge per its own spec.)

**Mock-removal impact:** Arsenal currently has no mock to remove. This is new wiring that depends on the real event stream existing. **Cutover-gated** — Arsenal's live trigger feature is feature-flagged and only enabled once the event bus is solid.

### War Room — `ranked_session_started` events

**File:** `frontend/src/app/(dashboard)/war-room/page.tsx`.

**Current behaviour:** War Room shows the opponent profile, gameplan summary, and mental prep statically. No live awareness of "are you in a ranked match right now."

**New behaviour:** Subscribes to `MATCH_STARTED` events filtered by integrity context. When a ranked-mode session begins, the page surfaces context: "Ranked match started against [opponent inferred from VAF + opponent record]. Voice cues paused per Ranked policy."

**Subscription:**

```typescript
const matchEvent = useVisionEvents({
  event_type: "MATCH_STARTED",
  filter: (e) => e.session_id === currentSession,
});
```

**Reaction:**
- Show a live "match in progress" banner.
- Switch the War Room's mid-game-adjustment surface from inert to active (it'll receive `PLAY_ENDED + drive_complete` events; see [03-war-room-page-profile-spec.md](../integrations/voiceforge/03-war-room-page-profile-spec.md)).
- Trigger TiltGuard's mood-check pulse if a configured threshold is met.

**Mock-removal impact:** War Room currently has no mock-call site. This is new wiring. War Room's existing static surfaces (opponent profile, mental prep) stay unchanged.

### Analytics Film Room — frame cache for replay analysis

**File:** `frontend/src/components/analytics/FilmRoom.tsx`.

**Current behaviour:** A panel that references VisionAudioForge in copy ("Powered by VisionAudioForge") but has no functional wiring.

**New behaviour:** Consumes a session's frame cache (kept by the core service for the duration of the session, see below) plus the session's event timeline. Renders a scrubable timeline where the player can step through plays post-game, with each event timestamped against the synced frame snapshots.

**Special architectural note:** Analytics Film Room is the only consumer that needs **frames**, not just events. The default "no frame retention in v1" rule (per [02-visionaudioforge-core.md §"Frame retention"](02-visionaudioforge-core.md)) is **opted out of** for sessions where the player explicitly turns on Film Room recording. Mechanics:

- Player toggles "Record this session for Film Room" in War Room (default off; respects Integrity Mode — Tournament mode disables the toggle entirely).
- VAF core service, on receiving the toggle event, retains a downsampled (1 fps) JPEG cache for the session duration in S3 (lifecycle policy: 7 days, then auto-delete).
- Analytics Film Room calls `GET /api/v1/visionaudio/sessions/{session_id}/replay` which returns `(frames_url, events_url)`.
- Renders a scrubable timeline; click an event → jump to the nearest frame.

**Subscription:**

The page does not subscribe to live events; it consumes the post-session bundle via REST. Live during gameplay is not the use case — this is review-after-the-fact.

**Mock-removal impact:** Film Room copy stays as-is; new functionality lights up once the cache feature ships. **Phase 2 feature** (gated behind Phase 1 of VAF core stabilising).

### Subscription summary table

| Page / Component | Events subscribed | Source surface | Cutover phase |
|---|---|---|---|
| Drill Lab | `FORMATION_LOCKED` | `useVisionEvents` hook | Phase 1, first to cutover |
| SimLab | `PLAY_STARTED`, `PLAY_ENDED`, `FORMATION_LOCKED` | `useVisionEvents` hook | Phase 1, after Drill Lab proven |
| Gameplan | `COVERAGE_LOCKED` | `useVisionEvents` hook | Phase 1, after SimLab |
| Arsenal | `SNAPSHOT`, `FORMATION_LOCKED`, `COVERAGE_LOCKED`, `DOWN_AND_DISTANCE` | `useVisionEvents` + `WeaponTriggerEvaluator` | Phase 1.1 (after stable event stream) |
| War Room | `MATCH_STARTED` (filtered to ranked sessions) | `useVisionEvents` hook | Phase 1.1 |
| Analytics Film Room | Post-session bundle (frames + events) | `GET /api/v1/visionaudio/sessions/{id}/replay` | Phase 2 |

---

## 3. Migration strategy

### Strategy: parallel run with feature-flag cutover

The migration is per-page. At any point during the migration window, some pages are on the real pipeline and others are still on the mock. The two paths coexist behind a feature flag. The mock never forks behaviour during the window — it continues returning the same canned data it does today, so any UI that's still on the mock continues to behave as it does today.

### Feature flag: `VAF_REAL_PIPELINE_ENABLED_<PAGE>`

Per-page flag, evaluated at the consumer level. Granular cutover.

```typescript
// in each page
const useRealPipeline = useFeatureFlag("VAF_REAL_PIPELINE_ENABLED_DRILL_LAB");

useEffect(() => {
  if (useRealPipeline) {
    // subscribe to event bus
  } else {
    // call legacy REST endpoint
  }
}, [useRealPipeline]);
```

Flags are exposed via the EsportsForge backend's existing feature-flag service (or via env var if no flag service exists yet — see Open Questions below).

### Cutover phases

| Phase | Window | What changes |
|---|---|---|
| **Phase 0 — Parallel build** | Weeks 1–3 | VAF core ships per [02](02-visionaudioforge-core.md). Capture agent ships per [01](01-capture-agent.md). Both deploy to staging. No flags flipped; no consumer touches the real pipeline. |
| **Phase 1a — Drill Lab cutover** | Week 4 | Flip flag for staff (~10 users). Monitor: event delivery rate, end-to-end latency, page error rates, manual UX validation. After 7 days stable, flip for all Competitive+ tier users. Free-tier players stay on mock until Phase 1c (they don't see the difference because mock data is what populates their UI today). |
| **Phase 1b — SimLab + Gameplan cutover** | Weeks 5–6 | Same pattern: staff flip → 7-day observation → all-users flip. SimLab depends on Drill Lab being stable because it shares the `FORMATION_LOCKED` infrastructure. |
| **Phase 1c — Arsenal + War Room cutover** | Weeks 7–8 | These pages have new functionality (live triggers, ranked-session awareness) that requires the real pipeline — once flipped, they go from inert to live. No mock equivalent existed; flag flip enables the feature. |
| **Phase 2 — Analytics Film Room** | Weeks 9–10 | Frame-cache feature ships. Player opt-in toggle. Independent of other cutovers. |
| **Phase 3 — Mock deletion** | Week 12+ | After 30 days of all-page stability on the real pipeline, delete `vision_client.py`, sibling stubs, deprecated endpoints, and REST-fallback paths in the frontend service. |

### Per-cutover acceptance criteria

A cutover is considered stable and promoted when:

- Event delivery rate to the page's hook ≥99% over 24 hours.
- End-to-end latency p95 ≤2 s.
- Page-level error rate (caught exceptions, sentry breadcrumbs) increases by <10% vs. mock baseline.
- No critical bugs reported via in-app feedback in the prior 7 days.

If any criterion fails, the flag flips back to mock and the issue is debugged before re-cutover.

### Data integrity during the parallel window

Both code paths emit page-level state. While the flag is on, the mock REST polling is **not called** by the consumer (the hook subscribes instead). The mock endpoint stays mounted in the backend but receives zero traffic from real users. This avoids dual-write inconsistency.

### Migration order rationale

The cutover order is not arbitrary:

1. **Drill Lab first** — simplest event subscription (`FORMATION_LOCKED` only), most-mocked page today, easiest to detect regression because rep counting is visible and quantified.
2. **SimLab second** — depends on the same `FORMATION_LOCKED` infrastructure; second-easiest sanity check.
3. **Gameplan third** — net-new functionality, but contained (a single banner in the kill-sheet view).
4. **Arsenal fourth** — new functionality; needs the full event stream stable.
5. **War Room fifth** — new functionality; least visible if it breaks (player still sees the static War Room UI).
6. **Analytics Film Room last** — heaviest dependency (frame cache), independent feature flag, no urgency.

---

## 4. Rollback plan

### Trip wires

Each cutover ships with monitoring trip wires. If any fires, the flag auto-flips back and an alert pages oncall.

| Trip wire | Threshold | Action |
|---|---|---|
| Event delivery rate | <90% over 5 minutes | Auto-flip flag back; page oncall |
| Page error rate | >2× baseline | Auto-flip flag back |
| End-to-end latency p99 | >5 s for 5 minutes | Manual investigation; flag stays on but alarm |
| WS connection failure rate | >5% | Auto-flip flag back |
| User-reported "broken" feedback | >3 reports in 24 hours | Manual investigation; consider flip-back |

### Manual rollback

Operator can flip a per-page flag via the feature-flag dashboard at any time. Rollback time: <30 s per flag. The mock code stays in tree until the Phase 3 deletion, so the rollback path is always available.

### Rollback invalidates which artefacts

Rolling back a page-level cutover does not affect:
- Other pages that have already cutover (they keep using the real pipeline).
- The capture agent (it stays running; frames keep flowing into the core).
- The core service (it keeps publishing events; subscribers other than the rolled-back page keep consuming).

The rolled-back page silently drops its event subscription and resumes calling the mock REST endpoint. From the player's perspective, behaviour returns to "today's mocked experience."

### When rollback is permanent vs. transient

- **Transient (most cases):** auto-rollback fires, oncall investigates, fixes the issue, flag flips back forward within hours-to-days.
- **Permanent (architectural failure):** if the real pipeline cannot be made to perform within the latency budget, or if a critical bug surface only when ranked H2H volume hits the system, the flag stays off indefinitely while the team replans. The mock lives on.

The 30-day stability window before mock deletion is specifically to surface "permanent" issues during the migration period. Don't delete the mock until that window passes.

### What's NOT recoverable

If the player has opted into Analytics Film Room frame caching, those S3 frames exist regardless of rollback. They persist for 7 days then auto-delete per the lifecycle policy. Rollback doesn't recall them but they're harmless — the player can simply not view them.

---

## 5. Open questions for sign-off

1. **Feature flag infrastructure.** EsportsForge backend doesn't have a dedicated feature-flag service today. Options: (a) ship LaunchDarkly integration, (b) use a simple env-var-driven flag table in Settings, (c) use the existing Integrity Mode mechanic as a proxy (Offline Lab = real pipeline; Ranked = mock until stable). Recommendation: (b) for v1 simplicity; (a) when usage justifies. Decision needed before Phase 1a.

2. **Frame cache cost.** Analytics Film Room's S3 cache at 1 fps × ~50 KB JPEG × 1-hour sessions × N concurrent recording players = bandwidth + storage cost. Need a usage estimate and a budget cap. Recommendation: cap per-session at 30 minutes recorded, default-off, opt-in only.

3. **Backend webhook delivery — durable or fire-and-forget.** The core service sends events to EsportsForge backend via webhook. v1 is fire-and-forget with retries. If a critical event drops (e.g., `MATCH_STARTED` doesn't reach the War Room subscriber), the page misses a state transition. Decision: do we add a Redis Streams durable bus in v1 (per the open question in [02-visionaudioforge-core.md](02-visionaudioforge-core.md)) or accept the loss probability? Recommendation: ship in-process v1, monitor loss rate, upgrade if it exceeds 0.1% per session.

4. **Mock-deletion bar.** "30 days of all-page stability" is the proposal. Some PMs / eng leads may want longer (60 days). Decision needed before Phase 3.

---

## Compliance with FORGE_ARCHITECTURE_PATTERN.md

This migration is the cleanup that brings the codebase into compliance. Pre-migration, the simulated `vision_client.py` violates Rules 2 and 3 — it's an external-API stand-in that consumers call directly with logic baked into the call site. Post-migration:

| Rule | How the migration produces compliance |
|---|---|
| **1. Multi-dimensional from day one.** | The migration is the moment the codebase stops hardcoding Madden-shaped responses. Each consumer subscribes to a typed event stream that's title-aware via the envelope's `title` field. Adding CFB/NBA/etc. requires zero further consumer changes. |
| **2. Consumers never call external APIs directly.** | Today, pages reach into `VisionAudioForgeService` which proxies to `vision_client.py`'s simulated pipeline. The migration replaces every direct call with an event subscription. The capture agent talks to the core; the core talks to ML services; consumers see only typed events. The vector for "consumer makes a Claude vision call directly" is permanently closed. |
| **3. Logic lives in the Forge, not the consumer.** | Pre-migration, the SimLab page had drill-monitoring polling logic, the Gameplan page had no live coverage logic at all (just static recommendations), Arsenal had no live trigger logic. Post-migration, pages contain only render logic: subscribe → derive UI from event payload. All vision logic lives in the core's adapters. |
| **4. Events are structured and canonical.** | The migration commits the codebase to subscribing against the universal event-bus contract (defined in [02-visionaudioforge-core.md §3](02-visionaudioforge-core.md)). Adding a new event type requires a contract bump, not silent extension. Subscribers pin to the schema version they consume. |
| **5. Adapters are added without core changes.** | Once migration is done, adding the CFB / NBA / EA FC / etc. adapters is purely a server-side change. None of the consuming pages need code edits. The hooks are predicate filters over the event envelope; new titles simply produce events with new `title` discriminators that existing subscriptions either match or ignore by predicate. |

This spec is ready for engineering kickoff once:
- The capture-agent build per [01](01-capture-agent.md) is in progress (Phase 0 of this migration depends on the agent existing).
- The VAF core build per [02](02-visionaudioforge-core.md) is in progress (Phase 0 of this migration depends on the core existing).
- The four open questions above (§5) have signed-off resolutions.
