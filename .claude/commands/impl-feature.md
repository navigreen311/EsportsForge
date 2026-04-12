# EsportsForge Feature Implementation Command

## Project Context
EsportsForge — Next.js 14 + TypeScript + Tailwind (frontend) + FastAPI + SQLAlchemy + PostgreSQL (backend) + Redis + Anthropic Claude API
Green Companies LLC | navigreen311 GitHub org

## Architecture
- Frontend: Next.js app router at frontend/src/app/(dashboard)/[page]/page.tsx
- Backend: FastAPI at backend/app/api/v1/endpoints/
- AI agents: backend/app/services/ai/ — all use claude-sonnet-4-20250514
- Database: SQLAlchemy ORM — models at backend/app/models/
- State: Zustand for client state, React Query for server state
- Styling: Tailwind CSS — dark theme bg-dark-900, card bg-dark-800, accent forge-400/forge-600

## Git Workflow
1. git checkout -b ai-feature/[feature-name]
2. Implement end-to-end
3. git add relevant files && git commit -m "feat([scope]): [description]"
4. git push origin ai-feature/[feature-name]

## Quality Gates
- Backend: uvicorn starts cleanly, all endpoints return expected responses
- Frontend: npm run build must pass with zero TypeScript errors
- All new components have loading and error states
- IntegrityMode checked on any feature using AI or screen capture

## Feature to Implement
$ARGUMENTS
