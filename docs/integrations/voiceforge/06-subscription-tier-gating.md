# Subscription Tier Gating Logic

> Companion: [01-core-service-spec.md](01-core-service-spec.md), [04-routing-matrix.md](04-routing-matrix.md).
> Tier gating is centralised. One file (`policies/tier_gating.py`) declares what each tier unlocks. Page and language authors don't think about tiers; the router consults this file before synthesis.

## Tier semantics

EsportsForge has four subscription tiers (see `app/models/user.py: UserRole`):

| Tier | Voice surface |
|---|---|
| **Free** | Text-only fallback. No TTS synthesis. Banner: "Upgrade to Competitive for voice coaching." |
| **Competitive** | Voice on War Room, Drills, Gameplan, SimLab, Tournament, Analytics, Dashboard. **No In-Game voice cues.** Default voice IDs (standard quality). |
| **Elite** | Everything Competitive has + In-Game live cues + premium voice IDs (better latency, more natural-sounding) + voice ID picker (~6 curated voices to choose from). |
| **Team** | Everything Elite has + custom team-cloned voice ("coach voice") shared across roster + team-cast feature (one cue plays for all 6 roster members simultaneously during scrim). |

The tier gate is the **first** filter after script-template selection (see [01-core-service-spec.md §"Router"](01-core-service-spec.md) step 3 in the routing pipeline). It runs before integrity-mode gating because tier rules don't depend on game context.

## Gating decision shape

```python
@dataclass
class TierDecision:
    drop: bool                         # if True, cue does not produce any output
    text_only: bool                    # if True, render template but don't synthesise; deliver as text banner
    voice_id_pool: list[str]           # voice IDs the user is allowed to use
    voice_id_default: str              # default selection if user hasn't picked
    use_premium_provider: bool         # ElevenLabs Pro vs ElevenLabs Free vs Coqui
    upgrade_prompt: str | None         # text for the "Upgrade to X" CTA banner
    reason: str                        # for telemetry
```

The router consumes this and either:
- `drop=True` → cue is silently discarded (no banner).
- `text_only=True` → cue renders to text, sent to dashboard as a banner with the upgrade prompt; no audio.
- `text_only=False, drop=False` → proceed to integrity-mode gate, then synthesis.

## Per-page coverage by tier

Authoritative table. The single source of truth lives in `policies/tier_gating.py`:

```python
PAGE_VOICE_COVERAGE: dict[Tier, dict[Page, Coverage]] = {
    Tier.FREE: {
        page: Coverage.TEXT_ONLY for page in Page  # all text, no TTS
    },
    Tier.COMPETITIVE: {
        Page.WAR_ROOM:    Coverage.VOICE,
        Page.GAMEPLAN:    Coverage.VOICE,
        Page.ARSENAL:     Coverage.VOICE,
        Page.DRILLS:      Coverage.VOICE,
        Page.SIMLAB:      Coverage.VOICE,
        Page.TOURNAMENT:  Coverage.VOICE,
        Page.ANALYTICS:   Coverage.VOICE,
        Page.DASHBOARD:   Coverage.VOICE,
        Page.IN_GAME:     Coverage.TEXT_ONLY,    # In-Game gated to Elite+
    },
    Tier.ELITE: {
        page: Coverage.VOICE_PREMIUM for page in Page
    },
    Tier.TEAM: {
        page: Coverage.VOICE_PREMIUM for page in Page
        # plus team-cast feature, see "Team-only features" below
    },
}
```

Three coverage levels:

- `TEXT_ONLY` — render to text, surface as a banner. No TTS cost. Player sees the content but doesn't hear it.
- `VOICE` — synthesise via ElevenLabs default voices, default speed/quality. Free voices pool (standard ElevenLabs voices, no clones).
- `VOICE_PREMIUM` — ElevenLabs Pro features: faster first-byte, higher fidelity, voice picker access (~6 curated voices), custom voice clones (Team tier).

## Voice ID pools

Players can pick a preferred voice in Settings (per [02-core-service-spec.md §"Voice IDs"](01-core-service-spec.md)). The pool depends on tier:

```python
VOICE_POOLS = {
    Tier.FREE:        [],                                     # not applicable — no synthesis
    Tier.COMPETITIVE: ["default_competitive"],                # one default
    Tier.ELITE:       [
        "default_elite",
        "calm_coach",
        "intense_drill",
        "analyst_review",
        "neutral_female",
        "neutral_male",
    ],                                                         # 6 curated
    Tier.TEAM:        ELITE_VOICE_POOL + ["team_coach_voice"], # + custom clone
}
```

The Settings UI shows the picker only if the pool has >1 entry. Free/Competitive players see no picker.

## Tier-only features

### In-Game voice (Elite+)

The In-Game page profile is gated to Elite and above for two reasons:
1. **Cost.** Live cues during gameplay are dynamic (constant new payload data), so caching doesn't help much. Steady stream of TTS calls = real expense.
2. **Anti-cheat sensitivity.** Real-time AI cues during ranked play are exactly what the integrity gate is meant to govern. Pricing the feature into Elite encourages players who care about competitive integrity to pay attention to mode settings.

