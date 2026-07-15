#!/usr/bin/env bash
# live.sh — one-command live-vision dev stack (roadmap #1).
#
# Boots core :8100 + backend :8002 + frontend :3002, each with its env-exports,
# waits for health, prints "ready", and stays in the foreground so the services
# (its background children) keep running. Ctrl-C stops all three.
#
#   bash scripts/live.sh          # (or: make live, if you have make)
#   bash scripts/live-setup.sh    # one-time: dev DB seed + .env.local (run this FIRST)
#
# The capture agent is NOT auto-started here — it still needs the browser's
# session id (roadmap #2 removes that). After READY, follow
# docs/runbooks/1a-drill-lab-flag.md §3 to pin + launch it.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGDIR="$ROOT/.live-logs"; mkdir -p "$LOGDIR"
VAF="$ROOT/services/visionaudioforge"; BE="$ROOT/backend"; FE="$ROOT/frontend"
VAF_PY="$VAF/.venv/Scripts/python.exe"; [ -f "$VAF_PY" ] || VAF_PY="$VAF/.venv/bin/python"
BE_PY="$BE/venv/Scripts/python.exe";   [ -f "$BE_PY" ]  || BE_PY="$BE/venv/bin/python"

pids=()
cleanup() {
  echo; echo "[live] stopping..."
  for p in "${pids[@]:-}"; do kill "$p" 2>/dev/null || true; done
  # belt-and-braces: free the ports + any ffmpeg a capture agent left behind
  for port in 8100 8002 3002; do
    for pid in $(netstat -ano 2>/dev/null | grep -E ":$port .*LISTENING" \
                   | grep -oE '[0-9]+$' | sort -u); do
      taskkill //F //PID "$pid" //T >/dev/null 2>&1 || kill "$pid" 2>/dev/null || true
    done
  done
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
echo "[live] booting core :8100 ..."
( cd "$VAF" && ESF_BACKEND_URL=http://127.0.0.1:8002 PYTHONPATH="$VAF" \
    "$VAF_PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8100 ) \
  > "$LOGDIR/core.log" 2>&1 & pids+=($!)
echo "[live] booting backend :8002 ..."
( cd "$BE" && VAF_DRILL_LAB_ENABLED=true VAF_CORE_URL=http://127.0.0.1:8100 PYTHONPATH="$BE" \
    "$BE_PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8002 ) \
  > "$LOGDIR/backend.log" 2>&1 & pids+=($!)
echo "[live] booting frontend :3002 ..."
( cd "$FE" && npm run dev -- -p 3002 ) > "$LOGDIR/frontend.log" 2>&1 & pids+=($!)

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

[live] READY.
  Frontend : http://localhost:3002   (login  dev@example.com / devpass123)
  Backend  : http://127.0.0.1:8002       Core : http://127.0.0.1:8100
  Logs     : $LOGDIR/{core,backend,frontend}.log

  Next (until roadmap #2 auto session-coord ships): pin the capture agent —
  open a page, then follow docs/runbooks/1a-drill-lab-flag.md §3.

  Ctrl-C to stop everything.
EOF

wait
