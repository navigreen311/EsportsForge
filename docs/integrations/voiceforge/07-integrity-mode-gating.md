# Integrity Mode Anti-Cheat Gating Logic

> Companion: [01-core-service-spec.md](01-core-service-spec.md), [04-routing-matrix.md](04-routing-matrix.md), [06-subscription-tier-gating.md](06-subscription-tier-gating.md).
> Integrity-mode gating is the anti-cheat compliance layer. One file (`policies/integrity_gating.py`) declares what each mode permits. The gate runs **after** tier gating in the router pipeline.

## Why this layer exists separately from tier

Tier gating is a commercial decision (paid vs free, what you bought). Integrity-mode gating is a **competitive-fairness decision** (is real-time AI coaching allowed in the player's current ranked/tournament context). They're orthogonal:

- A Tournament-mode Elite player has paid for premium voice but is in a context where real-time cues are disallowed. Tier permits, integrity blocks.
- A Free player in Offline Lab can't get voice (tier blocks) regardless of integrity rules.

Both must agree before a cue synthesises.

## Integrity modes recap

From `app/types/settings.ts: IntegrityEnvironment`:

| Mode | Player intent |
|---|---|
| `offline_lab` | Practice, scrim, training. No competitive impact. Full AI. |
| `ranked` | Standard competitive ladder. Some AI restricted. |
| `tournament` | Sanctioned bracket play. Strict — only pre-approved AI allowed. |
| `broadcast` | Streaming-safe. Hide opponent data; voice OK between matches but not during gameplay if the camera is on. |

The current Integrity Mode is read from `User.integrity_mode` and refreshed at session open + on explicit mode-change events. Cached for ~3s in-session to avoid hammering the backend.

## Gating decision shape

```python
@dataclass
class IntegrityDecision:
    drop: bool
    silence_during_gameplay: bool           # cue allowed but only between plays/rounds/matches
    redact_opponent_specifics: bool         # broadcast mode — replace "vs xViper_Elite" with "your opponent"
    use_local_provider_only: bool           # Offline Lab — no network TTS calls
    reason: str
```

The router consumes this and:
- `drop=True` → cue silently dropped. CRITICAL exception: a one-time mode-breach cue plays ("Voice paused for tournament mode") so the player isn't confused.
- `silence_during_gameplay=True` → cue queues, but waits for a non-gameplay window (between rounds/matches) before playing. If the window doesn't open within 30s, drop.
- `redact_opponent_specifics=True` → re-render the template with opponent names replaced by neutral phrases ("your opponent", "the matchup") before synthesising.
- `use_local_provider_only=True` → bypass ElevenLabs, route to Coqui local. Means no network egress. Means lower quality but appropriate for "offline lab" context.

## Per-mode policy

### `offline_lab` — fully unlocked

```python
POLICY[IntegrityMode.OFFLINE_LAB] = {
    every_page: PolicyEntry(drop=False, silence_during_gameplay=False),
    "_provider": ProviderPreference.LOCAL_FIRST,   # if Coqui is available, use it
}
```

Why local-first: Offline Lab implies network-isolated practice. The player may genuinely be offline. Coqui handles it. ElevenLabs available as fallback if network is up.

### `ranked` — partial restrictions

```python
POLICY[IntegrityMode.RANKED] = {
    Page.WAR_ROOM:   PolicyEntry(drop=False, silence_during_gameplay=False),
    Page.GAMEPLAN:   PolicyEntry(drop=False, silence_during_gameplay=True),  # don't read plays mid-match
    Page.ARSENAL:    PolicyEntry(drop=False, silence_during_gameplay=True),
    Page.DRILLS:     PolicyEntry(drop=False, silence_during_gameplay=False), # drills aren't ranked
    Page.SIMLAB:     PolicyEntry(drop=False, silence_during_gameplay=False), # ditto
    Page.TOURNAMENT: PolicyEntry(drop=False, silence_during_gameplay=False),
    Page.ANALYTICS:  PolicyEntry(drop=False, silence_during_gameplay=False), # post-game review
    Page.DASHBOARD:  PolicyEntry(drop=False, silence_during_gameplay=False),
    Page.IN_GAME:    PolicyEntry(drop=True),                                 # disabled in ranked
    "_provider": ProviderPreference.NETWORK_FIRST,
}
```

Key rule: **In-Game voice cues are disabled in ranked.** Live coaching during ranked play is exactly the thing competitive-integrity rules object to. Players who want In-Game voice should use Offline Lab or Casual.

### `tournament` — strict

```python
POLICY[IntegrityMode.TOURNAMENT] = {
    Page.WAR_ROOM:   PolicyEntry(drop=False, silence_during_gameplay=True),  # briefings between matches OK
    Page.GAMEPLAN:   PolicyEntry(drop=False, silence_during_gameplay=True),
    Page.ARSENAL:    PolicyEntry(drop=True),
    Page.DRILLS:     PolicyEntry(drop=False, silence_during_gameplay=False), # if practising before a match
    Page.SIMLAB:     PolicyEntry(drop=False, silence_during_gameplay=True),  # only between matches
    Page.TOURNAMENT: PolicyEntry(drop=False, silence_during_gameplay=False), # the page is for between rounds
    Page.ANALYTICS:  PolicyEntry(drop=False, silence_during_gameplay=False),
    Page.DASHBOARD:  PolicyEntry(drop=False, silence_during_gameplay=False),
    Page.IN_GAME:    PolicyEntry(drop=True),                                 # absolutely no live voice
    "_provider": ProviderPreference.NETWORK_FIRST,
}
```

The defining tournament rule: **no live voice during gameplay, period.** Between-match coaching is fine; in-match cues are not. If a tournament organiser allows it, they can opt the player into a less-strict custom mode (out of v1 scope).

### `broadcast` — opponent data redacted

```python
POLICY[IntegrityMode.BROADCAST] = {
    Page.WAR_ROOM:   PolicyEntry(drop=False, silence_during_gameplay=True,  redact_opponent_specifics=True),
    Page.GAMEPLAN:   PolicyEntry(drop=False, silence_during_gameplay=True,  redact_opponent_specifics=True),
    Page.ARSENAL:    PolicyEntry(drop=False, silence_during_gameplay=True),
    Page.DRILLS:     PolicyEntry(drop=False, silence_during_gameplay=False),
    Page.SIMLAB:     PolicyEntry(drop=False, silence_during_gameplay=False, redact_opponent_specifics=True),
    Page.TOURNAMENT: PolicyEntry(drop=False, silence_during_gameplay=False, redact_opponent_specifics=True),
    Page.ANALYTICS:  PolicyEntry(drop=False, silence_during_gameplay=False),
    Page.DASHBOARD:  PolicyEntry(drop=False, silence_during_gameplay=False),
    Page.IN_GAME:    PolicyEntry(drop=True),                                 # no live cues — viewers might hear them
    "_provider": ProviderPreference.NETWORK_FIRST,
}
```

Two distinct behaviours from the other modes:
- **Opponent data redaction.** Streamers protect against stream-snipers — if the cue says "watch out for xViper_Elite's Cover 3 tendency," the opponent could be watching the stream and adjust. Redaction replaces opponent-specific tokens at render time.
- **No live cues during gameplay.** Viewers can hear the streamer's audio. AI cues going out over the broadcast leak that the player is using AI assistance, which is at best unprofessional and at worst against tournament terms. (Some streamers may want their viewers to hear the cues — that's an Offline Lab/streaming-with-disclosure setup, not Broadcast mode.)

