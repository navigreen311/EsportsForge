# Voice Cue Priority & Interruption Rules

> Companion: [01-core-service-spec.md](01-core-service-spec.md), [03-war-room-page-profile-spec.md](03-war-room-page-profile-spec.md).
> The queue manager is the single owner of when cues play, when they interrupt, and how game audio ducks. Authors emit cues with a declared priority + cooldown_key; the queue does the rest.

## Priority enum

Four priority classes. Lower number = higher importance.

```python
class Priority(IntEnum):
    CRITICAL = 0   # immediate danger / safety / accidental Tournament-mode breach
    HIGH     = 1   # player-initiated request response, mood updates, system alerts
    NORMAL   = 2   # planned coaching cues — briefings, recommendations, drill cues
    LOW      = 3   # ambient narrative — tendency reminders, encouragement filler
```

Within a priority class, FIFO. The queue uses `(priority, sequence)` as the sort key where `sequence` is monotonically increasing per session.

## What lives at each level

### CRITICAL (0)

Things the player must hear *now*. Examples:

| Title | Intent | Why critical |
|---|---|---|
| Warzone / Fortnite | `BR_DANGER_FROM_BEHIND` | Audible threat warning; missing it gets the player killed |
| All | `INTEGRITY_MODE_BREACH_AUTOSTOP` | Settings changed mid-cue to a mode that disallows it; we say "voice paused for tournament mode" briefly so the player isn't confused |
| All | `SESSION_DISCONNECT_WARNING` | "Voice service disconnected" — surfaced as a brief audio cue so the player notices |

CRITICAL cues:
- Always interrupt anything below them, no questions.
- Game audio ducks aggressively (−18dB instead of the default −12dB).
- Cooldowns don't apply (a danger warning isn't suppressed because it just fired 5s ago — the danger may still be live).
- Are short by contract — typically 1–3 words. Authors that emit a >3s critical cue will get a CI warning.

### HIGH (1)

Player-initiated or context-urgent. Examples:

| Title | Page | Intent |
|---|---|---|
| All | War Room | `WAR_ROOM_MOOD_UPDATE_RESPONSE` (player tapped a mood pill) |
| All | Drills | `DRILLS_REP_CORRECTION_INSTANT` (player just made a mistake; tell them now) |
| All | * | Player explicit voice command response (Phase 6) |

HIGH cues:
- Interrupt NORMAL and LOW.
- Don't interrupt CRITICAL.
- Cooldown applies (default 4s per `cooldown_key`).
- Game audio ducks at default −12dB.

### NORMAL (2)

The default. Most coaching content lives here. Examples:

| Title | Page | Intent |
|---|---|---|
| Madden 26 | War Room | `WAR_ROOM_PRE_GAME_BRIEFING` |
| Madden 26 | Gameplan | `GAMEPLAN_KILL_SHEET_READ` |
| Warzone | In-Game | `FPS_LOADOUT_RECOMMENDATION` |
| All | * | Step-by-step guidance, planned briefings |

