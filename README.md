# EsportsForge

> Built to Win. Not to Coach.

AI-powered competitive gaming intelligence platform — 11 titles, 57 AI agents, one decisive voice.

## Phase 1 MVP

- **Universal Backbone**: ForgeData Fabric, ForgeCore Orchestrator, PlayerTwin AI, ImpactRank AI, Truth Engine, LoopAI
- **Launch Titles**: Madden 26 + EA Sports College Football 26
- **Governance**: IntegrityMode + Mode Integrity Matrix

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL + Redis |
| AI | LangGraph + Anthropic Claude API |
| Auth | NextAuth.js + JWT |
| Deploy | Docker + AWS (ECS + RDS + ElastiCache) |

## Quick Start

```bash
# Clone
git clone https://github.com/navigreen311/EsportsForge.git
cd EsportsForge

# Environment
cp .env.example .env
# Fill in your API keys

# Docker (recommended)
docker compose up -d

# Or manual:
# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Project Structure

```
EsportsForge/
├── frontend/          # Next.js 14 + TypeScript
│   └── src/
│       ├── app/       # App router pages
│       ├── components/ # React components
│       ├── lib/       # Utilities & API client
│       ├── hooks/     # Custom React hooks
│       └── types/     # TypeScript types
├── backend/           # FastAPI Python
│   └── app/
│       ├── api/       # REST endpoints
│       ├── core/      # Config, security
│       ├── models/    # SQLAlchemy models
│       ├── schemas/   # Pydantic schemas
│       ├── services/  # Business logic
│       │   ├── backbone/  # Universal backbone agents
│       │   └── agents/    # Title-specific agents
│       └── db/        # Database setup
├── docs/              # Documentation
├── infra/             # Infrastructure configs
└── scripts/           # Automation scripts
```

## Development

See [CLAUDE.md](CLAUDE.md) for AI-assisted development workflow.
