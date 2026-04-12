# EsportsForge Test Suite Command

## Testing Stack
- Backend: pytest + pytest-asyncio (backend/tests/)
- Frontend: Jest + React Testing Library (frontend/)
- Run backend tests: cd backend && pytest
- Run frontend tests: cd frontend && npm test

## What to Test
1. Backend unit: services/ai/* — mock Claude API, verify prompt structure
2. Backend integration: API endpoint tests with test database
3. Frontend unit: component rendering tests
4. Frontend integration: page-level tests

## Feature to Test
$ARGUMENTS
