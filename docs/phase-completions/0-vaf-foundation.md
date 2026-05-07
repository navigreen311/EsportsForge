# Phase 0 Completion — VAF Foundation

- **Phase:** 0 (foundation / parallel build)
- **Date of completion:** 2026-05-07
- **Sign-off:** Ivan Green
- **Source:** [docs/specs/02-visionaudioforge-core.md](../specs/02-visionaudioforge-core.md), [docs/specs/01-capture-agent.md](../specs/01-capture-agent.md), [docs/specs/03-mock-removal-and-page-wiring.md](../specs/03-mock-removal-and-page-wiring.md), [ADRs 0001–0010](../adr/README.md), [docs/integrations/visionaudioforge/05-phase-1-milestones.md §"M1"–"M5"](../integrations/visionaudioforge/05-phase-1-milestones.md).

## Streams

| Stream | Scope | Acceptance | Status |
|---|---|---|---|
| **Stream A — VAF core service + Madden 26 adapter v0.1** | FastAPI on `:8100`; session/router/integrity-gate/dispatcher/webhook-publisher; Madden 26 adapter with stubbed OCR + formation detector + snap detector + state assembler | Service boots; adapter loads; smoke test produces valid `EventEnvelope` events | ✅ |
| **Stream B — Capture agent skeleton** | Python+OpenCV+websockets agent; test-video source; TOML config; WS client with frame-batch transport + heartbeat + control-message receive loop | Agent connects to core, streams JPEG batches, receives session_open handshake | ✅ |

## Commit hashes

**Both streams shipped in a single PR (`#62`) and a single commit, not separate per-stream merges.** The two streams are clearly delineated by directory boundaries (`services/visionaudioforge/` for Stream A, `agents/capture/` for Stream B) and called out in the commit body, but the merge is one. This is a deviation from the original Phase 1 milestones doc (which framed M1 / M2 / M5 as separate milestones) — see "Deviations" below.

