# VoiceForge Core Service — Specification

> Companion: [00-overview.md](00-overview.md), [04-routing-matrix.md](04-routing-matrix.md), [05-priority-and-interruption-rules.md](05-priority-and-interruption-rules.md).
> The core service is the pipeline. Cues come in, audio (and a duck signal) goes out. **No title- or page-specific logic lives here** — the router pulls those from profiles.

## Purpose

The core service owns:
1. Speech synthesis (TTS).
2. Speech recognition (STT, deferred to Phase 6).
3. The voice queue manager (priority, interruption, ducking).
4. The multi-dimensional router (title × page × tier × mode → script template).
5. Tone & speed parameter shaping (reads Settings).
6. Outbound audio + duck signals.
7. Observability.

It does **not** define vocabulary (that's the language profile), does **not** define scripts (that's the page profile), and does **not** decide what's cheatable (that's the integrity-mode gate's policy declaration).

## Recommendation: stack and deployment

**Stack: FastAPI + asyncio + Pydantic, deployed as a separate ECS service.** Same reasoning as the VisionAudioForge core (docs/specs/02-visionaudioforge-core.md):

- Same stack as the EsportsForge backend → shared logging / Pydantic / Dockerfile pattern.
- WebSockets + async are first-class (cue stream + audio chunk delivery).
- Different scaling profile from the EsportsForge API (long-lived connections, steady CPU + GPU-adjacent network for TTS provider calls).
- Independent deploy cadence — language profiles change weekly.

