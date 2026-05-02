# Changelog

All notable changes to EsportsForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- `Settings` now declares `redis_max_connections: int = 50` and `redis_socket_timeout: float = 5.0`;
  `app/db/redis.py:init_redis()` referenced both attrs but they were never defined, causing
  `AttributeError` on app startup when a Redis URL was configured.
- `SquadOps.decide_revive_priority` scoring tuned (K/D weight × 16, damage ÷ 40) so a
  high-damage Slayer-type player ranks above an IGL whose only advantage is a high comms score;
  fixes `TestSquadOps::test_revive_priority_orders_by_value`.
- `SquadOps.assign_roles` greedy algorithm correctly prevents duplicate non-FLEX role
  assignments; `TestSquadIntegrity::test_no_duplicate_role_assignments` now green.

### Added
- Initial monorepo scaffold (Next.js frontend + FastAPI backend)
- CLAUDE.md AI development configuration
- Claude Code commands: impl-feature, test-suite, deploy-prod, code-review, api-test
- Docker Compose for local development (Postgres + Redis)
- Health check endpoint at `/api/health`
