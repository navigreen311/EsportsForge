# Phase 1 — Milestone Breakdown

> Companion: [01-capture-agent-spec.md](01-capture-agent-spec.md), [02-core-service-spec.md](02-core-service-spec.md), [03-event-bus-contract.md](03-event-bus-contract.md), [04-madden26-adapter-spec.md](04-madden26-adapter-spec.md).
> Phase 1 ships **the multi-title core architecture + the first adapter (Madden 26)**. Target window: **10–14 working days**.

## What "Phase 1 done" means

A player can:
1. Hook a CLX PC to a PS5 running Madden 26.
2. Launch EsportsForge desktop → capture agent connects to the core.
3. Start a session in the dashboard. Active title auto-detects as Madden 26.
4. Watch the dashboard react to **real game state** — score updates, down-and-distance, offensive formation reads — within 1–2 seconds of on-screen events.
5. Switch Integrity Mode to Tournament → capture pauses; switch back to Offline Lab → capture resumes.

What's explicitly **not** in Phase 1 done:
- Defensive formation / coverage detection (deferred to adapter v0.3)
- Any other title's adapter (Phase 2+)
- Audio capture
- Macros / keyboard shortcuts in the desktop UI

CFB 26 follows in Phase 2 (5–7 days), reusing ~70% of the Madden adapter code and the entire core.

## Milestone list

| # | Milestone | Owner role | Days | Dependencies |
|---|---|---|---|---|
| **M1** | Capture Agent skeleton | Desktop eng | 2–3 | None |
| **M2** | Core service skeleton | Backend eng | 2 | None |
| **M3** | EsportsForge backend integration endpoints | Backend eng | 1 | None |
| **M4** | Title detector v1 (Madden signature only) | ML/CV eng | 1–2 | M2 |
| **M5** | Madden adapter v0.1 — OCR + offensive formation | ML/CV eng | 3 | M2, M4 |
| **M6** | State assembler + event publishing | Backend eng | 1–2 | M2, M5 |
| **M7** | End-to-end integration test (PS5 → dashboard) | Tech lead + manual QA | 1–2 | M1, M2, M3, M5, M6 |
| **M8** | Hardening + Integrity Mode gates + Phase 1 deploy | Backend eng | 1 | M7 |

**Total: 12–17 days** depending on team size and parallel work. With 1 backend, 1 ML/CV, 1 desktop engineer working in parallel, **12–14 days** is realistic.

Critical path: M2 → M4 → M5 → M6 → M7 → M8 (~10 days serial).
M1 and M3 happen in parallel. They're not on the critical path but block M7.

## Per-milestone detail

### M1 — Capture Agent skeleton (2–3 days)

Goals:
- Capture from a connected HDMI capture card via OpenCV (`cv2.VideoCapture`).
- Encode JPEG, batch frames, send over WebSocket to a local mock core.
- Heartbeat every 5s.
- Read config from TOML.
- Diagnostic UI window with status lines.
- Build into a Windows `.exe` via PyInstaller (signing deferred to M8).

Out of scope for M1: ring buffer (defer to M7), `pc-monitor` source (defer to v2 — Madden is console-only anyway), auto-update.

Acceptance:
- Run the agent against a sample MP4 (`test-video` source). It connects to a local stub WS server and sends 10 fps of JPEG frames. Stop, restart — reconnects cleanly.
- Run against a real capture card in dev → dashboard shows frames arriving (in M7).

Deliverable: signed-but-unsigned `.exe`, config schema, dev README. Branch: `vaf/capture-agent-skeleton`.

### M2 — Core service skeleton (2 days)

Goals:
- New FastAPI service. Separate Dockerfile, separate ECR target. Port 8100.
- WebSocket `/ws/ingest` accepts agent connections, validates a stubbed API key, holds the connection open, decodes frames.
- HTTP `POST /api/v1/sessions/open` and `POST /api/v1/sessions/{id}/close`.
- Webhook publisher — POSTs a stub event payload to a configured URL on a 1Hz cadence.
- Health endpoint.
- Pytest skeleton with a fixture that runs the service in-process and connects an in-memory agent.

