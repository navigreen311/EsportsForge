# VoiceForge — Architecture Overview

> **Read this first.** Entry point for every VoiceForge spec. VoiceForge is the **output** counterpart to VisionAudioForge's input. Architecture is title-aware AND page-aware from day one. Madden 26 + War Room is the *first* language-profile + page-profile combination, not the only one.

## Why this document set exists

EsportsForge already ships frontend voice surfaces (`useVoiceForge.ts` hook, `VoiceForgeService` class, six stubbed Python modules under `backend/app/services/integrations/voiceforge/`). Today these route to a fictional `https://api.voiceforge.greencompanies.com/v1` endpoint and contain no real synthesis, no recognition, and no awareness of which sport / which page / which subscription tier is asking.

Production needs a real voice service that:
- Synthesises speech in real time (TTS)
- Recognises voice commands (STT, deferred to Phase 6)
- Routes through a **multi-dimensional matrix**: title × page × subscription tier × integrity mode
- Manages a priority queue with interruption + game-audio ducking
- Reads the player's coaching tone (Intense / Standard / Calm) and briefing speed (Slow / Normal / Fast) from Settings
- Consumes typed game-state events from VisionAudioForge and turns them into spoken cues

This is fundamentally different from "TTS that reads strings out loud." Football voice cadence (long pre-snap pauses) breaks NBA cues (continuous play). War Room briefings are 5-minute structured monologues; In-Game cues are 1–2 word interjections. The architecture must support both, and everything between, without retrofits.

## Document map

| # | Doc | Audience | Purpose |
|---|---|---|---|
| 01 | [Core Service](01-core-service-spec.md) | Backend engineer | Synthesis, recognition (deferred), queue manager, router, ducking. Stack + deployment. |
| 02 | [Madden 26 Language Profile](02-madden26-language-profile-spec.md) | Voice/content engineer | Football vocabulary, sport cadence, phonetic guides, tone variants. Pattern for the other 10 languages. |
| 03 | [War Room Page Profile](03-war-room-page-profile-spec.md) | Voice/content engineer | Pre-game briefing template, mid-game adjustments, mood update flow, mental reset prompts. Pattern for the other 8 pages. |
| 04 | [Routing Matrix](04-routing-matrix.md) | Anyone wiring a page to VoiceForge | The title × page × tier × mode matrix. How cells map to scripts. Conflict resolution. |
| 05 | [Priority + Interruption Rules](05-priority-and-interruption-rules.md) | Anyone authoring a script | Queue priority, interruption semantics, cooldowns, ducking ramp. |
| 06 | [Subscription Tier Gating](06-subscription-tier-gating.md) | Backend + product | Free / Competitive / Elite / Team — what voice surfaces each tier unlocks. |
| 07 | [Integrity Mode Anti-Cheat Gating](07-integrity-mode-gating.md) | Backend + compliance | Tournament / Ranked / Offline Lab / Broadcast — what voice surfaces each mode permits. |
| 08 | [Phase 1 Milestones](08-phase-1-milestones.md) | Tech lead planning the build | Day-by-day milestones for Madden + War Room first ship. |

Language-profile specs 2–11 (CFB, NBA, EAFC, MLB, Warzone, Fortnite, UFC 5, Undisputed, PGA, Video Poker) get written when their phase starts using Doc #02 as the template. Page-profile specs for the other 8 pages (Gameplan, Arsenal, Drills, SimLab, Tournament, Analytics, Dashboard, In-Game) get written using Doc #03 as the template.

## Architecture at a glance

```
                                     ┌─────────────────────────────────────────┐
                                     │  Player's Settings → Game Settings →    │
                                     │  Voice Settings                          │
                                     │  - tone: Intense | Standard | Calm      │
                                     │  - speed: Slow | Normal | Fast          │
                                     │  - master enable, per-page enable        │
                                     └────────────┬────────────────────────────┘
                                                  ▼
   ┌─────────────────────────┐         ┌───────────────────────────────────────────┐
   │  VisionAudioForge       │  events │  VoiceForge Core Service                  │
   │  (typed game state)     │ ──────▶ │  (FastAPI :8200)                          │
   └─────────────────────────┘         │                                           │
   ┌─────────────────────────┐         │  ┌─────────────────────────────────────┐  │
   │  EsportsForge agents    │  cues   │  │  Multi-dimensional router          │  │
   │  (GameplanAgent, etc.)  │ ──────▶ │  │  title × page × tier × mode → cell  │  │
   └─────────────────────────┘         │  └────────────────┬────────────────────┘  │
                                       │                   ▼                        │
                                       │  ┌─────────────────────────────────────┐  │
                                       │  │  Script template selection          │  │
                                       │  │  Madden + WarRoom → "Pre-game"...   │  │
                                       │  └────────────────┬────────────────────┘  │
                                       │                   ▼                        │
                                       │  ┌─────────────────────────────────────┐  │
                                       │  │  Tier + Integrity-mode gates         │  │
                                       │  │  (drop, downgrade, or pass-through) │  │
                                       │  └────────────────┬────────────────────┘  │
                                       │                   ▼                        │
                                       │  ┌─────────────────────────────────────┐  │
                                       │  │  Voice queue (priority + interrupt) │  │
                                       │  └────────────────┬────────────────────┘  │
                                       │                   ▼                        │
                                       │  ┌─────────────────────────────────────┐  │
                                       │  │  TTS synthesis (ElevenLabs)         │  │
                                       │  └────────────────┬────────────────────┘  │
                                       │                   ▼                        │
                                       └───────────────────┼────────────────────────┘
                                                           ▼
                                          ┌────────────────────────────────────────┐
                                          │  Audio out + duck signal               │
                                          │  - browser WebAudio (in-app)            │
                                          │  - OS audio (capture-agent ducks game)  │
                                          └────────────────────────────────────────┘
```

