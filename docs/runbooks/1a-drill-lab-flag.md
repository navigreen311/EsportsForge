# Runbook — Drill Lab Live-Vision Flag

- **Scope:** how to enable/disable and roll back the Drill Lab live-vision cutover (Phase 1a).
- **Model:** env-var feature flag, **engineer-flipped via deployment config + restart — no in-app flip** (ADR 0001). The in-app Settings → Game Settings shows a **read-only** status of this flag; it is not a control.
- **Related:** [ADR 0001](../adr/0001-feature-flag-infrastructure.md) (env-flag model), [ADR 0012](../adr/0012-two-stage-flag-pattern.md) (two-stage: master + widening), [ADR 0003](../adr/0003-webhook-delivery-durability-v1.md) (rollback / webhook alarm).

## Flags

| Flag | Where | Read | Purpose |
|---|---|---|---|
| `VAF_DRILL_LAB_ENABLED` | **Backend** process env (`os.environ`, read per-request by the broker `POST /api/v1/visionaudio/sessions/start`) | runtime, per request | **Server-side master kill-switch.** When not `"true"`, the broker returns **403** → no new vision sessions provisioned. |
| `NEXT_PUBLIC_VAF_DRILL_LAB_ENABLED` | **Frontend** build-time env (Next inlines `NEXT_PUBLIC_*` at build) | build time | Frontend opt-in — gates whether the Drill Lab page attempts to provision + connect. Read via `frontend/src/lib/vafFlags.ts` (`drillLabVisionEnabled()`), the single source the page enforces and Settings displays. |

Both must be `"true"` for the live path to run end-to-end (frontend attempts; backend permits). The **backend flag is authoritative** — with it off, the frontend flag has no effect (broker 403s).

**Webhook routing is global, not per-session.** Core delivers events through a single publisher targeting its own `ESF_BACKEND_URL` (`services/visionaudioforge/app/core/webhook.py`) — the broker does **not** pass a per-session `webhook_url` (that param was ignored and was removed, Finding 1). For core events to reach *this* backend, **align core's `ESF_BACKEND_URL` to this backend's URL** (e.g. `http://127.0.0.1:8003` in local dev).

## Enable (engineer)

1. **Backend:** set `VAF_DRILL_LAB_ENABLED=true` in the backend's environment; **restart** the backend process/ECS task.
2. **Frontend:** set `NEXT_PUBLIC_VAF_DRILL_LAB_ENABLED=true` at build; **rebuild + redeploy** the frontend (build-time inline — a running frontend will not pick it up without a rebuild).
3. Verify: Settings → Game Settings shows **Drill Lab Live Vision: On**; the Drill Lab page provisions a session.

## Run it live — full local recipe (verified end-to-end 2026-07-13, PS5 → browser)

This is the concrete "how to run the whole thing off a real PS5 locally" recipe. Verified: driving a play-call rep on the PS5 auto-completed a Drill Lab rep in the browser (`FORMATION_LOCKED` → `useDrillLabAutoRep`), with `COVERAGE_LOCKED` + `SNAPSHOT` also flowing.

**Dev-path caveat:** this uses `next dev` (unbundled), **not** a production build. `NEXT_PUBLIC_*` still inlines at dev-server start, so a running dev server must be **restarted** (not just HMR) to pick up an `.env.local` change. Dev mode exercises the exact browser event-flow (broker → core WS → hook → render); the dev-vs-prod distinction is about bundling/inlining, not whether events reach the UI. For a prod bundle, rebuild + redeploy per "Enable (engineer)" above.

### Topology / ports (local)

| Component | Port | Run dir | Runtime |
|---|---|---|---|
| VAF core | 8100 | `services/visionaudioforge` | `.venv` (Py 3.12, cv2+easyocr+torch) |
| Backend (broker + webhook receiver) | **8002** | `backend` | `venv` |
| Frontend (`next dev`) | 3002 | `frontend` | node (matches `NEXTAUTH_URL`) |
| Capture agent (capture-card) | — | `agents/capture` | VAF `.venv` (has cv2 + websockets) |

Backend is **8002**, not 8001 (ADR 0011 — a ghost PID holds 8001). The old `NEXT_PUBLIC_API_URL=http://127.0.0.1:8001` in `.env.local` was **stale and dead** and 502'd every `sessions/start`; it must be `:8002`.

### Env — shell-export for services, `.env.local` for the frontend

The backend/core do **not** `load_dotenv` these — they must be **shell-exported in the process that launches the service** (per [[feedback_esportsforge_dev_setup]]):

- **Backend:** `VAF_DRILL_LAB_ENABLED=true` (master gate) **and** `VAF_CORE_URL=http://127.0.0.1:8100` (broker → core).
- **Core:** `ESF_BACKEND_URL=http://127.0.0.1:8002` (webhook publisher → this backend; global, not per-session).

Frontend `frontend/.env.local` (build/dev-server-time; restart the dev server after editing):
```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8002        # fixed from dead :8001 (ADR 0011)
NEXT_PUBLIC_VAF_DRILL_LAB_ENABLED=true           # frontend opt-in
NEXT_PUBLIC_VAF_WS_URL=ws://127.0.0.1:8100        # fallback only — the broker returns ws_url; a valid ws:// keeps new WebSocket() from throwing on empty
```

### 0. Backend DB (one-time, if schema-drifted)

