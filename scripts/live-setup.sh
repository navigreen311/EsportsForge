#!/usr/bin/env bash
# live-setup.sh — one-time setup for the live-vision stack (roadmap #1).
# Fresh dev DB + seed (dev@example.com / devpass123) and a sane frontend/.env.local.
# Idempotent: safe to re-run. Then:  bash scripts/live.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BE="$ROOT/backend"; FE="$ROOT/frontend"
BE_PY="$BE/venv/Scripts/python.exe"; [ -f "$BE_PY" ] || BE_PY="$BE/venv/bin/python"
[ -f "$BE_PY" ] || { echo "[live-setup] MISSING backend venv ($BE_PY)."; exit 1; }

# --- dev DB: seed if the dev user is missing (covers empty / drifted / absent DB) ---
if "$BE_PY" - "$BE/esportsforge.db" <<'PY' 2>/dev/null
import sqlite3, sys
try:
    c = sqlite3.connect(sys.argv[1])
    n = c.execute("select count(*) from users where email='dev@example.com'").fetchone()[0]
    sys.exit(0 if n >= 1 else 1)
except Exception:
    sys.exit(1)
PY
then
  echo "[live-setup] dev DB already seeded (dev@example.com) — skipping."
else
  echo "[live-setup] seeding dev DB (fresh alembic + dev user)..."
  if [ -f "$BE/esportsforge.db" ]; then
    mv "$BE/esportsforge.db" "$BE/esportsforge.db.bak-$(date +%s)"   # preserve any drifted DB
  fi
  ( cd "$BE" && "$BE_PY" -m alembic upgrade head && "$BE_PY" scripts/seed_dev_user.py )
  echo "[live-setup]   -> login: dev@example.com / devpass123"
fi

# --- frontend/.env.local: create if absent, else sanity-check ---
ENVF="$FE/.env.local"
if [ ! -f "$ENVF" ]; then
  echo "[live-setup] writing $ENVF"
  cat > "$ENVF" <<'EOF'
NEXTAUTH_SECRET=dev-nextauth-secret-not-for-production-67890
NEXTAUTH_URL=http://localhost:3002
NEXT_PUBLIC_API_URL=http://127.0.0.1:8002
NEXT_PUBLIC_VOICEFORGE_ENABLED=true
NEXT_PUBLIC_VISIONAUDIOFORGE_ENABLED=true
NEXT_PUBLIC_VAF_DRILL_LAB_ENABLED=true
NEXT_PUBLIC_VAF_SIMLAB_ENABLED=true
NEXT_PUBLIC_VAF_GAMEPLAN_ENABLED=true
NEXT_PUBLIC_VAF_ARSENAL_ENABLED=true
NEXT_PUBLIC_VAF_WAR_ROOM_ENABLED=true
NEXT_PUBLIC_VAF_WS_URL=ws://127.0.0.1:8100
EOF
else
  echo "[live-setup] $ENVF exists — sanity-checking..."
  grep -q "NEXT_PUBLIC_API_URL=http://127.0.0.1:8002" "$ENVF" \
    || echo "  ⚠  NEXT_PUBLIC_API_URL should be http://127.0.0.1:8002 (the dead :8001 landmine)."
  for f in DRILL_LAB SIMLAB GAMEPLAN ARSENAL WAR_ROOM; do
    grep -q "NEXT_PUBLIC_VAF_${f}_ENABLED=true" "$ENVF" \
      || echo "  ⚠  NEXT_PUBLIC_VAF_${f}_ENABLED is not =true (that surface's live vision stays off)."
  done
fi

echo "[live-setup] done. Now:  bash scripts/live.sh"