Default port: **8200** (paired with VisionAudioForge's :8100). In dev: `http://localhost:8200`. In prod: `wss://voice.esportsforge.gg`, separate ECR repo, separate ECS service, ALB hostname split.

## TTS provider — decision and fallback

**v1 recommendation: ElevenLabs Pro (primary) + Coqui XTTS (local fallback for Offline Lab).**

Reasoning:

| Provider | Pros | Cons | Used for |
|---|---|---|---|
| **ElevenLabs Pro** | Best-in-class voice quality (multilingual, low artifacts at fast speeds), per-voice cloning if we want a coach-cast voice, ~250ms first-byte latency | $/month proportional to usage, network-dependent | All paid tiers, all modes except Offline Lab. Default. |
| **Coqui XTTS (self-hosted)** | Free, runs on-prem, deterministic, works offline | Quality is good-not-great, 500ms+ latency on CPU, GPU recommended | Offline Lab mode (player isolated from network), and as ElevenLabs fallback when their API is degraded |
| Azure Cognitive | Cheap, reliable | Slightly more robotic, weaker on game-specific terms | Considered, deferred — adds a third vendor for marginal gain |

The voice synthesis interface abstracts both:

```python
class TTSProvider(Protocol):
    async def synthesise(
        self,
        text: str,
        voice_id: str,
        tone: VoiceTone,           # Intense | Standard | Calm
        speed: VoiceSpeed,         # Slow | Normal | Fast
    ) -> AsyncIterator[bytes]:     # PCM/MP3 chunks
        ...
```

`ElevenLabsProvider` and `CoquiProvider` both implement it. The router decides which one to call per cue based on integrity mode and a feature flag.

### Voice IDs

ElevenLabs uses voice IDs. We keep a registry:

```python
VOICE_REGISTRY = {
    "default_competitive": "elevenlabs:21m00Tcm4TlvDq8ikWAM",   # American male, neutral
    "default_elite":       "elevenlabs:VR6AewLTigWG4xSOukaG",    # American male, premium
    "calm_coach":          "elevenlabs:N2lVS1w4EtoT3dr4eOWO",
    "intense_drill":       "elevenlabs:bVMeCyTHy58xNoL34h3p",
    "team_coach_voice":    "elevenlabs:<custom_clone>",          # Team tier feature
}
```

Voice ID selection happens in the router based on tier + Settings preference. Authors of language/page profiles never hardcode voice IDs.

## STT (deferred to Phase 6)

Architecture must accommodate but not implement in Phase 1:

- **Provider:** Whisper (OpenAI API or local `faster-whisper`).
- **Trigger:** push-to-talk on the player's headset, or voice activity detection in the capture agent.
- **Flow:** Player says "What should I run?" → capture agent forwards a 3-second audio clip → Whisper transcribes → command parser routes to GameplanAgent → response goes back through the cue queue.

Reserve the wire surface for it now (`POST /api/v1/recognise`) so Phase 6 isn't a refactor.

## Coaching tone & briefing speed

These come from `User.settings.voice` — the player's selections in Settings → Game Settings → Voice Settings. The core reads them when opening a session and includes them in the router context.

**Tone (Intense / Standard / Calm)** affects:
1. **Voice ID.** Intense → `intense_drill`. Calm → `calm_coach`. Standard → `default_competitive` or `default_elite`.
2. **Script-template variant.** Each (language × page) cell ships up to 3 script variants — one per tone. Authors are free to write a single neutral variant if they want; the core falls back to "standard" when a tone-specific variant isn't authored.
3. **TTS modulation parameters.** ElevenLabs supports `stability`, `similarity_boost`, `style` knobs. Intense lowers stability (more dynamic), Calm raises stability (smoother).

**Briefing speed (Slow / Normal / Fast)** affects:
1. ElevenLabs `speaking_rate` parameter (`0.85` / `1.0` / `1.15`).
2. Pause duration in script templates — `{{ pause(short) }}`, `{{ pause(medium) }}`, `{{ pause(long) }}` token rendering.

Both are read fresh per cue (cheap), so the player can change them mid-session and hear the change on the next cue.

## Router

The router is the brain. Per cue:

```
Inputs:
  cue_request: { event_type, page, language, intent, payload }
  user_context: { user_id, tier, integrity_mode, voice_settings }

Pipeline:
  1. Page profile lookup    — page_profiles[page]
  2. Language profile       — language_profiles[language]
  3. Tier gate              — drop / downgrade / pass through
  4. Integrity-mode gate    — drop / pass through
  5. Script template select — tone-aware, intent-keyed
  6. Template fill          — interpolate payload + game-state context
  7. TTS provider select    — ElevenLabs (default) or Coqui (offline / fallback)
  8. Voice ID + tone params — from registry + user settings
  9. Submit to queue        — with priority + interruption hints
```

Steps 1–6 are pure data. Step 7+ are async. The router is stateless — all stateful concerns are in the queue.

The matrix structure of the lookup is detailed in [04-routing-matrix.md](04-routing-matrix.md).

## Voice queue manager

A per-session priority queue with interruption + ducking semantics. Detailed rules in [05-priority-and-interruption-rules.md](05-priority-and-interruption-rules.md).

Core implementation in this doc:
- Per session, a single `asyncio.PriorityQueue`.
- Each entry: `(priority, sequence, cue)`. Lower priority number = higher importance (CRITICAL=0, HIGH=1, NORMAL=2, LOW=3).
- Sequence ties keep FIFO within a priority class.
- The player-facing audio output is single-track. At most one cue plays at a time.

When a higher-priority cue is enqueued while a lower-priority one is mid-play:
1. Synthesis of the in-flight cue is cancelled (if still streaming) or playback is faded out (40ms ramp).
2. Duck signal stays asserted (already ducked).
3. The interrupting cue is synthesised + played.
4. Default: the interrupted cue is **dropped**, not requeued — it's now stale. (Authors can mark a cue with `requeue_on_interrupt: true` for cues that should retry, e.g., scheduled briefings.)

Cooldown rules (e.g., don't repeat the same `event_type` within 8 seconds) are stored on each cue's metadata; the queue checks before playing.

## Audio out + game-audio ducking

Two delivery paths:

### Browser playback (in-app dashboard)

The frontend opens a WebSocket to `/ws/voice/{session_id}` and receives `(audio_chunk, control_messages)`. WebAudio plays the chunk; control messages (`duck_start`, `duck_end`, `cue_started`, `cue_ended`) drive UI state (the speaking indicator pulse).

### Game-audio ducking

This is the non-trivial part. The game running on PS5 produces audio that the player wants quieter while VoiceForge speaks. Three options:

| Approach | How | Pros | Cons |
|---|---|---|---|
| **OS-level ducking** | Voice service signals capture agent → agent uses Windows audio API to lower the per-app volume of the game-capture-card audio routed to the player's speakers | Works for capture-card setups; player keeps all native game audio routing | Requires capture agent integration; only works when player monitors game audio through the PC |
| **In-app ducking** | If player listens via the dashboard's in-app audio (e.g., headphones plugged into PC), web app duckes its own audio output | Simple, no agent integration | Doesn't work if player listens directly through console output |
| **Manual** | Player sets sidetone manually | No engineering | Not actually ducking |

**v1 recommendation: OS-level ducking via the capture agent**, fallback to in-app when no agent is connected. The capture agent already has Windows audio API access for capture-card discovery. The voice service sends a `duck_audio` message over the agent's control channel; the agent applies a −12dB attenuation to the configured app/device for the duration, releases on `unduck_audio`. Default ramp 100ms in, 200ms out.

If no agent is connected (player using browser only), fall back to in-app ducking of any HTML5 `<audio>` elements registered with the duck handler.

## Synthesis caching

Two classes of cues:

**Static cues** — the script renders identically every time (e.g., universal `MENU_DETECTED → "Menu paused — voice cues paused"`). Cache the synthesised audio per `(text_hash, voice_id, tone, speed)` tuple. Hit rate target: 60%+. Cache in S3 with CloudFront in front; in-memory LRU on the service for the hottest entries.

**Dynamic cues** — the script interpolates user/game data (player names, scores, formations). Don't cache. ElevenLabs supports streaming at <250ms first-byte, which is acceptable.

Configurable via cell metadata in the matrix: `cacheable: true | false`. Default `true` for snapshot/announcement cues, `false` for player-named cues.

## Wire surfaces

### HTTP: `POST /api/v1/sessions/open`

Backend → core. Opens a voice session for a player.

```json
{
  "user_id": "5041bbe7-...",
  "session_id_visionaudio": "ses_01HXXX",   // links to a VAF session
  "tier": "competitive",
  "integrity_mode": "ranked",
  "voice_settings": {
    "tone": "standard",
    "speed": "normal",
    "voice_id_pref": null,
    "master_enabled": true,
    "per_page": { "war_room": true, "in_game": false, ... }
  }
}
```

### HTTP: `POST /api/v1/cues/enqueue`

Agents (GameplanAgent, etc.) → core. Submit a cue for playback.

```json
{
  "session_id": "voicesess_01HYY",
  "page": "war_room",
  "language": "madden26",
  "event_type": "BRIEFING_REQUESTED",
  "intent": "full_pre_game_briefing",
  "priority": "NORMAL",
  "cooldown_key": "war_room.briefing",
  "payload": {
    "opponent_name": "xViper_Elite",
    "opponent_archetype": "Aggressive Rush",
    "gameplan_play_count": 15,
    /* ... */
  }
}
```

Returns `{ "queued": true, "estimated_play_at": "...", "cue_id": "..." }`.

### WebSocket: `/ws/voice/{session_id}`

Frontend → core. Subscribes for audio + control messages.

Frames:
- `{ "type": "cue_started", "cue_id": "...", "duration_estimate_ms": 4200 }`
- `{ "type": "audio_chunk", "data_b64": "..." }` (MP3 or PCM, content-type negotiated at connect)
- `{ "type": "cue_ended", "cue_id": "...", "reason": "completed | interrupted | dropped" }`
- `{ "type": "duck_start" }` / `{ "type": "duck_end" }`
- `{ "type": "queue_state", "depth": 3, "currently_speaking": true }`

### HTTP: `GET /api/v1/sessions/{id}/queue`

Debug endpoint. Returns the current queue state.

### HTTP: `POST /api/v1/sessions/{id}/integrity-mode`

Backend → core. Player switched mode mid-session. Triggers cue-queue re-evaluation (in-flight cues that violate the new mode are cancelled).

### HTTP: `GET /api/health`

Standard. Returns `active_sessions`, `tts_provider_status`, `synthesis_p50_ms`, `cache_hit_ratio`.

## Per-session state

```python
@dataclass
class VoiceSession:
    session_id: str
    user_id: str
    tier: SubscriptionTier
    integrity_mode: IntegrityMode
    voice_settings: VoiceSettings
    queue: asyncio.PriorityQueue
    currently_playing: CueInFlight | None
    cooldowns: dict[str, datetime]      # cooldown_key -> next_allowed_at
    capture_agent_connected: bool       # for ducking path selection
    opened_at: datetime
    last_cue_at: datetime | None
```

In-memory only in v1, same trade-off as VAF.

## External dependencies

| External | Surface | Owned by |
|---|---|---|
| ElevenLabs API | `POST /v1/text-to-speech/{voice_id}/stream` | external — credentials in AWS Secrets Manager |
| Coqui XTTS (self-hosted) | gRPC or HTTP, deployed as sidecar container | infra |
| EsportsForge backend `/api/v1/voice/sessions/active` | Frontend reads to show "voice live" indicator | EsportsForge backend team |
| EsportsForge backend `/api/v1/users/me/voice-settings` | Existing — read voice tone/speed | shared |
| VisionAudioForge core | Indirect — events flow through EsportsForge backend's agents, which call this core | shared |
| Capture agent | Control channel for `duck_audio` / `unduck_audio` | desktop team |

## Observability

- Per-session: cues enqueued, cues played, cues dropped (by reason: tier, mode, interrupt, cooldown), TTS p50/p95/p99 latency, queue depth p99.
- Per cell: requests, hit rate (cache), tier distribution.
- Per provider: success / failure / fallback rate.

Same destination as EsportsForge logs (CloudWatch).

## Open architectural questions

| # | Question | v1 decision |
|---|---|---|
| 1 | TTS provider | ElevenLabs Pro primary, Coqui XTTS local fallback for Offline Lab + provider-degraded states |
| 2 | Synthesis caching | Static cues cache to S3+CloudFront; dynamic cues stream live |
| 3 | Queue durability | In-process asyncio queues v1. Redis Streams when we cross the same thresholds as VAF |
| 4 | Voice profile per user vs per tier | Tier-default + per-user override (Elite+ can pick any voice from a curated list of ~6) |
| 5 | Capture-agent ducking integration | Capture agent gains a control-channel handler; default for capture-card setups. In-app fallback only for browser-headphones case. |

## What this spec does not decide

- **Vocabulary or script content.** Doc #02 (Madden language) and Doc #03 (War Room page) cover those.
- **Cell-by-cell matrix population.** Doc #04 covers the structure; cells are authored by language/page profile teams.
- **Priority numbers per cue type.** Doc #05.
- **Tier gating cells.** Doc #06.
- **Integrity-mode gating cells.** Doc #07.