### Redaction semantics

When `redact_opponent_specifics=True`, the renderer pre-processes the payload:

```python
REDACTION_RULES = {
    "opponent.spoken_name":   "your opponent",
    "opponent.archetype_phrase": "this matchup",
    "opponent.top_tendency":  "the matchup-specific read",
    "play.against":           "this opponent style",
    # leave non-opponent fields alone (own gameplan plays, drills, etc.)
}
```

Implemented as a payload transformer that runs before template rendering. The redaction map is per-language since the neutral phrasing differs ("your opponent" in English; localisation TBD).

## Mid-gameplay vs. between-gameplay window detection

The `silence_during_gameplay` flag depends on knowing whether a play / round / match is in progress. Source of truth: VisionAudioForge events.

The router maintains a per-session `is_in_gameplay` flag, updated by:

- `MATCH_STARTED` → `True`
- `MATCH_ENDED` → `False`
- `ROUND_STARTED` → `True` (combat sports, BR)
- `ROUND_ENDED` → `False`
- `PLAY_STARTED` → `True` (football, basketball)
- `PLAY_ENDED` + 5s grace → `False`
- `MENU_DETECTED` → `False`
- Session open with no VAF events yet → `False` (assume between-gameplay until proven otherwise)

When `silence_during_gameplay=True` and `is_in_gameplay=True`:
- Cue is queued with a `WAIT_FOR_GAMEPLAY_PAUSE` flag.
- Queue holds the cue; checks `is_in_gameplay` every 250ms.
- When `is_in_gameplay` flips to `False`, cue is released to the normal queue.
- 30-second timeout: if gameplay never pauses, cue is dropped with reason `silence_window_timeout`.

