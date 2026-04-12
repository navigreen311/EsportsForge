# Production Deployment Command

## Pre-Deployment Checklist
1. Backend: uvicorn starts, all endpoints respond
2. Frontend: npm run build — zero errors
3. Run all tests
4. Verify .env variables set in production
5. Check health endpoint: /api/health returns all green

## Deployment (Docker)
1. docker compose -f docker-compose.prod.yml build
2. docker compose -f docker-compose.prod.yml up -d
3. Monitor health checks
4. Verify /api/health returns green

## What to Deploy
$ARGUMENTS
