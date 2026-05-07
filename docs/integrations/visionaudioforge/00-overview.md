# VisionAudioForge — Architecture Overview

> **Read this first.** This is the entry point for every VisionAudioForge spec. Architecture is multi-title from day one. Madden 26 is the *first* adapter, not the only one.

## Why this document set exists

EsportsForge's downstream brain (the 57 agents — GameplanAgent, OpponentScout, MetaBot, ImpactRank, TiltGuard, etc.) is fully wired and assumes a stream of typed game-state events. Today those events come from `vision_client.py` which returns hardcoded simulation data. **Production needs a real ingestion pipeline.**

The current `backend/app/services/integrations/visionaudio/vision_client.py` is a stub. It accepts no real frames and returns Madden-shaped mock state regardless of what's on screen. Replacing it requires:

1. **A capture agent** running on the player's PC that pulls frames from a capture card (PS5/Xbox via HDMI) or local screen.
2. **A core service** that detects which game is being played and routes frames to the right adapter.
3. **Eleven title adapters** (one per EsportsForge title) that turn pixels into typed game-state events.
4. **An event bus contract** so every downstream agent reads the same shape regardless of source title.

## Document map

| # | Doc | Audience | Purpose |
|---|---|---|---|
| 01 | [Capture Agent](01-capture-agent-spec.md) | Engineer building the CLX-PC-side capture binary | What runs on the player's PC. Title-agnostic. Hands frames to core. |
| 02 | [Core Service](02-core-service-spec.md) | Engineer building the VisionAudioForge backend | Frame ingestion, title detection, adapter routing, anti-cheat gating, event publishing. |
| 03 | [Event Bus Contract](03-event-bus-contract.md) | Anyone subscribing to events (frontend, EsportsForge backend, every agent) | The discriminated-union schema that all 11 titles publish to. Locked surface. |
| 04 | [Madden 26 Adapter](04-madden26-adapter-spec.md) | Engineer building the first adapter | HUD regions, OCR pipeline, formation detector, state assembler. Proves the pattern. |
| 05 | [Phase 1 Milestones](05-phase-1-milestones.md) | Tech lead planning the build | Day-by-day milestones for the Madden-first ship. |

Adapters 2–11 will each get their own `docs/integrations/visionaudioforge/adapters/<title>.md` written when their phase starts. The Madden adapter spec (#04) is the template.

## Architecture at a glance

```
┌─────────────────┐    HDMI     ┌─────────────────────┐    WS frames    ┌──────────────────────┐
│  PS5 / Xbox /   │ ─────────▶  │  Capture Agent      │ ──────────────▶ │  VisionAudioForge    │
│  PC game        │             │  (CLX PC, native)   │   ~10–15 fps    │  Core Service        │
└─────────────────┘             │  - title-agnostic   │   JPEG batches  │  (FastAPI :8100)     │
                                │  - integrity-aware  │                 │                      │
                                └─────────────────────┘                 │  ┌────────────────┐  │
                                                                        │  │ Title detector │  │
                                                                        │  └────────┬───────┘  │
                                                                        │           ▼          │
                                                                        │  ┌────────────────┐  │
                                                                        │  │ Adapter router │  │
                                                                        │  └────────┬───────┘  │
                                                                        │   ┌───┬───┴┬───┬───┐ │
                                                                        │   │M26│CFB │NBA│...│ │ ← title adapters
                                                                        │   └─┬─┴──┬─┴─┬─┴───┘ │
                                                                        │     ▼    ▼   ▼       │
                                                                        │  ┌────────────────┐  │
                                                                        │  │  Event bus     │  │
                                                                        │  └────────┬───────┘  │
                                                                        └───────────┼──────────┘
                                                                                    │
                                       ┌────────────────────────────────────────────┴───────────┐
                                       ▼                                                        ▼
                            ┌──────────────────────┐                            ┌──────────────────────┐
                            │ EsportsForge backend │                            │ Frontend dashboard   │
                            │ (the 57 agents)      │                            │ (live overlay UI)    │
                            └──────────────────────┘                            └──────────────────────┘
```

## Hard architectural rules

1. **Capture agent never knows about titles.** It captures frames and forwards them. Title detection happens server-side (the player can switch games mid-session).
2. **Frontend never receives raw frames.** The dashboard subscribes to typed events from the bus, not pixels. Privacy/bandwidth/anti-cheat reasons.
3. **Anti-cheat gating runs in the core service, not the agent.** The agent sends every frame; the core decides whether to process based on the user's current Integrity Mode (queried from EsportsForge backend at session start). This means the agent doesn't need to be trusted to enforce mode rules.
4. **Adapters are pure functions of state.** No network calls, no DB writes. They take frames + session context, return events. All side effects happen in the core after the adapter returns.
5. **The event bus contract is the API.** Adapter authors implement against it; agent authors consume from it. Change requires a versioned bump and migration plan.
6. **One title at a time per session.** Title detection locks once confident; doesn't re-detect mid-game. If the player switches titles, they restart the session. (Future v2 may relax this.)

## Title roster (locked for the build)

The 11 EsportsForge titles, grouped by sport-archetype because adapter complexity correlates more with archetype than individual title:

| Archetype | Titles | Adapter complexity |
|---|---|---|
| American football | Madden 26, EA Sports CFB 26 | High (HUD-dense, formation reads). Builds together. |
| Basketball | NBA 2K26 | Medium (HUD-light, action-recognition heavy). |
| Soccer | EA FC 26 | Medium (continuous play; HUD is sparse but readable). |
| Baseball | MLB The Show 26 | Medium (discrete states, clear HUD). |
| Battle royale FPS | Warzone, Fortnite | High (build-mode adds dimension; HUD in motion). |
| Combat sport | UFC 5, Undisputed | Medium (round-based, damage HUD). |
| Golf | PGA TOUR 2K25 | Low (slow-paced, deterministic HUD). |
| Card | Video Poker | Low (static HUD, OCR-dominant). |

Phase order (recapped from prompt): Madden → CFB → (NBA, EA FC, MLB) → (Warzone, Fortnite) → (UFC 5, Undisputed) → (PGA, Video Poker). Earlier phases unlock platform value for the largest player segments.

## What "ready to test against PS5" means

After **Phase 1**, hooking the CLX PC to PS5 with Madden 26 running will mean:
- Capture agent runs on the PC, ingests HDMI feed, forwards frames.
- Core service detects Madden 26 and routes to its adapter.
- Adapter publishes `score_change`, `play_ended`, `down_distance_change`, `formation_locked` events to the bus.
- EsportsForge dashboard agents react to **real game state** (not mock data).
- Anti-cheat gating: Tournament mode disables capture; Ranked mode allows post-snap analysis only; Offline Lab mode is unrestricted.

CFB 26 follows ~5–7 days later. Other titles incrementally.

## Open architectural questions (for review before Phase 1 build starts)

1. **Capture agent distribution.** Native Windows installer? Electron app? Python+PyInstaller? Decision deferred to Doc #01 with recommendation.
2. **Core service deployment.** Same Docker host as EsportsForge backend, or separate ECS service? Decision deferred to Doc #02.
3. **Title detector ML model.** Heuristic (template-match HUD signature) or small CNN? Decision deferred to Doc #02.
4. **Event bus durability.** In-process asyncio queues v1 (lose events on crash) vs Redis Streams v1 (durable, more ops). Decision in Doc #02.
5. **Frame storage.** Do we retain frames for replay/debugging? GDPR/privacy implications. Decision deferred — default v1: no frame storage, only events.

These are flagged in their respective spec docs with explicit recommendations.
