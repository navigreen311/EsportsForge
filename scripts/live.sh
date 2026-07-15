#!/usr/bin/env bash
# live.sh — one-command live-vision dev stack (roadmap #1) + supervisor.
#
# Boots core :8100 + backend :8002 + frontend :3002, each with its env-exports,
# waits for health, prints "ready", then SUPERVISES them: if one exits
# unexpectedly it is restarted (port swept first so it rebinds cleanly). A
# service that crash-loops (dies fast, repeatedly) is given up on with a loud
# pointer to its log rather than spun forever. Ctrl-C stops everything.
#
#   bash scripts/live.sh          # (or: make live, if you have make)
#   bash scripts/live-setup.sh    # one-time: dev DB seed + .env.local (run this FIRST)
#
# The capture agent is NOT auto-started here (a lost feed can thrash the dshow
# driver). After READY, start it pin-free — see the READY banner / runbook §3.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGDIR="$ROOT/.live-logs"; mkdir -p "$LOGDIR"
VAF="$ROOT/services/visionaudioforge"; BE="$ROOT/backend"; FE="$ROOT/frontend"
VAF_PY="$VAF/.venv/Scripts/python.exe"; [ -f "$VAF_PY" ] || VAF_PY="$VAF/.venv/bin/python"
BE_PY="$BE/venv/Scripts/python.exe";   [ -f "$BE_PY" ]  || BE_PY="$BE/venv/bin/python"

SERVICES=(core backend frontend)
declare -A PORT=([core]=8100 [backend]=8002 [frontend]=3002)
declare -A PID START FLAPS GAVEUP

# Supervisor tuning.
POLL_SECS=3        # how often to check liveness
MIN_UPTIME=20      # a death sooner than this after (re)start counts as a "flap"
MAX_FLAPS=5        # give up on a service after this many consecutive flaps
RESTART_BACKOFF=2  # pause before a restart

shutting_down=0
_cleaned=0

free_port() {  # $1 = port — kill whatever holds it (incl. child trees)
  for pid in $(netstat -ano 2>/dev/null | grep -E ":$1 .*LISTENING" \
                 | grep -oE '[0-9]+$' | sort -u); do
    taskkill //F //PID "$pid" //T >/dev/null 2>&1 || kill "$pid" 2>/dev/null || true
  done
}

start_svc() {  # $1 = service name — (re)spawn it, record pid + start time
  local name="$1"
  case "$name" in
    core)
      # VAF_LOCAL_SESSION=true: /sessions/open returns ONE fixed id (get-or-create),
      # so every browser surface + the capture agent share a session, no pin (#2).
      ( cd "$VAF" && ESF_BACKEND_URL=http://127.0.0.1:8002 VAF_LOCAL_SESSION=true PYTHONPATH="$VAF" \
          "$VAF_PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8100 ) \
        >> "$LOGDIR/core.log" 2>&1 & PID[core]=$! ;;
    backend)
      ( cd "$BE" && VAF_DRILL_LAB_ENABLED=true VAF_CORE_URL=http://127.0.0.1:8100 PYTHONPATH="$BE" \
          "$BE_PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8002 ) \
        >> "$LOGDIR/backend.log" 2>&1 & PID[backend]=$! ;;
    frontend)
      ( cd "$FE" && npm run dev -- -p 3002 ) >> "$LOGDIR/frontend.log" 2>&1 & PID[frontend]=$! ;;
  esac
  START[$name]=$SECONDS
}

cleanup() {
  shutting_down=1
  [ "$_cleaned" = "1" ] && return
  _cleaned=1
  echo; echo "[live] stopping..."
  for name in "${SERVICES[@]}"; do kill "${PID[$name]:-}" 2>/dev/null || true; done
  # belt-and-braces: free the ports + any ffmpeg a capture agent left behind
  for name in "${SERVICES[@]}"; do free_port "${PORT[$name]}"; done
  taskkill //F //IM ffmpeg.exe >/dev/null 2>&1 || true
  echo "[live] stopped."
}
trap cleanup INT TERM EXIT

