#!/usr/bin/env bash
# =============================================================================
# EsportsForge — Local Development Setup
# Usage: bash scripts/dev-setup.sh
# =============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }

# ---------------------------------------------------------------------------
# 1. Check prerequisites
# ---------------------------------------------------------------------------
info "Checking prerequisites..."

command -v node   >/dev/null 2>&1 || fail "Node.js is not installed. Install v20+ from https://nodejs.org"
command -v python >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1 || fail "Python is not installed. Install v3.12+ from https://python.org"
command -v docker >/dev/null 2>&1 || fail "Docker is not installed. Install from https://docker.com"
command -v docker compose >/dev/null 2>&1 && COMPOSE="docker compose" || {
  command -v docker-compose >/dev/null 2>&1 && COMPOSE="docker-compose" || fail "docker compose is not available"
}

NODE_VER=$(node --version | cut -d. -f1 | tr -d 'v')
if [ "$NODE_VER" -lt 18 ]; then
  fail "Node.js v18+ required, found $(node --version)"
fi

PYTHON_CMD=$(command -v python3 || command -v python)
PYTHON_VER=$($PYTHON_CMD --version 2>&1 | awk '{print $2}' | cut -d. -f1-2)
info "Found Node $(node --version), Python $PYTHON_VER, Docker $(docker --version | awk '{print $3}')"

# ---------------------------------------------------------------------------
# 2. Environment file
# ---------------------------------------------------------------------------
if [ ! -f .env ]; then
  info "Copying .env.example -> .env"
  cp .env.example .env
  warn "Edit .env to fill in real API keys before running the app."
else
  info ".env already exists, skipping copy."
fi

# ---------------------------------------------------------------------------
# 3. Start infrastructure containers
# ---------------------------------------------------------------------------
info "Starting PostgreSQL and Redis via docker compose..."
$COMPOSE up -d postgres redis

# Wait for postgres to be ready
info "Waiting for PostgreSQL to accept connections..."
for i in $(seq 1 30); do
  if $COMPOSE exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
    break
  fi
  if [ "$i" -eq 30 ]; then
    fail "PostgreSQL did not become ready in time"
  fi
  sleep 1
done
info "PostgreSQL is ready."

# ---------------------------------------------------------------------------
# 4. Backend setup
# ---------------------------------------------------------------------------
info "Installing backend Python dependencies..."
cd backend

if [ ! -d "venv" ]; then
  $PYTHON_CMD -m venv venv
fi

# Activate venv
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
  source venv/Scripts/activate
fi

pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install flake8 mypy -q

# ---------------------------------------------------------------------------
# 5. Run database migrations
# ---------------------------------------------------------------------------
if [ -d "alembic" ]; then
  info "Running Alembic database migrations..."
  alembic upgrade head
else
  warn "No alembic/ directory found. Skipping migrations."
fi

cd ..

# ---------------------------------------------------------------------------
# 6. Frontend setup
# ---------------------------------------------------------------------------
info "Installing frontend dependencies..."
cd frontend
npm install
cd ..

# ---------------------------------------------------------------------------
# Done!
# ---------------------------------------------------------------------------
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  EsportsForge dev environment is ready!    ${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "  Backend API:    http://localhost:8000"
echo "  API Docs:       http://localhost:8000/api/docs"
echo "  Frontend:       http://localhost:3000"
echo "  PostgreSQL:     localhost:5432"
echo "  Redis:          localhost:6379"
echo ""
echo "  Start backend:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  Start frontend: cd frontend && npm run dev"
echo "  Or use:         make dev-start"
echo ""
