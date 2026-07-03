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

## Rollback via master flag (~30 s)

**Fastest kill:** set backend `VAF_DRILL_LAB_ENABLED` to anything other than `"true"` (or unset) and **restart the backend** (~30 s). The broker immediately **403s** new `sessions/start` calls → no new vision sessions. Drill state is unaffected (rep counter is server-side; per state report §2.5, the mock/legacy path remains available).

- The frontend build-time flag can be left as-is during an incident — the backend master is sufficient to stop the live path. Flip the frontend flag off on the next deploy if the rollback is durable.
- Audit trail of flips: git blame on the deployment config (ADR 0001).

## Deferred / pending

- **P2 — CloudWatch webhook-failure alarm (ADR 0003): PENDING / NOT WIRED.** Only the **manual** master-flag rollback above exists today; there is **no automated auto-rollback** on webhook-failure yet. Wiring this alarm is the P2 follow-up before widening.
- **Widening flag (`VAF_DRILL_LAB_COHORT`) + per-user infra (`vaf_pipeline_enabled_for`) — DEFERRED** (ADR 0012 two-stage). Phase 1a is solo (`allowlist=[founder]`); per-user targeting lands when widening past the founder. Not built.
