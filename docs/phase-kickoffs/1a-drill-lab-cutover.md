# Phase 1a Kickoff — Drill Lab Cutover

- **Phase:** 1a (first per-page cutover from mocked vision_client to real VAF pipeline)
- **Kickoff date:** TBD (after Phase 0 PR #62 merge + L2 webhook-alarm wiring)
- **Target window:** 1 week of build + 7-day observation = ~2 weeks calendar
- **Source:** [docs/specs/03-mock-removal-and-page-wiring.md §3 Phase 1a](../specs/03-mock-removal-and-page-wiring.md), [ADR 0001](../adr/0001-feature-flag-infrastructure.md), [ADR 0003](../adr/0003-webhook-delivery-durability-v1.md), [docs/phase-completions/0-vaf-foundation.md](../phase-completions/0-vaf-foundation.md).
- **Status:** Brief only. No implementation begins until sign-off.

## Why Drill Lab is first

Per Spec #03 cutover-order rationale:

1. **Simplest event subscription.** Drill Lab needs only one event type: `FORMATION_LOCKED`.
2. **Most-mocked page today.** The current `VisionAudioForgeService.startDrillMonitoring` polls a backend that proxies the mocked `vision_client.py`. Replacement is a clean swap.
3. **Easiest regression detection.** Rep counting is visible and quantified — if the cutover misroutes events or drops, the player sees "rep count not advancing" within seconds.

## Drill Lab cutover plan

### What changes in code

| File | Change |
|---|---|
| `frontend/src/hooks/useVisionEvents.ts` | **New file.** React hook opening a WebSocket to `services/visionaudioforge/`'s `/ws/events/{session_id}`. Predicate-filtered subscriber returning the latest matching event + a derived state machine. Per Spec #03 §2. |
| `frontend/src/lib/services/visionaudioforge.ts` | **Modified.** `VisionAudioForgeService` becomes a feature-flag-gated dual-path: real WS subscription when `VAF_REAL_PIPELINE_ENABLED_DRILL_LAB=true`, legacy REST polling otherwise. Method signatures preserved so callers compile. |
| `frontend/src/app/(dashboard)/drills/page.tsx` | **Modified.** Lines that call `VisionAudioForgeService.startDrillMonitoring` get rewrapped: when flag on, replace polling with `useVisionEvents({ event_type: "FORMATION_LOCKED" })`; on each event, increment the rep counter and compare to the drill's target formation. |
| `frontend/src/app/(dashboard)/drills/simlab/page.tsx` | **No change in Phase 1a.** SimLab cutover is Phase 1b. Lines 482–514 stay on the legacy path until the SimLab flag flips. |
| `services/visionaudioforge/app/api/events.py` | **New file.** WebSocket endpoint `/ws/events/{session_id}` that fans out events from the per-session queue to subscribers. (Phase 0 only ships the webhook publisher, not the WS subscriber surface.) |
| `services/visionaudioforge/app/core/dispatcher.py` | **Modified.** When a dispatcher emits events, also push to the session's WS subscriber queue (in addition to the webhook publisher). |

### Build sequence

```
Day 1  — events WS endpoint in VAF core (services/visionaudioforge/app/api/events.py + dispatcher fan-out)
Day 2  — useVisionEvents hook (frontend/src/hooks/useVisionEvents.ts) + unit tests
Day 3  — Drill Lab page rewire behind feature flag (drills/page.tsx)
Day 4  — Settings → Game Settings flag exposure (per ADR 0001) + ops runbook entry
Day 5  — End-to-end manual test on staging with the synthetic fixture
Day 6  — Staff-cohort flag flip + observation kickoff
Day 7+ — Observation window (7 days)
```

## Feature flag setup per ADR 0001

ADR 0001 chose the env-var-driven Settings table. Per-page granularity.

### Flag definition

| Flag | Default | Owner | Rollout target |
|---|---|---|---|
| `VAF_REAL_PIPELINE_ENABLED_DRILL_LAB` | `false` | Backend ops | Staff cohort first (Day 6), all Competitive+ tier players if acceptance passes (Day 13+) |

The flag is added to `backend/app/core/settings.py` (the central settings module, env-readable + override via `settings.json`). The frontend reads it via the existing `/api/v1/users/me/settings` endpoint extended with a `feature_flags: dict[str, bool]` field.

### Flip mechanism

- **Engineer flip:** edit `settings.json`, restart backend ECS task. ~30 seconds. The frontend hook reads on next page load + on a 60-second poll.
- **No UI for non-engineers** in Phase 1a. The flag is engineer-flippable only; this matches ADR 0001's "engineer gate-keep flips" tradeoff.
- **Audit trail:** git blame on `settings.json` is the audit. Operations runbook documents who flipped what when, with rationale.

### Per-cohort rollout via the flag

The single boolean flag does not natively support per-user targeting (ADR 0001 explicitly traded this off). To get per-cohort rollout in Phase 1a:

1. **Hardcoded staff allowlist** in the backend, evaluated at request time:

   ```python
   # backend/app/core/feature_flags.py (new)
   STAFF_COHORT_USER_IDS: set[str] = {
       "5041bbe7-...",  # Ivan
       # 4 more founding-team user_ids
   }
   TRUSTED_PLAYERS_COHORT_USER_IDS: set[str] = {
       # 5 trusted-player user_ids — TBD with sign-off
   }
   def vaf_pipeline_enabled_for(user_id: str) -> bool:
       if not settings.VAF_REAL_PIPELINE_ENABLED_DRILL_LAB:
           return False  # global kill-switch
       if user_id in STAFF_COHORT_USER_IDS:
           return True
       if user_id in TRUSTED_PLAYERS_COHORT_USER_IDS:
           return True
       # All other users: stay on the legacy mock until promotion
       return settings.VAF_DRILL_LAB_PROMOTED_TO_ALL  # second flag
   ```

2. **Two-stage flag pattern:** `VAF_REAL_PIPELINE_ENABLED_DRILL_LAB` (master kill-switch — stays `true` once enabled) + `VAF_DRILL_LAB_PROMOTED_TO_ALL` (default `false`; flipped to `true` on Day 13+ if acceptance passes).

The two-stage pattern keeps the rollback surface minimal: the master kill-switch can drop everyone back to mock instantly, and the promoted flag only widens the cohort.

## Staff rollout cohort

User-suggested: founding team + 5 trusted players.

### Founding-team cohort (Day 6 flip)

5 users, hand-picked. Active EsportsForge users who can drop everything to triage if the cutover misbehaves.

- Ivan Green (`5041bbe7-...`) — primary
- 4 additional founding-team user_ids — TBD before Phase 1a kickoff. Confirm via Slack-equivalent channel; populate `STAFF_COHORT_USER_IDS`.

### Trusted-player cohort (Day 9 flip)

5 users from outside the founding team. Selection criteria:

- **Active drillers** — placed at least 20 drill reps in the last 30 days (queryable from existing analytics).
- **Engaged with feedback** — have submitted at least one in-app feedback report. They'll notice and report regressions.
- **Subscription tier ≥ Competitive** — they have voice-coaching active, so they're already engaged with the platform's AI surfaces.
- **Mix of titles** — at least 3 of the 5 should play Madden 26 (since that's the only adapter live in Phase 1a). Including 1–2 non-Madden players is intentional: they'll surface the edge case where the title isn't yet supported.

Action: publish a "Phase 1a beta" opt-in form in the in-app notification center on Day 1 of the build week. Pick 5 from respondents who match criteria.

## 7-day observation period plan

Starts Day 6 (staff flip) and runs through Day 13. Day 9 onwards adds the trusted-player cohort; the same 7-day clock continues from Day 6. Day 13+ is the promotion-decision point.

### What's monitored

| Metric | Target | Source | Alarm |
|---|---|---|---|
| **VAF webhook delivery rate** (per ADR 0003) | ≥ 99.9% per session | `services/visionaudioforge/app/core/webhook.py` `_delivered` / `_failed` exposed via `/api/health`, scraped to CloudWatch every 10 s | **>0.1% failure sustained over 60 minutes → auto-upgrade trigger fires** (per ADR 0003 — must upgrade to Redis Streams before Phase 1c) |
| **`FORMATION_LOCKED` events delivered to Drill Lab page** | ≥ 99% of expected events (one per drill rep) | New telemetry event `drill_lab_event_received` emitted by the hook | Manual investigation if <95% over 24 hours |
| **Drill Lab page error rate** | ≤ 110% of mocked-baseline (i.e., <10% increase) | Sentry breadcrumbs on `/drills` page, segmented by user cohort | Auto-rollback at >2× baseline (per Spec #03 §4 trip wires) |
| **End-to-end latency p95** | <2 s capture → event-rendered-on-page | New `_e2e_latency_ms` field on event envelopes (set in capture agent at JPEG-encode time, computed at frontend hook) | Manual investigation at >5 s for 5 minutes (per Spec #03 §4) |
| **WS connection failure rate** | <1% of session-opens succeed | VAF core's `/api/health` `active_sessions` minus client-side connect attempts | Auto-rollback at >5% (per Spec #03 §4) |
| **User-reported feedback** | 0 critical reports | In-app feedback bell | Manual investigation at >3 critical reports in 24 hours |

### Daily check-ins

- **Day 6 — Staff flip.** Slack-equivalent message: "Phase 1a is live for staff cohort. Run a drill. Flag anything that feels off." Operator (TBD) checks dashboard at +1h, +6h, +24h.
- **Day 7.** Day-1 review meeting. Decision: continue, pause for fix, or roll back.
- **Day 9 — Trusted-player cohort flip.** In-app DM to selected players: "You're on the Phase 1a beta. Here's the feedback channel."
- **Day 10–12.** Daily metric review (5-minute async standup).
- **Day 13.** Day-7 review meeting. Promotion decision.

## Rollback wire configuration per ADR 0003

### Auto-rollback trip wires (per Spec #03 §4 + ADR 0003)

Configured in CloudWatch (or equivalent) before Day 6:

| Wire | Threshold | Action | Notification |
|---|---|---|---|
| **VAF webhook failure rate** | >0.1% sustained over 60 min | **Trigger Phase 1c-blocking flag**: stop scheduling Phase 1c kickoff until Redis Streams ships (per ADR 0003). **Does not auto-flip Drill Lab flag** — webhook loss may be tolerable for FORMATION_LOCKED. | Page oncall + post-mortem |
| **Drill Lab page error rate** | >2× mocked-baseline over 5 min | **Auto-flip `VAF_REAL_PIPELINE_ENABLED_DRILL_LAB` to `false`.** | Page oncall |
| **End-to-end latency p99** | >5 s sustained over 5 min | Manual investigation (no auto-flip) | Page oncall, alarm in dashboard |
| **WS connection failure rate** | >5% over 5 min | **Auto-flip flag to `false`.** | Page oncall |
| **User feedback "broken" reports** | >3 critical over 24 hours | Manual investigation (no auto-flip) | Slack alert |

### Manual rollback path

Operator can flip `VAF_REAL_PIPELINE_ENABLED_DRILL_LAB` to `false` in `settings.json`, restart backend task. ~30-second rollback. The Drill Lab page hook detects the flag change on next 60-second poll and reverts to the legacy REST polling path. Player drill state is preserved (rep counter is server-side; the source of truth doesn't change with the cutover).

### What rollback does NOT recover

- Events already published to the bus stay published. Backend retains them per its own retention policy.
- Capture agent stays running and stays connected to VAF core. Other pages that have already cut over (Phase 1b, 1c) are unaffected.
- The mock code stays in tree until Phase 3 deletion (per ADR 0004). Rollback is always available.

### Phase-1c-blocking trigger (per ADR 0003)

If the webhook failure-rate alarm fires during Phase 1a or Phase 1b, **Phase 1c (Arsenal + War Room) cannot kick off until Redis Streams durable bus ships.** This is recorded in the Phase 1c kickoff-checklist as a hard prerequisite.

## Acceptance criteria for promoting to all Competitive+ tier users

The Day 13 promotion-decision meeting goes "yes" only if **every** criterion below is met. Any "no" → defer promotion, fix root cause, restart 7-day clock.

| # | Criterion | How verified |
|---|---|---|
| 1 | Webhook delivery rate ≥ 99.9% over the 7-day cohort window | CloudWatch dashboard time-series |
| 2 | `FORMATION_LOCKED` event delivery to the page hook ≥ 99% of expected | New telemetry counter |
| 3 | Drill Lab page error rate increase ≤ 10% vs mocked baseline | Sentry comparison, cohort-segmented |
| 4 | End-to-end latency p95 ≤ 2 s sustained | CloudWatch p95 |
| 5 | WS connection failure rate ≤ 1% | Frontend connect-attempt vs core-side `/api/health` `active_sessions` |
| 6 | Zero critical user-feedback reports in the cohort | In-app feedback review |
| 7 | No auto-rollback fired during the 7-day window | Alarm history |
| 8 | The webhook failure-rate alarm did NOT fire (per ADR 0003) | Alarm history. If it fired, Phase 1c is blocked but Phase 1a promotion is also paused for re-evaluation. |
| 9 | Manual UX validation by 3 of the 10 cohort users — "the rep counter feels normal, no perceptible delay" | Async written sign-off, recorded in this doc |
| 10 | Mock REST endpoint received zero hits from the staff cohort during the window | Backend log filter — confirms the cutover actually routed traffic to the new path |

If all 10 pass: flip `VAF_DRILL_LAB_PROMOTED_TO_ALL=true`. All Competitive+ tier users move to the real pipeline.

If 1–2 criteria fail: investigate, fix, restart the 7-day cohort observation. Don't promote until all 10 are clean.

If 3+ criteria fail: the cutover has a structural issue. Pause Phase 1a, investigate root cause, **possibly delay Phase 1b** (SimLab + Gameplan) which depends on the same `useVisionEvents` infrastructure.

## Out of scope for this brief

- Phase 1b (SimLab + Gameplan cutover) — gets its own kickoff brief after Phase 1a stabilizes.
- Phase 1c (Arsenal + War Room cutover) — gets its own kickoff brief, gated on Madden adapter v0.3 (per ADR 0010) **and** webhook durability not having tripped its ADR 0003 alarm.
- Phase 2 (Analytics Film Room) — separate kickoff.
- Mock deletion (Phase 3, Week 12+) — calendar-anchored, not gated by Phase 1a alone.

## Approvals required before kickoff

1. **Phase 0 PR #62 merged to main.**
2. **Webhook failure-rate alarm wired** to CloudWatch (per Phase 0 lesson L2). Operator confirms it triggers test-mode at >0.1% synthetic failure.
3. **Staff cohort identified** — 5 user_ids populated in `STAFF_COHORT_USER_IDS` constant.
4. **Trusted-player cohort identified** — 5 user_ids populated in `TRUSTED_PLAYERS_COHORT_USER_IDS` constant. Players consented via opt-in form.
5. **Resource allocation** — 1 backend engineer + 1 frontend engineer for the 5-day build week. 1 operator on call during the 7-day observation window.
6. **Ops runbook entry** for "How to flip `VAF_REAL_PIPELINE_ENABLED_DRILL_LAB`" published in the team wiki.

After approvals, kick off Day 1 of the build sequence.