CRITICAL cues bypass `silence_during_gameplay` (a tournament-mode breach warning still plays mid-play if the system needs to confirm it stopped a violation).

## Mode change mid-session

When `POST /api/v1/sessions/{id}/integrity-mode` arrives:

1. **In-flight cue.** Re-evaluate against the new mode. If the new mode disallows it (drop), hard-cut and play the breach announcement. If it requires redaction, complete the in-flight cue (it's already rendered with non-redacted text — accept this brief inconsistency rather than mid-cue swap).
2. **Queue.** Re-evaluate every queued cue. Drop / wait-for-pause as appropriate.
3. **Breach announcement.** A CRITICAL cue plays once: "Voice paused for tournament mode" / "Opponent details redacted for broadcast." Same priority class as any CRITICAL.

## Provider selection by mode

Per-mode provider preference is `ProviderPreference.LOCAL_FIRST` or `NETWORK_FIRST`. Implemented as the order in which the router tries providers:

```python
def select_provider(mode: IntegrityMode, available: list[TTSProvider]) -> TTSProvider:
    pref = POLICY[mode].get("_provider", ProviderPreference.NETWORK_FIRST)
    if pref == ProviderPreference.LOCAL_FIRST:
        return next((p for p in available if p.is_local), available[0])
    return next((p for p in available if not p.is_local), available[0])
```

If the preferred provider is unavailable, the other is used (with a downgrade-quality CRITICAL announcement once per session).

## Anti-cheat threat model

What integrity-mode gating defends against:

| Attack | Defense |
|---|---|
| Player uses AI cues to gain unfair real-time advantage in ranked | Ranked mode disables In-Game cues; ranked mode disables on-demand Gameplan/Arsenal voice during gameplay |
| Player streams the dashboard to opponents (stream-sniping risk) | Broadcast mode redacts opponent specifics + disables live cues |
| Player switches modes during a tournament match to enable cues | Mode change is logged; tournament platforms can require server-side mode lock for the duration of a sanctioned match (Phase 2 feature, out of v1) |
| Player uses Offline Lab while ranked is the actual game state | Out of scope for VoiceForge — VAF-side title detection + EsportsForge backend's anti-cheat status are what enforce mode-context match |

What it does **not** defend against:
- Mode setting tampering at the client (mode is server-trusted; client just signals intent)
- Out-of-band coaching (player hears advice from a friend on Discord) — VoiceForge has no remit there

## Gating policy file location

```
backend/app/services/integrations/voiceforge/policies/integrity_gating.py
```

Authored by backend + compliance. Reviewed by:
- Backend lead
- Compliance / legal (for tournament-platform alignment)
- Tournament organiser representatives, where the platform supports official events

Versioned same as tier policy. `composed_from` includes both versions on every cue.

## Audit trail

Every cue routed through the integrity gate logs:

```json
{
  "session_id": "...",
  "user_id": "...",
  "mode": "tournament",
  "page": "war_room",
  "intent": "WAR_ROOM_PRE_GAME_BRIEFING",
  "decision": "queue_for_pause",
  "policy_version": "integrity_policy@1.0.0",
  "ts": "..."
}
```

Logs are retained for the longer of (a) 90 days or (b) the EsportsForge audit retention policy. Tournament organisers can request the audit trail for a player's session.

## What this spec does not decide

- **Tournament platform integrations** (server-side mode lock during sanctioned matches). Phase 2+.
- **Per-tournament custom modes.** Some organisers will want their own gating rules. Out of v1.
- **Geographic/regional rules.** EU-vs-US differences in what's permissible. Out of v1.
- **The legal disclaimer text** shown to players when they switch into Tournament mode. Owned by legal; out of voice scope.
