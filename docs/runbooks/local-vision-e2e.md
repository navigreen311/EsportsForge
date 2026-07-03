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

Use a **throwaway `DATABASE_URL`** (above) rather than the default `esportsforge.db`. That default is **schema-drifted** — the `recommendations.feedback_at` column that first surfaced this is only the symptom.

**Full audit (Session #11): [../db-migration-drift-audit.md](../db-migration-drift-audit.md).** In short, alembic was effectively abandoned — **two heads** (`df_` + `rec_`, no merge), **no `alembic.ini`**, only **18 of 50 model tables** migrated, and the dev DB is **`create_all`-built / never stamped**.

- **`alembic upgrade head` is NOT the fix** — a throwaway-copy test failed with *"Multiple head revisions are present"*, and even resolving that, an upgrade-from-base would collide with the already-existing `create_all` tables. Do **not** run alembic against the real DB.
- **Interim:** `create_all` works for dev/test — keep using it; use a throwaway DB for any migration experiments.
- **Fix = a scoped remediation project** (add `alembic.ini` → merge heads → autogenerate the 32 missing tables → `stamp` existing DBs → switch lifespan to `alembic upgrade`), deliberately all-or-nothing. See the audit doc.