# --- preflight ---
[ -f "$VAF_PY" ] || { echo "[live] MISSING VAF venv ($VAF_PY) — see docs/runbooks."; exit 1; }
[ -f "$BE_PY" ]  || { echo "[live] MISSING backend venv ($BE_PY)."; exit 1; }
[ -f "$FE/.env.local" ] || { echo "[live] MISSING $FE/.env.local — run: bash scripts/live-setup.sh"; exit 1; }
if ! "$BE_PY" - "$BE/esportsforge.db" <<'PY' 2>/dev/null
import sqlite3, sys
try:
    c = sqlite3.connect(sys.argv[1])
    n = c.execute("select count(*) from users where email='dev@example.com'").fetchone()[0]
    sys.exit(0 if n >= 1 else 1)
except Exception:
    sys.exit(1)
PY
then
  echo "[live] dev DB not seeded (no dev@example.com). Run once:  bash scripts/live-setup.sh"; exit 1
fi

# --- boot the three services (background children of THIS shell) ---
for name in "${SERVICES[@]}"; do
  echo "[live] booting $name :${PORT[$name]} ..."
  start_svc "$name"
done

# --- wait for health ---
wait_up() {  # $1 url  $2 name
  for _ in $(seq 1 45); do
    curl -s -m2 -o /dev/null "$1" && { echo "[live]   $2 up"; return 0; }
    sleep 1
  done
  echo "[live]   $2 DID NOT COME UP — check $LOGDIR"; return 1
}
echo "[live] waiting for health (frontend can take ~20-40s to compile)..."
wait_up http://127.0.0.1:8100/docs "core :8100"
wait_up http://127.0.0.1:8002/api/v1/status "backend :8002"
wait_up http://127.0.0.1:3002 "frontend :3002"

cat <<EOF

[live] READY (supervised — a crashed service auto-restarts).
  Frontend : http://localhost:3002   (login  dev@example.com / devpass123)
  Backend  : http://127.0.0.1:8002       Core : http://127.0.0.1:8100
  Logs     : $LOGDIR/{core,backend,frontend}.log

  Capture agent (no pin needed — local single-session mode):
    cd agents/capture && VAF_LOCAL_SESSION=true VAF_CORE_URL=http://127.0.0.1:8100 \\
      "$VAF_PY" -m capture_agent.main --config ./config.capture-card.toml
  (start it only with the PS5 feed live — a lost feed can thrash the dshow driver.)

  Ctrl-C to stop everything.
EOF

# --- supervise: restart a service that exits unexpectedly, give up on crash-loops ---
while [ "$shutting_down" != "1" ]; do
  sleep "$POLL_SECS"
  [ "$shutting_down" = "1" ] && break
  for name in "${SERVICES[@]}"; do
    [ "${GAVEUP[$name]:-0}" = "1" ] && continue
    if ! kill -0 "${PID[$name]:-}" 2>/dev/null; then
      uptime=$(( SECONDS - ${START[$name]:-0} ))
      if [ "$uptime" -lt "$MIN_UPTIME" ]; then
        FLAPS[$name]=$(( ${FLAPS[$name]:-0} + 1 ))
      else
        FLAPS[$name]=1   # was healthy for a while — treat this as a fresh incident
      fi
      if [ "${FLAPS[$name]}" -gt "$MAX_FLAPS" ]; then
        GAVEUP[$name]=1
        echo "[live] ⚠  $name crash-looped (${FLAPS[$name]} quick deaths) — giving up. See $LOGDIR/$name.log"
        continue
      fi
      echo "[live] ⚠  $name exited (up ${uptime}s) — restarting (#${FLAPS[$name]}) in ${RESTART_BACKOFF}s..."
      sleep "$RESTART_BACKOFF"
      [ "$shutting_down" = "1" ] && break
      free_port "${PORT[$name]}"       # clear a lingering child tree so it rebinds
      start_svc "$name"
      echo "[live]   $name restarted (pid ${PID[$name]})"
    fi
  done
  # all three abandoned → nothing left to supervise
  if [ "${GAVEUP[core]:-0}" = "1" ] && [ "${GAVEUP[backend]:-0}" = "1" ] \
     && [ "${GAVEUP[frontend]:-0}" = "1" ]; then
    echo "[live] all services gave up — exiting."; exit 1
  fi
done
