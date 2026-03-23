#!/usr/bin/env bash
# =============================================================================
# EsportsForge — Run All Tests
# Usage: bash scripts/test-all.sh
# =============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKEND_EXIT=0
FRONTEND_EXIT=0

echo "============================================"
echo "  EsportsForge — Full Test Suite"
echo "============================================"
echo ""

# ---------------------------------------------------------------------------
# Backend Tests
# ---------------------------------------------------------------------------
echo -e "${YELLOW}>>> Running backend tests...${NC}"
cd backend

# Activate venv if it exists
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
  source venv/Scripts/activate
fi

if pytest --cov=app --cov-report=term-missing -v 2>&1; then
  echo -e "${GREEN}Backend tests: PASSED${NC}"
else
  BACKEND_EXIT=$?
  echo -e "${RED}Backend tests: FAILED (exit code $BACKEND_EXIT)${NC}"
fi

cd ..
echo ""

# ---------------------------------------------------------------------------
# Frontend Tests
# ---------------------------------------------------------------------------
echo -e "${YELLOW}>>> Running frontend tests...${NC}"
cd frontend

if npm test -- --coverage --passWithNoTests 2>&1; then
  echo -e "${GREEN}Frontend tests: PASSED${NC}"
else
  FRONTEND_EXIT=$?
  echo -e "${RED}Frontend tests: FAILED (exit code $FRONTEND_EXIT)${NC}"
fi

cd ..
echo ""

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "============================================"
echo "  Test Summary"
echo "============================================"

if [ "$BACKEND_EXIT" -eq 0 ]; then
  echo -e "  Backend:  ${GREEN}PASSED${NC}"
else
  echo -e "  Backend:  ${RED}FAILED${NC}"
fi

if [ "$FRONTEND_EXIT" -eq 0 ]; then
  echo -e "  Frontend: ${GREEN}PASSED${NC}"
else
  echo -e "  Frontend: ${RED}FAILED${NC}"
fi

echo "============================================"
echo ""

# Exit with failure if any suite failed
if [ "$BACKEND_EXIT" -ne 0 ] || [ "$FRONTEND_EXIT" -ne 0 ]; then
  exit 1
fi

echo -e "${GREEN}All tests passed!${NC}"