NORMAL cues:
- Don't interrupt anything except LOW.
- Are ducked aside (not cancelled) when CRITICAL fires; resume when CRITICAL ends, *if still relevant* (cue's `requeue_on_interrupt` flag).
- Cooldown applies (default 8s per `cooldown_key`).

### LOW (3)

Ambient narrative. Easily skipped if anything else needs to play. Examples:

| Title | Page | Intent |
|---|---|---|
| All | War Room | `WAR_ROOM_OPPONENT_TENDENCY_REMINDER` (subtle hover-derived) |
| All | War Room | `WAR_ROOM_MENTAL_RESET_LONG` (explicitly low so it interrupts cleanly) |
| All | Analytics | `ANALYTICS_FILLER_NARRATIVE` |

LOW cues:
- Get interrupted by anything above them.
- Are dropped on interrupt (no `requeue_on_interrupt`).
- Cooldown applies (default 30s — they're meant to be infrequent).

## Interruption matrix

```
                  Currently playing →
Incoming ↓        CRITICAL    HIGH        NORMAL      LOW         (idle)
CRITICAL          fade-out 40ms then play
                  ----------  interrupt   interrupt   interrupt   play
HIGH              wait        FIFO        interrupt   interrupt   play
NORMAL            wait        wait        FIFO        interrupt   play
LOW               wait        wait        wait        FIFO        play
```

"Wait" means enqueue and play when current cue finishes. "Interrupt" means cancel the current cue (or fade it out — see Cancellation semantics) and play the new one immediately. "FIFO" means enqueue at the back of the same priority class.

## Cooldowns

Each cue declares a `cooldown_key` (an arbitrary string the author chooses) and the queue tracks `last_played_at[cooldown_key]`. If a new cue with the same key is enqueued before `last_played_at + default_cooldown_for_priority`, it's dropped silently.

Default cooldowns:
- CRITICAL: **0** (no suppression)
- HIGH: **4s**
- NORMAL: **8s**
- LOW: **30s**

Authors can override per-intent: `cooldown_sec=2` etc. The override is honoured even if it's lower than the priority default; the queue trusts the author.

Common cooldown keys:
```
"war_room.briefing"                   # don't replay a briefing within 30s
"madden26.formation_locked"           # don't read the same formation twice
"warzone.danger_alert.behind"         # one CRITICAL danger every 0s — but
                                      # the *event* itself doesn't repeat
                                      # because VAF dedupes upstream
```

## Cancellation semantics

When an interrupt cancels a cue:

1. **Synthesis still streaming** — abort the streaming TTS connection. ElevenLabs supports streaming, so the bytes already sent play out then stop; no extra latency penalty.
2. **Audio mid-playback** — fade out over 40ms (cosine envelope). Avoids audible click.
3. **Queue position retained?** — by default, cancelled cue is dropped. Authors can mark `requeue_on_interrupt: True`:
   - True: cue goes back into the queue at its priority FIFO position when the interrupting cue ends. Useful for the pre-game briefing — a CRITICAL danger cue interrupts, then the briefing resumes.
   - False (default): cue is gone. Useful for "kill confirmed" announcements — by the time the interrupt clears, the kill is no longer relevant news.

For requeueable cues, the renderer remembers where it left off (text-token offset). On resume, it re-renders from that offset, preserving context.

## Game-audio ducking

Per [01-core-service-spec.md §"Audio out + game-audio ducking"](01-core-service-spec.md), the queue manager controls the duck signal:

```
On cue start:    send `duck_audio` with attenuation_db = priority-dependent
                 default: -12 (HIGH/NORMAL/LOW), -18 (CRITICAL)
                 ramp: 100ms cosine
On cue end:      send `unduck_audio`
                 ramp: 200ms cosine
```

The agent (or the in-app fallback) honours these messages. Multiple overlapping cues are collapsed — the duck is asserted once and held until no cue is playing.

## Scheduling specifics

### Pre-emption vs. graceful handoff

When a HIGH cue arrives mid-NORMAL, the default is "interrupt." Some pages opt into "graceful handoff" — wait for the next sentence boundary in the current cue, then interrupt. Worth it for narrative flows like the War Room pre-game briefing where a hard cut feels jarring.

Page profiles declare per-intent:
```python
INTERRUPT_BEHAVIOR = {
    Intent.WAR_ROOM_PRE_GAME_BRIEFING: InterruptBehavior.GRACEFUL_HANDOFF_MAX_2S,
    Intent.WARZONE_BR_DANGER_FROM_BEHIND: InterruptBehavior.HARD_CUT,    # always
}
```

`GRACEFUL_HANDOFF_MAX_2S` means: wait up to 2 seconds for a sentence boundary in the in-flight cue. If 2s elapses without one, hard-cut. Prevents indefinite blocking.

CRITICAL never honours graceful handoff — always hard-cuts.

### Sport cadence influence

Per [02-madden26-language-profile-spec.md §"Cadence"](02-madden26-language-profile-spec.md), each language profile declares cadence rules. The queue consults them at scheduling time:

- Football's `SNAP_INTERRUPTION_RULE = "duck_only"` means a `PLAY_STARTED` event during a cue causes a duck (drop −18dB extra) but NOT cancellation. This lets a long War Room briefing continue softly under the snap audio rather than vanishing.
- Basketball's `INTERRUPT_ON_SHOT_CLOCK_RESET = True` makes shot-clock-reset events trigger a cue cancellation (continuous play means stale cues are useless).

Per-sport cadence rules are queue policies, not scripts.

## Edge cases

### Two CRITICAL cues at once

Most realistic case: dual danger alerts in BR. The queue holds at most one CRITICAL in flight. If two arrive within ~50ms:
- The first plays.
- The second is checked for `cooldown_key` collision. If same key, drop. If different key, queue at CRITICAL FIFO and play after the first.

### Cue arrives while session is opening

Cues queued before the session is fully ready (TTS provider not yet ready) buffer in a pending list with a 5s TTL. If the session opens within 5s, they flush in order. If not, dropped with reason `session_not_ready`.

### Player switches Integrity Mode mid-cue

Per [01-core-service-spec.md §"HTTP: POST /api/v1/sessions/{id}/integrity-mode"](01-core-service-spec.md), this triggers:
- In-flight cue: cancelled if the new mode disallows it. (Hard cut, no fade — we want to be visibly compliant.)
- Pending cues in queue: re-evaluated; ones that violate the new mode are dropped.
- A CRITICAL `INTEGRITY_MODE_BREACH_AUTOSTOP` cue plays briefly: "Voice paused for tournament mode."

### TTS provider degrades

If ElevenLabs starts returning errors, the queue:
- Existing cues complete (using whatever bytes already streamed).
- New cues route to the Coqui fallback automatically (per [01-core-service-spec.md §"TTS provider — decision and fallback"](01-core-service-spec.md)).
- One-time CRITICAL cue plays: "Voice quality degraded" (uses Coqui to deliver this).

## Authoring guidance

### Picking a priority

Use this decision tree:

```
Is missing this cue dangerous (death, breach, error)?
    YES → CRITICAL
    NO  → ↓
Did the player just ask for it directly (button tap, voice command)?
    YES → HIGH
    NO  → ↓
Is it scheduled coaching content (briefing, drill cue, gameplan read)?
    YES → NORMAL
    NO  → ↓
LOW
```

### Picking a cooldown key

- Be specific: `madden26.war_room.opponent_tendency.${tendency_id}` not `war_room.cue`. Otherwise distinct cues get suppressed by overly-broad keys.
- Don't include payload data that varies per call (e.g., timestamps) — that defeats cooldown.

### When to use `requeue_on_interrupt`

True for cues where the *content* is still relevant after the interruption:
- Long structured briefings (War Room, Tournament round briefing)
- Drill rep cues at the start of a rep

False for cues where the content is stale post-interruption:
- Real-time announcements ("kill confirmed" — by the time the interrupt clears, no longer news)
- Mood update responses (player's mood may have changed)

## What this spec does not decide

- **Specific intent → priority assignments** for each page. Page profiles ([03-war-room-page-profile-spec.md](03-war-room-page-profile-spec.md) covers War Room) own those.
- **Cadence rules per sport.** Language profiles ([02-madden26-language-profile-spec.md](02-madden26-language-profile-spec.md) covers Madden) own those.
- **Tier or mode gating overlay.** Docs #06, #07.
