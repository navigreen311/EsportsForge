# Runbook — Local Drill Lab Live-Path E2E

How to stand up the full browser → core live path locally and drive a real
`FORMATION_LOCKED` through it. Companion to [1a-drill-lab-flag.md](1a-drill-lab-flag.md).

## Processes / ports / env

| Process | Command (from repo root) | Port | Key env |
|---|---|---|---|
| VAF core | `<vaf-venv> -m uvicorn app.main:app --port 8100` (cwd `services/visionaudioforge`) | 8100 | `ESF_BACKEND_URL=http://127.0.0.1:8003` (so core's global webhook publisher targets *our* backend — routing is global, not per-session) |
| Backend | `<backend-venv> -m uvicorn app.main:app --port 8003` (cwd `backend`) | 8003 | `VAF_CORE_URL=http://127.0.0.1:8100`, `VAF_DRILL_LAB_ENABLED=true`, `DATABASE_URL=sqlite+aiosqlite:///./e2e_dev.db` |
| Frontend | `npm run dev` (cwd `frontend`) | 3000 | `NEXT_PUBLIC_API_URL=http://127.0.0.1:8003`, `NEXT_PUBLIC_VAF_WS_URL=ws://127.0.0.1:8100`, `NEXT_PUBLIC_VAF_DRILL_LAB_ENABLED=true` |

**Port alignment matters:** the frontend must point at the backend running *this* repo's broker (`:8003` here), and core's `ESF_BACKEND_URL` must point back at that same backend, or the webhook lands on the wrong process.

## Seed a dev user + log in

```bash
cd backend
DATABASE_URL="sqlite+aiosqlite:///./e2e_dev.db" .venv/Scripts/python.exe scripts/seed_dev_user.py
```
Prints `dev@example.com` / `devpass123`. Log in with those in the browser.

> **GOTCHA:** the login endpoint uses pydantic `EmailStr`, which **rejects domains without a dot** (`dev@local` → 422). The seed uses `dev@example.com`. If you hand-create a user, give it an RFC-valid email.

## Drive a clip through the live path

1. Open `http://localhost:3000/drills` (flag on) → the page brokers a session; the "Vision:" line shows `connected · ses_…`. Copy that `ses_…`.
2. Drive an **overlay** clip against that session (broadcast reads null by design):
   ```bash
   VAF_CORE_URL=http://127.0.0.1:8100 \
   ESF_OVERLAY_CLIP=<abs path>/madden26_playcall_shotgun_trips.mp4 \
   ESF_SESSION_ID=<the ses_… from the page> \
   <vaf-venv> agents/capture/e2e_live_path.py
   ```
3. Expect in the browser: "Vision: · Trips" + the rep counter +1.

## Known limitation — dev DB schema drift (tracked, deferred)

Use a **throwaway `DATABASE_URL`** (above) rather than the default `esportsforge.db`. That default is **schema-drifted** — its `recommendations` table lacks `feedback_at`.

- **Root cause (benign):** dev builds/maintains the DB via `Base.metadata.create_all` (the app lifespan), **not `alembic upgrade`**. `create_all` only creates *missing tables*; it never ALTERs existing ones. The migration that adds the column (`rec_20260505_0001_add_recommendation_feedback`) **exists and is coherent with the model** — it was simply never applied to that long-lived file.
- **Fix (deferred, do NOT run here):** `alembic upgrade head` against the DB, or recreate it.
- **Broader signal (deferred):** the dev create_all-vs-alembic split means long-lived dev DBs drift over time. A **full migrations↔models coherence audit across all tables** is separately deferred (the Alembic investigation).