Out of scope for M2: real adapter dispatch (M6), title detection (M4), integrity gating (M8).

Acceptance:
- Local: run the service. Connect the M1 agent. Frames are decoded successfully and a stub `SNAPSHOT` event is webhooked to the local EsportsForge backend.

Deliverable: `backend/app/services/visionaudioforge_core/` (or a separate `services/visionaudioforge/` repo subdirectory — decide at kickoff). New Dockerfile, ECS task definition diff for review.

### M3 — EsportsForge backend integration endpoints (1 day)

Goals:
- Add `POST /api/v1/auth/validate-capture-key` (validates short-lived agent keys).
- Add `POST /api/v1/visionaudio/events` (webhook receiver for the core service to hit).
- Add `GET /api/v1/visionaudio/sessions/active` (frontend reads to show "session live" in the dashboard).
- Frontend: extend `Settings → Game Settings → Capture Source` with a "Test connection" button that opens a session and verifies the agent is up.

Acceptance:
- Curl-test all four surfaces. Frontend "Test connection" round-trips successfully.

Deliverable: branch `vaf/backend-integration-endpoints`, includes Alembic migration if any new tables (probably one for `capture_keys`).

### M4 — Title detector v1 (1–2 days)

Goals:
- Implement template-matching detector per Doc #02 §"Title detection".
- v1 only loads Madden's signature — the registry has one entry. (Other adapters will register their signatures as they ship.)
- Per-session lock with the 0.85 threshold.
- 30s "give up" timeout.

Acceptance:
- Feed the detector frames from a real Madden gameplay clip → locks within 5 seconds at >=0.9 confidence.
- Feed CFB 26 frames (we don't have the CFB adapter yet, but we can validate that the detector *doesn't* falsely lock on Madden) → reports no confident match.
- Feed menu/loading frames → reports no confident match.

Deliverable: title-detector module with pluggable signature registry. Madden's `hud_signature.png` curated and committed.

### M5 — Madden adapter v0.1 (3 days)

Three sub-parts. Sequence them in this order:

**5a. OCR pipeline (1 day).** Tesseract setup, `hud_regions.json`, numeric/field-position/team-abbr extraction. Unit tests with ~30 pinned fixtures.

**5b. Snap detector (0.5 day).** State machine over the play-clock + frame-difference. Unit tests against a labeled-snap fixture (~10 plays).

**5c. Offensive formation classifier (1.5 days).**
- Most of this time is data prep. Bootstrap labeling: ~50 examples × 8 most common formations = 400 manually labeled frames.
- Train MobileNetV3-Small on Colab (GPU, ~30 min). Export to ONNX.
- Macro-F1 target ≥ 0.85 on the v0.1 8-class subset.
- Wire into the adapter, gate on confidence ≥ 0.85 to emit `FORMATION_LOCKED`.

Deliverable: `backend/app/services/integrations/visionaudioforge_core/adapters/madden26/` package. Tests passing in CI. Branch: `vaf/madden26-adapter-v0.1`.

### M6 — State assembler + event publishing (1–2 days)

Goals:
- Glue M5's outputs into the event-bus contract envelope (Doc #03).
- Adapter dispatch in the core: route frames to Madden adapter when title is locked.
- Event flow: adapter → in-process queue → webhook publisher → EsportsForge backend → DB persistence (deferred? see Open Question 5 — likely v1 just logs).
- Wire the WS subscriber endpoint `/ws/events/{session_id}` for the frontend.

Acceptance:
- Run the full pipe (M1 agent → M2 core → M5 adapter → webhook to EsportsForge backend) against a Madden gameplay clip. Inspect emitted events. Verify they validate against the Pydantic models from Doc #03.