When a Competitive-tier player triggers an In-Game cue, the gate returns `text_only` with `upgrade_prompt = "Upgrade to Elite for live voice coaching."` The cue's content still renders to a banner.

### Team-cast (Team tier)

Team tier unlocks shared voice profiles across a roster (max 6 seats). Concretely:
- The team's coach can record a custom voice (or the team can pick a voice clone) → stored as `team_coach_voice` for that team.
- During scrim, when one player triggers a cue (or a coach-side button does), the cue plays simultaneously on every roster member's audio.
- Implementation: when the router sees a Team-tier session opening with `team_id`, it also fan-outs cue playback to every other open session for that team.

This is a Phase-2-or-later feature. Phase 1 only validates the tier gate fundamentals.

## Upgrade prompts

When a cue is downgraded to text-only, the banner shown to the player is taken from this map (single file, easily A/B tested):

```python
UPGRADE_PROMPTS = {
    (Tier.FREE, Page.WAR_ROOM):    "Hear your pre-game briefing — Competitive tier and up.",
    (Tier.FREE, Page.DRILLS):      "Coach voice during drills — Competitive tier and up.",
    (Tier.FREE, Page.IN_GAME):     "Live voice coaching mid-game — Elite tier and up.",

    (Tier.COMPETITIVE, Page.IN_GAME): "Live voice coaching mid-game — Elite tier and up.",
    # ... same Elite+ message regardless of which page they tried in In-Game
}
```

Banners surface in the dashboard's notification bar and inline within the page (e.g., a small "Upgrade for voice" pill on the War Room briefing card). Frontend handles display; the backend supplies the string.

## Tier change mid-session

If a player upgrades or downgrades while a session is open:
- EsportsForge backend POSTs to VoiceForge `POST /api/v1/sessions/{id}/tier`.
- Existing in-flight cue completes.
- New cues are evaluated against the new tier from arrival onward.
- If downgrading from Elite to Competitive, In-Game cues that were synthesising stop and convert to text-only on the dashboard (no abrupt cut — let the in-flight cue finish, but nothing new synthesises).

## Non-paying-tier voice prompts (one-time)

To give Free-tier players a taste, the first cue per session synthesises with a 30-second sample voice clip even though the tier policy is text-only. This is implemented as a one-shot bypass in the gate:

```python
if user.tier == Tier.FREE:
    if not user.has_received_voice_sample_today:
        user.mark_voice_sample_consumed()
        return TierDecision(drop=False, text_only=False, voice_id_pool=["default_competitive"], ...)
```

Once-per-day per user. After the sample, all subsequent cues are text-only until upgrade.

## Free tier text-only delivery

When `text_only=True`:
- Template renders normally (same Jinja path).
- Output bypasses TTS and is POSTed back to EsportsForge backend's `/api/v1/voice/text-cues` endpoint.
- The dashboard's notification bell receives a typed banner item:
  ```
  { type: "voice_cue_text", page: "war_room", intent: "WAR_ROOM_PRE_GAME_BRIEFING",
    text: "...rendered briefing...", upgrade_prompt: "..." }
  ```
- Frontend renders as an in-app message with an inline "Upgrade for audio" CTA.

This means Free players still receive coaching content — just as text, with the upgrade nudge. Their experience is *worse than paid*, not *blank*.

## Tier policy versioning

The policy file is versioned (`tier_policy@1.0.0`). Bumps correspond to:
- Adding a new tier (rare).
- Moving a page between coverage levels (e.g., promoting In-Game from Elite to Competitive).
- Changing the voice pool composition.

Cue events emitted carry the tier policy version as part of `composed_from`. Auditing "why was X player charged for Y voice quality" goes through this trail.

## Gating policy file location

```
backend/app/services/integrations/voiceforge/policies/tier_gating.py
```

Authored by backend + product. Reviewed jointly. Single file — no per-language or per-page tier overrides.

## Edge cases

### User somehow at multiple tiers (shouldn't happen but)

Impossible at the data model level (one `users.role` column), but in practice during in-flight tier changes the router caches `ctx.tier` per session. If a stale cache returns the old tier for a few seconds post-change, the new tier takes effect on next session refresh (handled by `POST /api/v1/sessions/{id}/tier` — see "Tier change mid-session").

### Trial / promotional grants

A 7-day free Elite trial is straightforward — write `users.role = elite` for the duration, write back to `competitive` on expiry. The gate doesn't need to know it's a trial.

### Per-page-feature opt-out within a tier

Player wants voice on War Room but not on Drills (or vice versa). This is a Settings-level toggle (`voice_settings.per_page.{page} = false`), not a tier policy. The router checks the user's per-page enable before consulting tier gate; if disabled, treat as `drop=True` (no synthesis, no banner).

## What this spec does not decide

- **Pricing.** Out of scope here.
- **Voice clone training procedures.** Team-tier feature; deferred until Phase 2+.
- **Stripe billing integration.** Already wired in EsportsForge backend; tier value flows from there.
- **Integrity-mode gating.** Doc #07 — runs after tier gate.
