# Phase 1 — Milestone Breakdown

> Companion: [01-core-service-spec.md](01-core-service-spec.md), [02-madden26-language-profile-spec.md](02-madden26-language-profile-spec.md), [03-war-room-page-profile-spec.md](03-war-room-page-profile-spec.md), [04-routing-matrix.md](04-routing-matrix.md), [05-priority-and-interruption-rules.md](05-priority-and-interruption-rules.md), [06-subscription-tier-gating.md](06-subscription-tier-gating.md), [07-integrity-mode-gating.md](07-integrity-mode-gating.md).
> Phase 1 ships **the multi-dimensional VoiceForge core + Madden language profile + War Room page profile**. Target window: **10–12 working days**.

## What "Phase 1 done" means

A Competitive-tier or Elite-tier player on Madden 26 can:
1. Open War Room → tap "Read briefing" → hear a 60–90s pre-game briefing in their selected tone (Intense / Standard / Calm) at their selected speed (Slow / Normal / Fast).
2. The briefing pulls real opponent + gameplan data from the EsportsForge backend.
3. Tap a TiltGuard mood pill → hear a tone-appropriate response within 2 seconds, with chained long-reset suggestion if mood is "Tilted."
4. Tap "Start reset" → hear an 8–12s breathing prompt.
5. Switch Integrity Mode to Tournament → next briefing is silenced during gameplay (queues for between-match window); CRITICAL "Voice paused for tournament mode" cue plays.
6. Switch back to Offline Lab → unrestricted; provider switches to local Coqui if it's available.

Free-tier player on the same setup sees the briefing **as text** in the dashboard with an "Upgrade to Competitive for voice coaching" banner. After the first cue per day, they get a one-shot voice sample for the same cue.

What's explicitly **not** in Phase 1 done:
- Other titles' language profiles (Phase 2+)
- Other pages' page profiles (Phase 2+)
- Voice command recognition (Phase 6)
- In-Game cues for Madden (Phase 2; Elite-tier only)
- Team-cast feature (Phase 2+)
- Custom voice clones for Team tier (Phase 2+)

## Milestone list

