# Event Bus Contract — Universal Game State Schema

> Companion: [02-core-service-spec.md](02-core-service-spec.md), [04-madden26-adapter-spec.md](04-madden26-adapter-spec.md).
> **This document is a locked surface.** Adapter authors implement against it. Agent authors consume from it. Changes require a major-version bump and migration plan. Touch this only with the platform tech lead's sign-off.

## Why this matters

The whole point of the multi-title architecture is that every downstream agent (the 57 in EsportsForge's brain) consumes events from the same bus regardless of which title produced them. Without a stable contract:

- Adapter authors invent their own shapes → agent authors write 11 case-statements per consumer.
- A schema change in Madden's adapter breaks every football agent silently.
- Sport-archetype agents (e.g., GameplanAgent for football) can't generalise across Madden + CFB.

The contract solves this by separating the **envelope** (universal) from the **payload** (title-specific, but shaped by sport-archetype rules).

## Envelope — every event has these fields

```python
class EventEnvelope(BaseModel):
    """Common envelope for every event published to the bus."""

    event_id: str                 # ULID, monotonic per session
    session_id: str
    user_id_hash: str             # one-way hash of user_id; raw user_id never leaves the core
    title: TitleEnum              # discriminator for `payload`
    timestamp: datetime           # UTC; when the event was emitted by the adapter
    captured_at: datetime         # UTC; when the underlying frame was captured
    confidence: float             # 0.0–1.0; adapter's confidence in this event
    adapter_version: str          # "madden26@0.3.1" — agents can require minimums

    event_type: EventType         # enum, see below
    payload: GameStatePayload     # discriminated union, keyed by `title`
```

**`confidence` semantics:**
- `>= 0.9` — high confidence; agents act on it without quoting evidence.
- `0.7–0.9` — medium; agents may surface "I think X" instead of "X happened".
- `< 0.7` — low; events at this confidence are still emitted but flagged. UI hides them by default; agents may use them for soft signals only.

Adapters never emit confidence outside `[0.0, 1.0]`. Below `0.5` events are dropped at the core (configurable per adapter).

## Event types — universal taxonomy

Two channels of events:

### A. State snapshots — `event_type: SNAPSHOT`

A periodic dump of the current game state. Low cadence (default 1 Hz; adjustable per adapter). Cheap for UI to render (just replace the displayed state with the latest snapshot). Subscribers can compute deltas if they care.

Snapshot payload is the title's `GameState` model (see "Title-specific payloads" below).

### B. Discrete events — everything else

The thing-just-happened events. Higher information density, lower volume. These are what agents subscribe to.

Universal event types (each title may emit a subset):

| `event_type` | Meaning | Sports that emit |
|---|---|---|
| `SESSION_STARTED` | First confident detection in a session | all |
| `MATCH_STARTED` | New game/match begins (kickoff, tip-off, fight start) | all team/combat sports |
| `MATCH_ENDED` | Match ended (final whistle, KO, last hand) | all |
| `SCORE_CHANGE` | Scoreboard ticked | football, basketball, soccer, baseball |
| `POSSESSION_CHANGE` | Possession flipped | football, basketball, soccer |
| `DOWN_AND_DISTANCE` | Down/distance updated | football only |
| `PLAY_STARTED` | Play snapped / pitch released / shot taken | football, baseball, basketball |
| `PLAY_ENDED` | Play resolved (tackle, basket, hit) | football, baseball, basketball |
| `FORMATION_LOCKED` | Pre-snap formation identified | football |
| `COVERAGE_LOCKED` | Defensive coverage identified post-snap | football, basketball |
| `KILL_CONFIRMED` | Kill registered | FPS, BR |
| `DOWN_CONFIRMED` | Player downed (revivable) | BR |
| `DEATH_CONFIRMED` | Player died (out for the round) | FPS, BR, combat |
| `LOOT_PICKED_UP` | Item collected | BR |
| `ZONE_PHASE_CHANGE` | Circle/zone advanced | BR |
| `LOADOUT_CHANGE` | Weapon/equipment swap | FPS, BR |
| `ROUND_STARTED` | New round begins | combat, BR |
| `ROUND_ENDED` | Round ends | combat, BR |
| `DAMAGE_DEALT` | Damage applied to opponent | combat |
| `DAMAGE_TAKEN` | Damage taken by player | combat, FPS |
| `STANCE_CHANGE` | Fighting stance switch | combat |
| `STROKE_TAKEN` | Golf stroke completed | golf |
| `HOLE_COMPLETED` | Hole finished | golf |
| `HAND_COMPLETED` | Card hand resolved | card |
| `MENU_DETECTED` | Player navigated to a menu (capture pauses) | all |
| `INTEGRITY_DROP` | Adapter dropped a frame for integrity-mode reasons | all (debug) |
| `SNAPSHOT` | Periodic state dump (channel A) | all |

This list is the complete v1 taxonomy. New event types require a contract bump. Adapters may emit a subset; they must never emit types not in this list.

## Subscription patterns

Agents and the frontend subscribe via predicate filters on the envelope. Three common patterns:

```python
# 1. All events for a session, regardless of title
sub.subscribe(filter=lambda e: e.session_id == "ses_01HXXX")

# 2. All football events across Madden + CFB
sub.subscribe(filter=lambda e: e.title in {TitleEnum.MADDEN26, TitleEnum.CFB26})

# 3. Score changes across all titles, for a global "live ticker" UI
sub.subscribe(filter=lambda e: e.event_type == EventType.SCORE_CHANGE)
```

The core implements these as predicate functions over the envelope; subscribers get a callback per matching event.

## Title-specific payloads (discriminated union by `title`)

The `payload` field is shaped per title. Pydantic v2 discriminated unions enforce this:

```python
GameStatePayload = Annotated[
    Union[
        Madden26Payload,
        CFB26Payload,
        NBA2K26Payload,
        EAFC26Payload,
        MLB26Payload,
        WarzonePayload,
        FortnitePayload,
        UFC5Payload,
        UndisputedPayload,
        PGA2K25Payload,
        VideoPokerPayload,
    ],
    Field(discriminator="title"),
]
```

Agents that care about a specific title pattern-match on the discriminator and get a fully-typed payload. Agents that subscribe across titles within a sport-archetype use the shared base class for their archetype (below).

## Sport-archetype base payloads

To enable agents to work across multiple titles within a sport, payloads inherit from sport-archetype bases:

```python
class FootballPayload(BaseModel):
    """Shared shape between Madden 26 and CFB 26."""
    score_home: int
    score_away: int
    quarter: int
    clock: str               # "MM:SS"
    down: int | None         # None outside of plays
    distance: int | None
    field_position: str      # "OWN_35", "OPP_22", "MIDFIELD"
    possession: Literal["home", "away"] | None
    offensive_formation: str | None
    defensive_formation: str | None

class Madden26Payload(FootballPayload):
    title: Literal[TitleEnum.MADDEN26]
    # any Madden-specific extras (e.g., Madden's "Coach Mode" indicator)

class CFB26Payload(FootballPayload):
    title: Literal[TitleEnum.CFB26]
    # CFB-specific extras (e.g., crowd-noise meter, momentum bar)
```

GameplanAgent subscribes to `FootballPayload` and works against both Madden and CFB. NBA-specific PnR analysis subscribes to `BasketballPayload`. And so on.

### The seven sport-archetype bases

| Base | Titles | Core fields |
|---|---|---|
| `FootballPayload` | Madden 26, CFB 26 | score, clock, quarter, down, distance, field_position, possession, formations |
| `BasketballPayload` | NBA 2K26 | score, clock, quarter, shot_clock, possession, offensive_action, defensive_scheme |
| `SoccerPayload` | EA FC 26 | score, clock, half, possession, formation_home, formation_away, last_action |
| `BaseballPayload` | MLB The Show 26 | score, inning (1-9 + half), outs, count, base_state, batter, pitcher |
| `BattleRoyalePayload` | Warzone, Fortnite | health, armor/shield, weapons, zone_phase, zone_timer, teammates_alive, kills |
| `CombatSportPayload` | UFC 5, Undisputed | round, round_clock, fighter_health (own + opp), stance, damage_state, last_strike |
| `GolfPayload` | PGA TOUR 2K25 | hole_number, par, current_stroke, distance_to_pin, lie, wind, score_to_par |
| `CardPayload` | Video Poker | hand_id, dealt_hand, held_cards, paytable_state, credits, bet |

(That's 8 bases for 11 titles; FPS-vs-BR merged because Warzone and Fortnite share the BR shape closely enough.)

## Concrete examples

The user supplied these in the prompt; locking them as the canonical examples:

### Football

```json
{
  "event_id": "01HXXX...",
  "session_id": "ses_01HXXX",
  "user_id_hash": "abc...",
  "title": "madden26",
  "timestamp": "2026-05-06T22:31:14.812Z",
  "captured_at": "2026-05-06T22:31:14.760Z",
  "confidence": 0.94,
  "adapter_version": "madden26@0.3.1",
  "event_type": "SNAPSHOT",
  "payload": {
    "title": "madden26",
    "score_home": 14, "score_away": 10,
    "quarter": 3, "clock": "8:34",
    "down": 2, "distance": 7,
    "field_position": "OWN_35",
    "possession": "home",
    "offensive_formation": "Shotgun Trips",
    "defensive_formation": "Cover 3"
  }
}
```

### Basketball

```json
{
  "event_id": "01HXXX...",
  "session_id": "ses_01HXXX",
  "user_id_hash": "abc...",
  "title": "nba2k26",
  "timestamp": "2026-05-06T22:31:14.812Z",
  "captured_at": "2026-05-06T22:31:14.760Z",
  "confidence": 0.91,
  "adapter_version": "nba2k26@0.1.0",
  "event_type": "SNAPSHOT",
  "payload": {
    "title": "nba2k26",
    "score_home": 87, "score_away": 84,
    "quarter": 4, "clock": "2:17",
    "shot_clock": 14,
    "possession": "home",
    "offensive_action": "PnR_high",
    "defensive_scheme": "ICE"
  }
}
```

### Battle Royale

```json
{
  "event_id": "01HXXX...",
  "session_id": "ses_01HXXX",
  "user_id_hash": "abc...",
  "title": "warzone",
  "timestamp": "2026-05-06T22:31:14.812Z",
  "captured_at": "2026-05-06T22:31:14.760Z",
  "confidence": 0.88,
  "adapter_version": "warzone@0.1.0",
  "event_type": "KILL_CONFIRMED",
  "payload": {
    "title": "warzone",
    "health": 150, "armor": 3,
    "weapon_primary": "MCW",
    "weapon_secondary": "Renetti",
    "circle_timer": "1:24",
    "teammates_alive": 3,
    "last_event": "kill_confirmed"
  }
}
```

## Versioning

`adapter_version` follows semver-with-context: `<title>@<major>.<minor>.<patch>`. Examples: `madden26@0.3.1`, `cfb26@1.0.0`, `warzone@0.1.0-beta`.

Agent code can express minimum-version requirements:

```python
@subscribe(title=TitleEnum.MADDEN26, min_adapter="madden26@0.3.0")
def handle_madden_event(event: MaddenEvent): ...
```

Events from older adapters are dropped before reaching the agent. The dashboard surfaces a "your adapter is out of date" message.

The contract document itself versions the schema in the file's frontmatter (when first locked) — this v1 doc is **schema v1.0.0**. Breaking shape changes ship as v2 with a migration window.

## Field naming conventions

To make the schema feel consistent across titles:

- Time fields are strings in `MM:SS` format (or `M:SS` if minutes < 10). Numeric seconds where machine-readable (`shot_clock`, `circle_timer_sec`, `round_clock_sec`).
- Scores are always `score_home` / `score_away` (never `home_team`, `their_score`, etc.).
- Possession is always `Literal["home", "away"]`.
- Health-style fields use the title's natural max (e.g., `health: 150` for Warzone Resurgence, `health: 100` for standard MP).
- Enums are SCREAMING_SNAKE_CASE strings (`event_type: "SCORE_CHANGE"`, not `"score_change"` or `"scoreChange"`).
- Adapter-specific extras live in a `extras: dict[str, Any]` field (last-resort escape hatch — prefer adding typed fields and bumping the adapter version).

## What this spec does not decide

- **How adapters detect events.** That's per-adapter (Doc #04 covers Madden's approach).
- **Which agents subscribe to which events.** That's the agents' own concern, codified in their handler decorators.
- **Persistence of events on the EsportsForge side.** Out of scope here — the EsportsForge backend stores what it wants when the webhook fires.
- **Latency budgets.** Per-adapter, per Doc #02 §"Adapter contract".
