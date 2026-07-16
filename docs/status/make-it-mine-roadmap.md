# "Make it actually mine" — solo-usability roadmap

The vision spine is **feature-complete and live-verified** (`v0.3.0-phase1c-complete`). Running it
solo *used* to be an expert operation: ~4 terminals + env-exports, a fiddly capture-agent-to-browser
**session pin** (grep the core log, copy a ULID), Arsenal effectively off (no LLM key), and no
service supervisor. This roadmap turned "an engine I own" into "boot it and play."

**✅ All three follow-ups are DONE.** Solo run is now — **in Git Bash (NOT PowerShell/cmd; in
PowerShell `bash` hits WSL and dies), from the repo root** `cd /c/Users/ivann/Projects/EsportsForge`:
`bash scripts/live-setup.sh` (once) → `bash scripts/live.sh` → open any page → (feed live) start the
pin-free capture agent **in its own PowerShell window** (§3 of the runbook — that command is
PowerShell syntax) → play Madden. Full shell/cwd detail: `docs/runbooks/1a-drill-lab-flag.md` §0.
(`make live` also works *if* you have `make` — it isn't installed on the dev box, so the scripts are
the primary interface.)

Sequence delivered: **#1 → #3 → #2** (quick ergonomics wins first; the big architectural
friction-killer last, with a clean home to slot into).

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

## #2 — Auto session-coordination  *(~1–2 sessions, medium risk — the big one)* — ✅ DONE (this PR)

**Gap:** the browser mints a fresh `ses_{ULID}` per page load; the capture agent must be pinned
to *that* id — today via grep-the-log. This is the #1 friction, and it's why multiple surfaces
don't share events.
**Build (DONE):** a **local single-session mode**, env-gated `VAF_LOCAL_SESSION=true`. It landed in
just **2 places, not 3** — the broker (`backend/.../visionaudio_phase0.py`) is a pure pass-through
of core's id, so it needed **zero** changes:
- **Core** (`services/visionaudioforge/app/api/sessions.py` + `app/core/session.py`): when the flag
  is on, `/sessions/open` returns ONE fixed id (`ses_localdev`, override via `VAF_LOCAL_SESSION_ID`)
  through a new `registry.open_or_get` (get-or-create — repeated opens don't wipe an in-flight
  session's `adapter_state`/`frame_history`). Flag off → the real fresh-`ses_{ULID}`-per-open path
  is byte-for-byte untouched (regression-tested).
- **Capture agent** (`agents/capture/capture_agent/main.py`): `--session-id` is now optional; with
  the flag set it opens-or-gets the fixed session on core itself (stdlib `urllib`, no new dep), so
  it's **order-independent** — no browser-first requirement, no pin.
- Core is the **single authority** on the id, so browser + agent converge with no coordination.
  `scripts/live.sh` boots core with the flag on and prints the pin-free agent command.
**Verified:** 5 new core tests (idempotent get-or-create, flag helpers, fixed-id-twice, real-path
regression) + a live smoke — two browser opens **and** the agent resolver all returned
`ses_localdev`. **Every surface + the agent now auto-share one session.**
**Not folded in:** capture-agent **auto-start** in `live.sh` — deliberately left manual. A lost feed
can thrash the dshow driver into a lockup (known limit below), so the agent should start only with
the PS5 feed live. The pin friction — the actual ask — is gone.
**Risk (realized):** low-medium — strictly behind the flag; the multi-user path has a regression test.

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

## Robustness track (separate from ignition)

- **Capture-card driver lockup** on a bad feed → **mitigated (2026-07-15).** The agent used to
  respawn ffmpeg every ≤5 s forever on a gone/busy device, and that open/close churn is what
  wedged the dshow driver. `hdmi_capture.py` now distinguishes a **mid-stream drop** (frames were
  flowing → fast 0.5 s retry, signal usually returns) from a **failed open** (ffmpeg died before a
  frame → device gone); consecutive failed opens escalate the backoff through tiers (0.5→1→2 s,
  then 5 s, then a **30 s cooldown**) and log a one-shot "re-plug the card" prompt, so a prolonged
  outage pokes dshow ≤ once/30 s and auto-recovers (`hdmi_recovered`) on re-plug. It doesn't
  *prevent* a hardware wedge, but it removes the churn that caused most of them. Covered by 4 new
  hardware-free unit tests.
- **No service supervisor** → **done (2026-07-15).** `scripts/live.sh` now supervises the three
  services: after READY it polls liveness and **restarts any that exits** (sweeping its port first
  so it rebinds cleanly). A service that **crash-loops** — dies within 20 s of start, `MAX_FLAPS`
  times running — is *given up on* with a loud pointer to its log instead of spun forever; a
  service that was healthy for a while and then dies is treated as a fresh incident (flap counter
  resets). `Ctrl-C` still tears everything down via the same trap. Smoke-tested: killing core
  mid-run auto-restarted it on a new pid; SIGTERM freed all three ports.

**Achieved (#1+#3+#2 all shipped; robustness track cleared):** solo run = `bash scripts/live.sh`
→ open any page → (feed live) start the pin-free agent → play. No terminal-juggling, no session
pin, Arsenal live, a crashed service auto-restarts, and the capture agent rides out a lost feed
without wedging the card. What's left is genuinely optional (capture-agent auto-start, log
rotation) — not ignition.
