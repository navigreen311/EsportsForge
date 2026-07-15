# "Make it actually mine" — solo-usability roadmap

The vision spine is **feature-complete and live-verified** (`v0.3.0-phase1c-complete`), but
running it solo today is an expert operation: ~4 terminals + env-exports, a fiddly
capture-agent-to-browser **session pin** (grep the core log, copy a ULID), Arsenal effectively
off (no LLM key), and no service supervisor. This roadmap turns "an engine I own" into
"boot it and play." Three follow-ups; **the goal is:** `bash scripts/live.sh` → open a page →
play Madden. (`make live` also works *if* you have `make` — it isn't installed on the dev box,
so the scripts are the primary interface.)

Sequence: **#1 → #3 → #2** (quick ergonomics wins first; the big architectural friction-killer
last, with a clean home to slot into).

## #1 — One-command launcher  *(~1 session, low risk)* — ✅ DONE (this PR)

**Gap:** No full-stack launcher. `make dev-start` is stale (old single backend on `:8000`, no
core service, no env-exports, no flags). You boot 4 things by hand.
**Build (DONE):** `scripts/live.sh` (`bash scripts/live.sh`; `make live` too): boots core `:8100`
/ backend `:8002` / frontend `:3002`, each with its env-exports (`ESF_BACKEND_URL`,
`VAF_DRILL_LAB_ENABLED`, `VAF_CORE_URL`), waits for health on each, prints "ready" + the URLs;
`Ctrl-C` (or `bash`-kill the ports via `make live-stop`) tears them down (ports + ffmpeg).
`scripts/live-setup.sh` does the one-time dev-DB fresh+seed + `.env.local` sanity (idempotent).
The capture agent is NOT auto-started here — it still needs the session pin until #2 lands; the
launcher prints the runbook §3 hint. Smoke-tested: all three boot to READY, `Ctrl-C` cleans up.
**Risk:** low — automates the documented runbook. Windows/Git-Bash quoting + reliable
backgrounding are the only fiddly parts (the script stays foreground and `wait`s so children
persist; `Ctrl-C` cleans up).

## #2 — Auto session-coordination  *(~1–2 sessions, medium risk — the big one)*

**Gap:** the browser mints a fresh `ses_{ULID}` per page load (`services/visionaudioforge/app/
api/sessions.py`); the capture agent must be pinned to *that* id — today via grep-the-log. This
is the #1 friction, and it's why multiple surfaces don't share events.
**Build:** a **local single-session mode** (env-gated, e.g. `VAF_LOCAL_SESSION=true`): the broker
(`backend/.../visionaudio_phase0.py:start_session`) returns a **fixed** session id instead of a
fresh ULID; core `open_session` becomes get-or-create for that id; the capture agent config
defaults to the same id. Then **every surface + the capture agent auto-share one session** — no
scraping, no pin — and it fixes the multi-surface problem (War Room + Arsenal + Drill Lab light
up together) for free. Fold the capture-agent auto-start into `make live`.
**Risk:** medium — touches the session model in 3 places (broker, core registry, capture config).
Must stay strictly behind the local flag so the real multi-user session path is untouched.

## #3 — Arsenal live-triggering  *(~½ session, low risk)* — ✅ DONE (this PR)

**Gap:** two small things — (a) `backend/app/services/arsenal_ai.py` needs
`settings.anthropic_api_key`; with none set the endpoint 503s ("ANTHROPIC_API_KEY not
configured"), so no weapon recommendation; (b) the trigger surface (`ArsenalAlert` via
`CompetitionModeCard`) already mounts on **dashboard / gameplan / war-room**, but NOT the Arsenal
*library* page.
**Build (DONE):** (a) the key was *already* wired — `config.py` has an `anthropic_api_key`
settings field that pydantic loads from `backend/.env` **or** the shell env, so no code was
needed; instead `scripts/live-setup.sh` now **detects** whether a key is reachable and, if not,
prints exactly how the owner adds their own (`echo 'ANTHROPIC_API_KEY=sk-ant-...' >> backend/.env`)
— the key is never written by the script. (b) `ArsenalAlert` is now mounted on the Arsenal
library page (`app/(dashboard)/arsenal/page.tsx`); it self-provisions a vision session via
`useArsenalAI` and renders null until a weapon fires, so it's inert without a live feed / key.
**Graceful degrade verified (no key):** service `call_claude()` returns `""`, the router 503s,
`useArsenalAI.poll()` swallows the error, `visible` stays false → the alert renders null. No
crash, no empty banner — Arsenal still detects coverages, it just can't recommend a weapon.
The 1c.3 wiring already fires the trigger on a live coverage — it just needs a key to answer.
**Risk:** low — one-line mount + a setup-script warning; the secret stays the owner's.

## Not on this list (separate robustness track)

- **Capture-card driver lockup** on a bad feed → currently needs a physical USB re-plug (the
  agent's restart-on-open-failure churns the dshow driver). Real, but it's "recover from a
  crash," not "start it solo."
- **No service supervisor** — a dead core/backend/frontend stays dead. A `make live` foreground
  supervisor (restart on exit) would help, but is polish, not the ignition key.

**After #1+#3+#2:** solo run = `bash scripts/live.sh` → open any page → play. No terminal-juggling, no
session pin, Arsenal live.