## Hard architectural rules

1. **Title-aware AND page-aware.** Every cue is selected from a (language × page) cell. A football cue running in basketball, or a War Room cue running in In-Game, is a routing bug.
2. **Sport cadence varies.** Football allows long pre-snap pauses. Basketball is continuous and demands short cues. FPS combat needs 1–2 word interjections. Don't carry football timing assumptions into other titles.
3. **Subscription gating happens in the router, not in scripts.** Free tier never reaches synthesis — text-only fallback. Voice authors don't need to know about tiers.
4. **Integrity Mode is enforced server-side.** Tournament mode silences real-time cues regardless of what the page or script wants. Ranked mode allows some cues, restricts others. Offline Lab is fully unlocked.
5. **The queue manager owns interruption semantics.** Scripts emit cues with declared priority; the queue decides what plays, what interrupts, what ducks. Authors don't manually manage timing.
6. **Game audio is ducked, never silenced, while VoiceForge speaks.** Default −12dB with a 100ms ramp. Player should always hear game audio under the cue.
7. **The 4-dimensional matrix is the API.** Cells are versioned independently. Changing a cell in Madden+WarRoom doesn't ripple to NBA+InGame.

## The matrix at a glance

11 titles × 9 pages × 4 tiers × 4 modes = **1,584 cells** in the full matrix. Most are derivable (defaults inherited from sport-archetype + page profile). The actual hand-authored count is closer to:

- 11 language profiles (one per title)
- 9 page profiles (one per page)
- 8 tier-gating policies (4 tiers × inherit-or-override)
- 4 integrity-mode gating policies

Cells materialise at request time as `(language_profile, page_profile, tier_policy, mode_policy)` — the router composes them; no pre-computed table.

The 9 pages locked for v1:

| Page | What VoiceForge does there |
|---|---|
| War Room | Full pre-game briefings, mood updates, mental reset prompts |
| Gameplan | Read plays on demand ("read me the kill sheet") |
| Arsenal | Step-by-step weapon coaching (pre-execution + post-deployment) |
| Drills | Rep cues, encouragement, correction |
| SimLab | Scenario reads + correction prompts |
| Tournament | Round briefings, between-round resets |
| Analytics | Analyst tone for review playback |
| Dashboard | Daily Forge summary, weekly narrative |
| In-Game | Live coaching during gameplay (anti-cheat-aware) |

## Phase order (recapped)

| Phase | Deliverable | Days |
|---|---|---|
| 1 | Core service + Madden language + War Room page | 10–12 |
| 2 | CFB 26 language + remaining football page profiles (Drill Lab, SimLab, Gameplan, In-Game) | 7–10 |
| 3 | NBA 2K26, EA FC 26, MLB 26 languages + their page profiles | 10–14 |
| 4 | Warzone, Fortnite languages + FPS In-Game profile upgrades | 10–14 |
| 5 | UFC 5, Undisputed, PGA 2K25, Video Poker languages + remaining page profiles | 10–14 |
| 6 | Voice command recognition / bidirectional loop | 5–7 |

Each phase delivers usable surface area. After Phase 1, Madden players get a working War Room briefing experience even if other pages stay text-only for them.

## What "Phase 1 done" means

- A Competitive-tier or Elite-tier player on Madden 26 can open War Room → tap "Read briefing" → hear a 90-second structured pre-game briefing in their selected tone (Intense / Standard / Calm) at their selected speed.
- The briefing pulls real opponent data, real gameplan plays, real drills.
- Mood-update flow works: player taps "Tilted" → War Room responds with a tone-appropriate reset prompt.
- Tournament mode silences live War Room voice during gameplay; Offline Lab allows everything.
- Free tier sees text-only briefing (no audio) with an upgrade prompt.

What's explicitly **not** in Phase 1 done:
- Other titles' language profiles (Phase 2+)
- Other pages' page profiles (Phase 2+)
- Voice command recognition (Phase 6)
- In-Game live cues (Phase 2 for football, Phase 4 for FPS)

## Open architectural questions (resolved per-doc)

- **TTS provider** — ElevenLabs vs Coqui local vs Azure. Recommendation in Doc #01 (ElevenLabs primary, Coqui local fallback for Offline Lab).
- **Synthesis caching strategy** — what's cacheable, what isn't. Doc #01.
- **Queue durability** — in-process vs Redis. Doc #05.
- **Voice profile per user vs per tier** — does Elite get more voices to choose from? Doc #06.
- **Capture-agent integration for ducking** — does the agent need to control OS audio, or do we duck only the in-app game playback? Doc #01.