| Stream | PR | Branch | Commit |
|---|---|---|---|
| A + B (combined) | [#62](https://github.com/navigreen311/EsportsForge/pull/62) | `feat/visionaudioforge-phase-0` | `dc6fefa78009642c7c81dce1d93c3eb620760cd6` |

**Merge status as of 2026-05-07:** PR #62 is **open**, not yet merged to `main`. Acceptance criteria are met locally; the procedural merge to `main` is the next action before Phase 1a kicks off.

## Test results

### End-to-end smoke (synthetic fixture)

Run sequence:
1. `services/visionaudioforge/` — uvicorn `app.main:app` on `:8100`, env `ESF_BACKEND_URL=http://127.0.0.1:8002`.
2. `backend/` — uvicorn `app.main:app` on `:8002` (ran on `:8002` instead of `:8001` because of a zombie listener; see Deviations).
3. `agents/capture/` — `python -m capture_agent.main --config config.dev.toml --session-id <ses_id>` against `agents/capture/fixtures/synthetic.mp4` (60-frame 1920×1080 generated).
4. Observed for ~6 seconds.

Result:

```
session: ses_01KR1YNA3PGBN1VGH9BBF2NFJF
agent_connected
title_locked (madden26, confidence 0.95, method=hint)
madden26_adapter_loaded (madden26@0.0.1-phase-0)
→ recent_event_count: 32
→ titles_seen: ["madden26"]
→ last_event_ts: 2026-05-07T19:29:36.225080Z
```

All 32 events conformed to the `EventEnvelope` + `Madden26Payload` discriminated-union shape. Webhook publisher batched and delivered them; `WebhookPublisher.failure_rate` was 0.0 across the run.

### Latency measurements

The dispatcher's per-frame budget enforcement is wired (ADR 0006 — 80 ms ceiling). **Actual per-frame latency was not measured rigorously in Phase 0** — `process_frame` returns near-instantly because the OCR and formation classifier are stubs. Real latency measurement is gated on Phase 1 M5a/M5c when Tesseract and the MobileNetV3 ONNX model land.

What was observed:

| Stage | Observed | Budget | Notes |
|---|---|---|---|
| Capture agent encode + batch | ~330 ms per 4-frame batch at 12 fps | 350 ms | Within Doc #02 §7 budget. |
| WS round-trip (agent → core, loopback) | <5 ms | <50 ms | Local loopback; production target is 50–200 ms. |
| Adapter `process_frame` | <2 ms (stubbed) | 80 ms | Real measurement comes with M5c. |
| Webhook batch flush | ~250 ms | 250 ms | Matches `BATCH_FLUSH_INTERVAL_SEC`. |
| End-to-end (capture → backend `recent_events`) | ~1 s observed | <2 s p99 target | Smoke run is too short for a meaningful p99; instrumented for Phase 1a. |

### Formation classification accuracy

**N/A for Phase 0.** The formation classifier (`FormationDetector.detect_offensive`) is a stub that returns `"shotgun_trips"` with confidence `0.5` regardless of the input frame. The synthetic test fixture (`synthetic.mp4`) is a 60-frame solid-color sequence with no Madden HUD content — measuring accuracy against it would be meaningless.

Real accuracy measurement is gated on Phase 1 M5c, which delivers:
- ~5,000 labeled frames per class via active-learning bootstrap.
- MobileNetV3-Small trained on Colab, exported to ONNX.
- Macro-F1 target ≥ 0.85 on the v0.1 8-class subset (gating CI).

The Phase 1 milestone for that work is the right place for the first real accuracy number.

### What was actually verified in Phase 0

- ✅ Adapter pattern dispatch (registry → `Madden26Adapter.process_frame` → events).
- ✅ Frame-level integrity gate (verified manually: switched session to `tournament` → frames dropped with `integrity_tournament_blocks_capture`).
- ✅ Title-detector hint path (passing `active_title=madden26` → instant lock at confidence 0.95).
- ✅ Event-envelope shape validates against the universal contract (Pydantic discriminator on `title` field).
- ✅ Webhook publisher batches + posts; per-session `_delivered`/`_failed` counters observable.
- ✅ EsportsForge backend Phase 0 endpoints receive events, expose `/sessions/active`.
- ✅ ADR 0009 platform-neutral check: `services/visionaudioforge/` has no `import win32*`, no `\\` literals, no `os.path.sep` mixing.

## Deviations from spec / ADRs

### D1 — Single-PR delivery vs separate milestone merges

**Spec said:** Phase 1 milestones doc (`docs/integrations/visionaudioforge/05-phase-1-milestones.md`) framed M1 (capture agent), M2 (core service), M3 (EsportsForge endpoints), M5 (Madden adapter) as separate per-milestone deliverables, each with its own branch + acceptance.

**What shipped:** all four landed in a single commit (`dc6fefa`) on PR #62.

**Why:** delivery agent (Claude) shipped them together in a single session for vertical-slice clarity — the value of each milestone is hard to validate without the others. Separate PRs would have been merge-and-rebase churn for no review benefit when the same engineer landed them all.

**Should this become a new ADR?** No — this is a delivery-cadence one-off, not an architectural rule. Future milestones (M5a Tesseract install, M5c ONNX classifier) genuinely benefit from separate PRs because the ML training work is substantial and reviewable independently. Phase 1a's per-page cutovers should also be separate PRs (one per page).

### D2 — Operational: zombie listener on `:8001`

**Spec said:** Backend runs on `:8001` (per memory + dev convention).

**What happened:** during the smoke run, prior `uvicorn --reload` parent/child PIDs left a stale `LISTENING` entry on `:8001` even after `taskkill` reported the process gone. New uvicorn binds failed with WinError 10048. Backend was started on `:8002` for the smoke; VAF core's webhook target was redirected via `ESF_BACKEND_URL=http://127.0.0.1:8002`.

**Why:** Windows TCP `LISTEN` state can outlive the owning process when uvicorn `--reload` is killed mid-restart (parent watcher + child worker race). PowerShell's `Get-Process` couldn't find the PID but `Get-NetTCPConnection` still showed it owning the port.

**Resolution for Phase 1:** treat this as an ops gotcha, not an architectural issue. Document in dev-setup memory. Two clean paths: (a) avoid `--reload` for backend dev (use `uvicorn --reload-dir backend/app` if you must), or (b) script a `Stop-Process` + 2-second sleep before any restart.

### D3 — Smoke fixture is synthetic, not Madden gameplay

**Spec said:** Phase 1 M7 specifies "5-minute Madden gameplay clip → fixture for regression testing."

**What shipped in Phase 0:** `agents/capture/fixtures/synthetic.mp4` is a 60-frame solid-color sequence with `cv2.putText` frame numbers. No Madden HUD. Adequate for Phase 0's "frames flow agent → core → adapter → events" smoke; not adequate for Phase 1's accuracy testing.

**Resolution:** Phase 1 M5/M7 will curate a real Madden gameplay fixture (≤50 MB, committed via Git LFS). This is the canonical Phase 1 M7 deliverable.

### D4 — Phase 0 didn't measure real latency

**Spec said:** Doc #02 §7 sets latency targets (capture-to-event p99 < 2s, adapter p95 < 80ms).

**What Phase 0 produced:** stub-driven smoke. Adapter latency is irrelevant when OCR + formation detection are no-ops; webhook latency was observed but only on loopback.

**Resolution:** Phase 1 M5/M6 ships real instrumentation — per-stage timing logs, `_delivered`/`_failed` exposed via `/api/health`, p50/p95/p99 trackers per session.

### D5 — ORB fallback + Madden/CFB disambiguation: code-reserved, not implemented

**ADR 0007 said:** Heuristic primary, ORB fallback after 5 frames without 0.85 confidence, team-abbrev OCR for Madden vs CFB tiebreaker.

**What shipped:** `TitleDetector` skeleton with the `method` field on results, but the actual fallback path is a `pass` (the hint-based path always wins in Phase 0). ORB matching is not invoked.

**Why:** Phase 0 used the active-title hint to bypass the detector, which kept the smoke loop tight. The fallback path is unreachable in current code.

**Resolution:** Phase 1 M4 (title detector real implementation) is the gating milestone. Documented in `services/visionaudioforge/app/core/title_detector.py` with TODO references to ADR 0007.

### D6 — `vision_client.py` mock not yet removed

**Spec said:** `docs/specs/03 §3 Phase 3 — Mock deletion (Week 12+)`.

**What's true:** the mock at `vision_client.py:132` is still in tree. This is correct per the migration plan — Phase 0 ships parallel infrastructure; the mock is removed in Phase 3 after 30 days of all-page stability post-Phase-1c (per ADR 0004).

**No action needed.** Flagged here for clarity.

## Lessons learned for Phase 1 planning

### L1 — Circular import pattern between dispatcher and adapter registry

`services/visionaudioforge/app/core/dispatcher.py` initially imported `app.adapters.registry.get_adapter` at module load; the registry imports the Madden adapter; the Madden adapter's state assembler imports `make_envelope` from the dispatcher. Round trip → circular import.

**Fix shipped:** `make_envelope` extracted to `app/core/envelope.py`; dispatcher does a lazy import of `get_adapter` inside the dispatch function.

**Phase 1 implication:** every new adapter (CFB 26 in Phase 2, NBA in Phase 3, etc.) imports `make_envelope`. The pattern is locked correctly now, but **document this in `docs/integrations/visionaudioforge/04-madden26-adapter-spec.md`** so future adapter authors don't re-trip the cycle. Action: add a "Common pitfalls" section to the Madden adapter spec when M5c lands.

### L2 — Webhook delivery alarm needs a real monitoring hookup

ADR 0003 says: "Alarm threshold: >0.1% sustained over 60 minutes; auto-upgrade trigger: if alarm fires during Phase 1a/b, upgrade to Redis Streams before Phase 1c."

`WebhookPublisher.failure_rate` is exposed as a property. It is **not** wired to any alarm system. Phase 1a's per-page cutover acceptance criteria should not start until either (a) the alarm + paging is wired, or (b) the failure rate is observable in a dashboard the operator checks every 60 minutes. Recommendation: wire to the same CloudWatch alarms the EsportsForge backend uses, with a `vaf.webhook.failure_rate` metric pushed every 10 seconds.

### L3 — Hint-based title lock is too convenient

The Phase 0 smoke uses `active_title=madden26` in `/api/v1/sessions/open` and the title detector uses that hint to lock instantly. This works for the smoke but **the heuristic + ORB fallback paths are completely untested in Phase 0.** Phase 1 M4 must include test fixtures that lock without a hint (real Madden frames + a CFB frame to validate the disambiguation tiebreaker per ADR 0007).

### L4 — Stub adapters can mask schema drift

Phase 0's `Madden26Adapter` returns hardcoded "Shotgun Trips" with confidence 0.5. Because the assembler always succeeds and always emits a SNAPSHOT, the smoke loop validates the *transport* but not the *content*. **Add a regression test in Phase 1 M5c that runs a known Madden gameplay clip end-to-end and asserts at least one `FORMATION_LOCKED` event with confidence ≥ 0.85.** Without this, a future schema change to `Madden26Payload` could pass the existing smoke and break agents downstream.

### L5 — OS-level dev-environment quirks need a runbook

The zombie-listener-on-:8001 issue (D2) is a Windows + uvicorn `--reload` interaction. Will hit any developer running the EsportsForge stack on Windows. **Add to `feedback_esportsforge_dev_setup.md` (memory) before Phase 1a kicks off.** Same applies to PowerShell-vs-Git-Bash divergence (`taskkill //F //PID` Bash quirks vs PowerShell's `Stop-Process`).

### L6 — Phase 1 milestones should account for real ML training time

Phase 0 shipped fast because the ML pieces are stubs. Phase 1 M5c (MobileNetV3 ONNX classifier) explicitly requires ~5,000 labeled frames per class × 8 classes = 40,000 frames + bootstrap-labeling iteration + Colab training. The Phase 1 milestones doc estimates 1.5 days for "M5c offensive formation classifier" — that is **almost certainly optimistic** if active-learning bootstrap is a serious effort. Recommendation: re-estimate M5c at 3–5 days when its kickoff brief is written, with an explicit go/no-go on data availability before scoping.

### L7 — Capture agent's Phase 1 work is heavier than Phase 0 might suggest

Phase 0 ships the agent's transport layer + test-video source. **The Phase 1 work (real DirectShow capture-card driver path, system tray UI, Tk diagnostic window, Win32 hotkeys, Credential Manager wrapper, EV-cert signed installer, reconnect-with-backoff, ring buffer drain-on-reconnect) is closer to 70% of total agent work, not 30%.** Phase 1 M1 final + M8 milestones together should budget for that reality. Recommendation: re-estimate M1 final at 4–5 days (was 1 day for "skeleton") and M8 capture-agent-related work at 2 days.

## Phase 1a readiness

Phase 0 is complete. Phase 1a (Drill Lab cutover) is the next milestone. Prerequisites for Phase 1a kickoff:

- [x] Phase 0 PR #62 acceptance criteria met locally.
- [ ] PR #62 merged to `main`.
- [ ] Webhook delivery alarm wired (per L2).
- [ ] Per ADR 0010: Phase 1c (Arsenal + War Room) is *not* gated by Phase 1a — Drill Lab can proceed on adapter v0.1.
- [ ] Per ADR 0001: feature flag `VAF_REAL_PIPELINE_ENABLED_DRILL_LAB` provisioned in Settings.
- [ ] Staff cohort identified (~10 users) for the Phase 1a observation window.

Kickoff brief: see [docs/phase-kickoffs/1a-drill-lab-cutover.md](../phase-kickoffs/1a-drill-lab-cutover.md).