A checkout can carry a **schema-drifted `backend/esportsforge.db`** (pre-rebaseline: unstamped `alembic_version`, fewer tables than main's `ffa2cd90434a` "clean baseline") — the startup `alembic upgrade head` then dies on `CREATE TABLE` collisions (exit 3). Fix: move the drifted DB aside, build fresh, seed the dev user.
```
cd backend
mv esportsforge.db esportsforge.db.drifted-bak      # preserve, don't delete
venv/Scripts/python.exe -m alembic upgrade head       # builds 32 tables + head stamp
venv/Scripts/python.exe scripts/seed_dev_user.py      # -> dev@example.com / devpass123
```

### 1. Boot the three services (each in its own shell/bg)
```
# core (:8100)
cd services/visionaudioforge
ESF_BACKEND_URL=http://127.0.0.1:8002 PYTHONPATH="$PWD" \
  .venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8100

# backend (:8002)
cd backend
VAF_DRILL_LAB_ENABLED=true VAF_CORE_URL=http://127.0.0.1:8100 PYTHONPATH="$PWD" \
  venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002

# frontend (:3002 to match NEXTAUTH_URL)
cd frontend && npm run dev -- -p 3002
```
Health: `curl :8100/docs`, `curl :8002/api/v1/status`, `curl :3002` → all 200.

Optional backend-leg smoke (no browser): login → `sessions/start` should broker to core and return `{session_id, ws_url}`:
```
TOK=$(curl -s -XPOST :8002/api/v1/auth/login -H 'Content-Type: application/json' -d '{"email":"dev@example.com","password":"devpass123"}' | jq -r .access_token)
curl -s -XPOST :8002/api/v1/visionaudio/sessions/start -H "Authorization: Bearer $TOK"
```

### 2. Browser: log in + open Drill Lab
Open `http://localhost:3002`, log in (`dev@example.com` / `devpass123`), navigate to **Drill Lab**. With the flag on, the page POSTs `sessions/start`, gets `{session_id, token, ws_url}`, and opens a WS to core `/ws/events/{session_id}`.

### 3. Launch the capture agent

**Solo local dev (recommended — no pin): local single-session mode.** With
`VAF_LOCAL_SESSION=true`, core's `/sessions/open` returns ONE fixed id
(`ses_localdev`) via get-or-create, so every browser surface **and** the capture
agent auto-share the same session — no scraping, no `--session-id`. `bash
scripts/live.sh` already boots core with this flag on; just run the agent with it
too (it opens-or-gets the fixed session on core itself, so the browser order
doesn't matter). Preflight the card first (brightness ~16 = black/no-signal;
30–90 = live game):
```
cd agents/capture
VAF_LOCAL_SESSION=true VAF_CORE_URL=http://127.0.0.1:8100 \
  <vaf-venv-python> -m capture_agent.main --config ./config.capture-card.toml
```

**Manual pin (multi-user / when local mode is OFF).** Ingest
(`/ws/ingest?session_id=X`) and events (`/ws/events/{session_id}`) are keyed by
the **same** `session_id`, and outside local mode the browser mints a **fresh**
session each load. So the agent must ingest into *that* session — scrape it from
the core log (the WS accept line carries it in the path) and pass `--session-id`:
```
grep -aE "WebSocket /ws/events" core.log | tail -1
#   ... "WebSocket /ws/events/ses_XXXX?token=esf-cap-dev-placeholder" [accepted]

cd agents/capture
<vaf-venv-python> -m capture_agent.main --config ./config.capture-card.toml --session-id ses_XXXX
```
Agent log should show `hdmi_ffmpeg_spawned` → `session_open` → `agent_connected`; core shows `agent_connected` → `title_locked`.

### 4. Verify the render
Drive a play to the **offensive/defensive play-call screen** → `FORMATION_LOCKED` fires → **a Drill Lab rep auto-completes**. Independent check: `curl :8002/api/v1/visionaudio/sessions/active` shows `recent_event_count` climbing; or subscribe a raw WS client to `/ws/events/{session_id}` to watch events directly. First events can lag ~60–90 s after connect (getting to a live play + EasyOCR warm).

### Known gotchas found during the first live run
- **Dead `:8001` in `.env.local`** — see above; must be `:8002`.
- **Schema-drifted dev DB** — see step 0.
- **File-source EOF heartbeat bug (latent):** `FilePlaybackSource` emits a heartbeat with `status="completed"` at clip EOF, which `HeartbeatMessage` (`ingest.py`) rejects (`literal_error`, only `ok|missing|degraded`) → an `ingest_error` at end-of-clip. Harmless for the live capture-card path (no EOF), but breaks clean shutdown of **file-mode** replays; fix the enum or map `completed`→`ok` before relying on file-mode tallying.

## Rollback via master flag (~30 s)

**Fastest kill:** set backend `VAF_DRILL_LAB_ENABLED` to anything other than `"true"` (or unset) and **restart the backend** (~30 s). The broker immediately **403s** new `sessions/start` calls → no new vision sessions. Drill state is unaffected (rep counter is server-side; per state report §2.5, the mock/legacy path remains available).

- The frontend build-time flag can be left as-is during an incident — the backend master is sufficient to stop the live path. Flip the frontend flag off on the next deploy if the rollback is durable.
- Audit trail of flips: git blame on the deployment config (ADR 0001).

## Deferred / pending

- **P2 — CloudWatch webhook-failure alarm (ADR 0003): PENDING / NOT WIRED.** Only the **manual** master-flag rollback above exists today; there is **no automated auto-rollback** on webhook-failure yet. Wiring this alarm is the P2 follow-up before widening.
- **Widening flag (`VAF_DRILL_LAB_COHORT`) + per-user infra (`vaf_pipeline_enabled_for`) — DEFERRED** (ADR 0012 two-stage). Phase 1a is solo (`allowlist=[founder]`); per-user targeting lands when widening past the founder. Not built.