| # | Milestone | Owner role | Days | Dependencies |
|---|---|---|---|---|
| **M1** | VoiceForge core service skeleton + ElevenLabs integration | Backend eng | 2 | None |
| **M2** | Voice queue manager (priority + interruption + ducking) | Backend eng | 2 | M1 |
| **M3** | Multi-dimensional router + matrix lookup | Backend eng | 1–2 | M1 |
| **M4** | Madden 26 language profile (vocabulary, cadence, tones, fragments) | Voice/content eng | 2–3 | None — runs in parallel with M1–M3 |
| **M5** | War Room page profile (intents, templates, triggers) | Voice/content eng | 2 | M4 (consumes Madden's language fragments) |
| **M6** | Subscription + Integrity-mode gating policy files | Backend + compliance | 1 | M3 |
| **M7** | Frontend wire-up (mood-update flow, briefing button, banner display) | Frontend eng | 1–2 | M3, M5 |
| **M8** | End-to-end integration test + Phase 1 deploy | Tech lead + manual QA | 1–2 | All above |

**Total: 12–16 days** raw. With 1 backend, 1 voice/content, 1 frontend engineer working in parallel, **10–12 days** is realistic.

Critical path: M1 → M2 → M3 → M5 → M7 → M8 (~9 days serial).
M4 runs alongside M1–M3 (different role). M6 runs alongside M5.

## Per-milestone detail

### M1 — Core service skeleton + ElevenLabs integration (2 days)

Goals:
- New FastAPI service. Separate Dockerfile, separate ECR target. Port 8200.
- `POST /api/v1/sessions/open`, `/cues/enqueue`, `/sessions/{id}/integrity-mode`, `/sessions/{id}/tier`, `/sessions/{id}/close`, `GET /api/health`.
- WebSocket `/ws/voice/{session_id}` for browser audio + control.
- ElevenLabs client wrapper (`ElevenLabsProvider`) implementing the `TTSProvider` protocol.
- Stub Coqui provider (returns silence with the right shape) so the abstraction is exercised; real Coqui integration deferred to M8 hardening.
- Smoke test: open session → enqueue a hardcoded cue → audio chunks stream over WS.

Out of scope for M1: real router (M3), real queue manager (M2), real templates (M4/M5), real gating (M6).

Acceptance: hit the API with curl, get audio bytes back. No multi-tenant concerns.

Deliverable: `services/voiceforge_core/` (or subdirectory of EsportsForge backend — TBD at kickoff). New ECS task definition diff for review. Branch: `vf/core-skeleton`.

### M2 — Voice queue manager (2 days)

Goals:
- Per-session priority queue (CRITICAL/HIGH/NORMAL/LOW).
- Interruption semantics per [05-priority-and-interruption-rules.md](05-priority-and-interruption-rules.md): hard cut for CRITICAL, graceful handoff option for narrative cues, requeue-on-interrupt flag.
- Cooldowns (per-`cooldown_key`, default-by-priority).
- Game-audio ducking: send `duck_audio` / `unduck_audio` control messages over the WS to the frontend. Capture-agent integration deferred to M8.
- Sport-cadence hooks: language-profile-declared rules (`SNAP_INTERRUPTION_RULE`, `INTERRUPT_ON_SHOT_CLOCK_RESET`) consulted at scheduling time. Stub for now — Madden's rules wired in M4.

Out of scope: provider failover (M8), full ducking via capture agent (M8).

Acceptance: unit tests covering all 16 cells of the interruption matrix (CRITICAL × {playing, idle} × {playing class}). Integration test: enqueue a NORMAL cue, then a HIGH cue 1s later → HIGH plays after NORMAL completes (or interrupts if `interrupt_lower_priority=True`).

Deliverable: `voiceforge_core/queue.py` + comprehensive tests. Branch: `vf/queue-manager`.

### M3 — Multi-dimensional router + matrix lookup (1–2 days)

Goals:
- Implement the routing pipeline in [01-core-service-spec.md §"Router"](01-core-service-spec.md): page profile → language profile → tier gate → integrity gate → template render → TTS submit.
- Loader that imports language and page profiles at boot. v1 loads `madden26` + `war_room` + `universal`.
- Pluggable hooks for tier gate and integrity gate. v1 uses stub policies until M6.
- Cue rendering via Jinja2 over a `RoutingContext` object.
- Telemetry: log composed-from versions on every cue.

Acceptance: enqueue a cue with `language=madden26, page=war_room, intent=WAR_ROOM_PRE_GAME_BRIEFING` → router returns a `RoutedCue` with rendered text (text content from M4/M5 stubs) and a voice ID.

Deliverable: `voiceforge_core/router.py`. Branch: `vf/router`.

### M4 — Madden 26 language profile (2–3 days)

Goals (all from [02-madden26-language-profile-spec.md](02-madden26-language-profile-spec.md)):
- `vocabulary.py` — 24 offensive formations, 8 coverages, 5 defensive fronts, situational labels, archetype phrases.
- `cadence.py` — pre-snap window, post-play window, two-min-drill rules, `SNAP_INTERRUPTION_RULE = "duck_only"`.
- `tones.py` — 3 tones × at least 5 entries per tone for greetings, encouragement, correction, mental cues, closers.
- `fragments/briefing_components.py` — opener, opponent_summary, key_plays, mental_cue, closer.
- `fragments/post_play.py`, `fragments/encouragement.py`, `fragments/correction.py` — reusable phrases for the other pages, even though only War Room consumes them in Phase 1 (front-loading content for Phase 2 efficiency).
- SSML phonetic overrides for known mispronunciations (RPO, Tampa 2, PA Crossers).
- Required-language-keys export so War Room's CI gate validates coverage.

Out of scope for M4: NBA / EAFC / etc. languages (Phase 3+).

Acceptance: render every fragment with synthetic data, listen to TTS output for at least 6 representative cues. No mispronunciations of any whitelisted term.

Deliverable: `voiceforge_core/languages/madden26/` + tests. Branch: `vf/madden26-language`.

### M5 — War Room page profile (2 days)

Goals (all from [03-war-room-page-profile-spec.md](03-war-room-page-profile-spec.md)):
- `intents.py` — full 7-intent enumeration.
- `templates/pre_game_briefing.j2` — 60–90s structured briefing.
- `templates/mid_game_adjustment.j2`, `mood_update_response.j2`, `mental_reset_short.j2`, `mental_reset_long.j2`, `round_recap.j2`.
- `triggers.py` — UI events + VAF events → intent mapping.
- Priority overrides per the page profile spec.
- Required-language-keys export — fails CI if a required key is missing on the active language.

Acceptance: synthetic test that:
- Renders pre_game_briefing.j2 with Madden language + a populated opponent payload → output is 60–90s when read at Normal speed → no orphan placeholders.
- Renders mood_update_response.j2 for `red` mood with Intense tone → output is calm-leaning despite the player's Intense preference (per the de-escalation rule).

Deliverable: `voiceforge_core/pages/war_room/` + tests. Branch: `vf/war-room-page`.

### M6 — Subscription + Integrity-mode gating policy files (1 day)

Goals:
- `policies/tier_gating.py` — implementing the table in [06-subscription-tier-gating.md](06-subscription-tier-gating.md).
- `policies/integrity_gating.py` — implementing the table in [07-integrity-mode-gating.md](07-integrity-mode-gating.md).
- Wire both into the router (replacing the M3 stubs).
- Per-mode provider selection (M3 + M6 jointly: M3 stubs the `select_provider` hook; M6 implements the real one).
- Audit trail logging: every gating decision emits a structured log line with policy versions.

Acceptance:
- Free-tier briefing request → returns `text_only=True`, banner string matches.
- Tournament-mode briefing request mid-gameplay → returns `silence_during_gameplay=True`; queue holds the cue until `is_in_gameplay` flips false.
- Broadcast-mode briefing request → opponent name in payload is redacted to "your opponent."

Deliverable: two policy files + tests. Branch: `vf/gating-policies`.

### M7 — Frontend wire-up (1–2 days)

Goals:
- `useVoiceForge` hook updates: connect to the new `/ws/voice/{session_id}` WS for audio streaming.
- WebAudio playback layer with the duck handler (in-app fallback ducking for HTML5 `<audio>` elements).
- War Room "Read briefing" button → POST to enqueue endpoint with the right shape.
- TiltGuard mood-pill click → POST → router triggers war_room mood-response cue → audio plays within 2s.
- "Start reset" button → enqueues `WAR_ROOM_MENTAL_RESET_SHORT`.
- Free-tier banner rendering for `text_only` cues.
- Speaking-indicator pulse on the dashboard.
- Settings → Game Settings → Voice Settings: voice ID picker (Elite+) reads from the tier policy's voice pool.

Acceptance: manual click-through on dev backend. Briefing audible. Mood update responsive. Free-tier upgrade banner appears.

Deliverable: frontend changes shipped behind a `vaf+vf` feature flag. Branch: `vf/frontend-wireup`.

### M8 — End-to-end integration test + Phase 1 deploy (1–2 days)

Goals:
- Full pipeline test: VAF → EsportsForge agent → VoiceForge → audio plays in the dashboard. (Phase 1 doesn't require VAF to be fully real — synthetic VAF events are fine.)
- Capture-agent ducking integration: capture agent receives `duck_audio` over its control channel and ducks the OS-level game audio. (Coordinate with the desktop team — this depends on VAF Phase 1's M1 capture agent existing.)
- Coqui local fallback: install + smoke-test for Offline Lab mode.
- Provider failover: ElevenLabs degraded → Coqui takes over → CRITICAL "voice quality degraded" cue plays.
- Stage deploy + smoke + bug triage.

Acceptance: tech lead + one stakeholder validate end-to-end on staging. Cut release tag (`vf-phase-1-v0.1.0`).

Deliverable: production-ready Phase 1.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| ElevenLabs latency exceeds budget under real-world load | Med | Med | Streaming TTS keeps perceived latency ≤250ms; cache static cues. If the issue is sustained, fall back to Coqui (lower quality but local). |
| Voice tone of the cloned coach voice doesn't match expectations | Med | Low | Iterate offline; the registered voices are configurable post-deploy without code change. |
| Mood-update response feels patronising / off-tone | Med | Med | Manual review of every mood-response template by the content team. Player feedback loop in Settings ("This response wasn't helpful" thumbs-down → fed back to author). |
| Game-audio ducking inconsistent across capture-card vendors | Med | Med | Test matrix in M8 covers Elgato + AVerMedia. Document any unsupported card in release notes. In-app fallback always works for browser-headphones case. |
| Tournament-mode "voice paused" cue itself plays during a tournament moment of silence and creates noise | Low | Low | Cap the breach announcement at 1 per session and 1.5s max length. If it would play during gameplay, defer to next pause. |
| Free-tier upgrade banner is too aggressive / annoying | Low | Med | One sample voice cue per day (auto-included), then text-only — banner is in the dashboard notification feed, not modal. Product-led conversion, not nag. |
| Author of a new (title × page) cell forgets a required language key | Med | Low | CI gate checks every page profile's `_required_language_keys.py` against the active language profile. Failing build is the alarm. |

## Resource needs

- 1 backend engineer (FastAPI / Python) — full Phase 1.
- 1 voice/content engineer (vocabulary curation, template authoring, prompt engineering) — full Phase 1.
- 1 frontend engineer (React / WebAudio) — M7 + M8 (split commitment).
- Tech lead for M8 + reviews.
- Capture-agent engineer for M8 ducking integration (coordinate with VAF Phase 1's desktop engineer).
- Cloud: 1 new ECS service (small task, t3.medium), new ECR repo, Route53 entry for `voice.esportsforge.gg`.
- ElevenLabs Pro subscription with sufficient credit for Phase 1 + first month of paid users.
- Compliance review for the integrity-mode policy file before M8 deploy.

## Out-of-scope follow-ups (Phase 1.1, post-launch)

- Coqui XTTS production-grade deploy (M8 ships a basic version; tuning + better voice models in 1.1).
- Capture-agent ducking edge cases.
- Voice command recognition prototype (Phase 6).

## Approvals required before kickoff

1. **Architecture sign-off** on Docs #00–#07. Resolve open architectural questions in Doc #01. Resolutions get amended into the docs.
2. **ElevenLabs commercial agreement** finalised — voice IDs licensed for production use, custom-clone Terms understood for Team tier.
3. **Compliance + tournament-organiser review** of [07-integrity-mode-gating.md](07-integrity-mode-gating.md). Get explicit approval on the Tournament-mode rules from at least one major sanctioning body.
4. **Resource allocation** — 3-engineer staffing for the 10–12 day window.

After approvals, kick off **M1 + M4 in parallel** (no cross-dependency). M2/M3/M5/M6/M7 follow from there.