Deliverable: end-to-end works against a fixture clip. No real PS5 yet (that's M7).

### M7 — End-to-end integration test against PS5 (1–2 days)

Goals:
- Hook up the actual hardware: PS5 running Madden 26 → HDMI capture card → CLX PC running the agent → dev-deployed core service → dev EsportsForge backend → dashboard.
- Run a 5-minute Madden session. Validate:
  - Title detection locks on Madden within 10 seconds.
  - Score/clock/down/distance update on the dashboard with <2s lag.
  - At least 8 of 10 plays emit a `FORMATION_LOCKED` event with correct formation.
  - No crashes, no memory leaks (monitor RSS).
- Capture and label the 5-minute session as a CI fixture (compress to <50MB) for regression testing.

Acceptance:
- Eyeball-validation by tech lead + one other stakeholder. Bug list captured for M8.

Deliverable: integration-test report (markdown), CI fixture, bug list.

### M8 — Hardening + Integrity Mode gates + Phase 1 deploy (1 day)

Goals:
- Wire Integrity Mode gates per Doc #02 §"Anti-cheat / Integrity Mode gating" (Madden's rules are simple — full access in Offline Lab, no FORMATION_LOCKED in Ranked, no processing in Tournament).
- Ring buffer in the agent (deferred from M1).
- Sign the agent `.exe` with the EV cert.
- Deploy core service to staging ECS.
- Smoke-test against staging.
- Triage and fix bug list from M7. Defer non-blockers to a Phase 1.1 follow-up branch.

Acceptance:
- Staging works end-to-end. Cut the Phase 1 release tag (`vaf-phase-1-v0.1.0`).

Deliverable: production-ready Phase 1.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Capture-card driver flakiness across vendor models | Med | High | Test matrix in M1 covers Elgato + AVerMedia. If a card fails, document in v1 release notes as unsupported. |
| Madden HUD shifts after a game patch | Low (Phase 1 window is short) | High | `hud_regions.json` is hot-swappable; ship a patched config without redeploying the adapter binary. |
| Tesseract OCR fails on stylized score fonts | Med | Med | Have PaddleOCR (heavier, more accurate) as a fallback engine, configurable. Ship Tesseract first. |
| Formation classifier under-trained at v0.1 | Med | Med | Bootstrap labeling is the bottleneck. Plan in 1.5 days; if it slips, ship at lower formation coverage (top-4 instead of top-8) and iterate. |
| Latency budget exceeded under real-world load | Low | Med | Doc #04 has 22ms slack at v0.1. Add downscaling-before-OCR if needed. |
| Anti-cheat false-positive on the agent | Low (we only read capture-card USB device, no game injection) | Critical | EV-signed binary, kernel-mode-free. Disclose to anti-cheat vendors pre-release for Madden 26 (EA's Easy Anti-Cheat does monitor USB peripherals). |

## Resource needs

- 1 backend engineer (FastAPI / Python) — full Phase 1.
- 1 ML/CV engineer (Tesseract / PyTorch / ONNX) — full Phase 1.
- 1 desktop engineer (Windows / OpenCV / PyInstaller) — M1 + M7 + M8 (split commitment).
- Tech lead for M7 + M8 + reviews.
- Hardware: dev PS5 with Madden 26 license, Elgato HD60 X capture card, CLX dev PC. (User has these.)
- Cloud: 1 new ECS service (small task, t3.medium), new ECR repo, Route53 entry for `vision.esportsforge.gg`.

## Out-of-scope follow-ups (Phase 1.1, post-launch)

- Defensive front + post-snap coverage classifier (Madden adapter v0.2, v0.3).
- `pc-monitor` capture source.
- Capture-agent auto-update.
- Frame-storage option behind a feature flag (for replay-debugging adapters).
- CFB 26 adapter (Phase 2).

## Approvals required before kickoff

1. **Architecture sign-off** — tech lead reviews Docs #00–#04, raises any objections to the open questions in Doc #02 §"Open architectural questions". Resolutions get amended into those docs.
2. **Resource allocation** — engineering manager confirms the 3-engineer staffing for the 12–14 day window.
3. **Hardware availability** — dev PS5, Madden license, capture card available for M1 + M7 + M8.
4. **Anti-cheat disclosure** — legal reviews the EA / Easy Anti-Cheat disclosure plan before M8 deploy.

After approval, kick off M1 + M2 + M3 in parallel (they have no cross-dependencies).
