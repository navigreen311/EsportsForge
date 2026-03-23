# =============================================================================
# EsportsForge — Makefile
# =============================================================================
.PHONY: help dev-setup dev-start dev-stop test test-backend test-frontend \
        build build-backend build-frontend docker-up docker-down \
        lint lint-fix db-migrate db-reset deploy-staging deploy-prod

COMPOSE := docker compose
PYTHON  := python3
BACKEND := cd backend
FRONTEND := cd frontend

# Default target
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# Development
# =============================================================================
dev-setup: ## Set up local development environment
	bash scripts/dev-setup.sh

dev-start: ## Start all services for local development
	$(COMPOSE) up -d postgres redis
	@echo "Starting backend..."
	$(BACKEND) && source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null && \
		uvicorn app.main:app --reload --port 8000 &
	@echo "Starting frontend..."
	$(FRONTEND) && npm run dev &
	@echo ""
	@echo "Backend:  http://localhost:8000"
	@echo "Frontend: http://localhost:3000"

dev-stop: ## Stop all development services
	$(COMPOSE) down
	@-pkill -f "uvicorn app.main:app" 2>/dev/null || true
	@-pkill -f "next dev" 2>/dev/null || true
	@echo "All services stopped."

# =============================================================================
# Testing
# =============================================================================
test: ## Run all tests (backend + frontend)
	bash scripts/test-all.sh

test-backend: ## Run backend tests with coverage
	$(BACKEND) && \
		(source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null) && \
		pytest --cov=app --cov-report=term-missing -v

test-frontend: ## Run frontend tests with coverage
	$(FRONTEND) && npm test -- --coverage --passWithNoTests

# =============================================================================
# Building
# =============================================================================
build: build-backend build-frontend ## Build all Docker images

build-backend: ## Build backend Docker image
	docker build -t esportsforge-backend:latest ./backend

build-frontend: ## Build frontend Docker image
	docker build -t esportsforge-frontend:latest ./frontend

# =============================================================================
# Docker Compose
# =============================================================================
docker-up: ## Start all containers via docker compose
	$(COMPOSE) up -d --build

docker-down: ## Stop and remove all containers
	$(COMPOSE) down -v

# =============================================================================
# Linting
# =============================================================================
lint: ## Run all linters
	@echo "=== Backend linting ==="
	$(BACKEND) && \
		(source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null) && \
		flake8 app/ --max-line-length=120 --exclude=__pycache__,migrations && \
		mypy app/ --ignore-missing-imports
	@echo ""
	@echo "=== Frontend linting ==="
	$(FRONTEND) && npx next lint && npx tsc --noEmit

lint-fix: ## Run linters with auto-fix where possible
	$(FRONTEND) && npx next lint --fix

# =============================================================================
# Database
# =============================================================================
db-migrate: ## Run Alembic migrations
	$(BACKEND) && \
		(source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null) && \
		alembic upgrade head

db-reset: ## Reset database (drop + recreate + migrate)
	$(COMPOSE) exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS esportsforge;"
	$(COMPOSE) exec postgres psql -U postgres -c "CREATE DATABASE esportsforge;"
	$(MAKE) db-migrate

# =============================================================================
# Deployment
# =============================================================================
deploy-staging: ## Deploy to staging environment
	@echo "Triggering staging deploy..."
	gh workflow run deploy.yml -f environment=staging
	@echo "Monitor at: https://github.com/$$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions"

deploy-prod: ## Deploy to production (requires confirmation)
	@echo "WARNING: You are about to deploy to PRODUCTION."
	@read -p "Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ] || (echo "Aborted." && exit 1)
	gh workflow run deploy.yml -f environment=production
	@echo "Monitor at: https://github.com/$$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions"
