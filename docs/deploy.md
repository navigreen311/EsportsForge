# EsportsForge Deployment Guide

## Architecture

```mermaid
graph TB
    subgraph "Client"
        Browser[Browser]
    end

    subgraph "AWS Cloud"
        subgraph "Networking"
            ALB[Application Load Balancer]
            Route53[Route 53 DNS]
        end

        subgraph "ECS Cluster"
            FE1[Frontend Container 1]
            FE2[Frontend Container 2]
            BE1[Backend Container 1]
            BE2[Backend Container 2]
        end

        subgraph "Data Layer"
            RDS[(RDS PostgreSQL)]
            ElastiCache[(ElastiCache Redis)]
        end

        subgraph "CI/CD"
            GHA[GitHub Actions]
            ECR[ECR Registry]
        end
    end

    Browser --> Route53 --> ALB
    ALB --> FE1 & FE2
    ALB --> BE1 & BE2
    BE1 & BE2 --> RDS
    BE1 & BE2 --> ElastiCache
    GHA --> ECR --> ECS Cluster
```

## Prerequisites

| Tool            | Version | Purpose                        |
|-----------------|---------|--------------------------------|
| AWS CLI         | 2.x     | AWS resource management        |
| Docker          | 24+     | Container builds               |
| GitHub CLI (gh) | 2.x     | Workflow triggers              |
| Node.js         | 20+     | Frontend build                 |
| Python          | 3.12+   | Backend runtime                |

### AWS Resources Required

- **ECR**: Two repositories (`esportsforge/backend`, `esportsforge/frontend`)
- **ECS**: Fargate cluster with two services
- **RDS**: PostgreSQL 16 instance
- **ElastiCache**: Redis 7 cluster
- **ALB**: Application Load Balancer with target groups
- **Route 53**: DNS hosted zone
- **Secrets Manager**: API keys and credentials

## Environment Variables Reference

### Backend (ECS Task Definition)

| Variable              | Required | Description                              |
|-----------------------|----------|------------------------------------------|
| `DATABASE_URL`        | Yes      | PostgreSQL connection string (asyncpg)   |
| `REDIS_URL`           | Yes      | Redis connection string                  |
| `SECRET_KEY`          | Yes      | JWT signing key (min 32 chars)           |
| `ANTHROPIC_API_KEY`   | Yes      | Anthropic API key for Claude             |
| `CLAUDE_MODEL`        | No       | Model ID (default: claude-sonnet-4-20250514)  |
| `ENVIRONMENT`         | No       | `staging` or `production`                |
| `DEBUG`               | No       | `true` / `false` (default: false)        |
| `CORS_ORIGINS`        | No       | Comma-separated allowed origins          |

### Frontend (Build Args & Runtime)

| Variable               | Required | Description                             |
|------------------------|----------|-----------------------------------------|
| `NEXT_PUBLIC_API_URL`  | Yes      | Backend API URL (baked at build time)   |
| `NEXTAUTH_SECRET`      | Yes      | NextAuth.js signing secret              |
| `NEXTAUTH_URL`         | Yes      | Canonical app URL                       |

### GitHub Actions Secrets

| Secret                   | Description                              |
|--------------------------|------------------------------------------|
| `AWS_DEPLOY_ROLE_ARN`   | IAM role ARN for OIDC authentication     |
| `NEXT_PUBLIC_API_URL`    | Set per environment in GitHub vars       |

## Deploy Commands

### Staging (automatic)

Every push to `main` triggers an automatic staging deployment:

```bash
git push origin main
# Monitor: https://github.com/<org>/esportsforge/actions
```

### Staging (manual)

```bash
make deploy-staging
# or directly:
gh workflow run deploy.yml -f environment=staging
```

### Production

```bash
make deploy-prod
# or directly:
gh workflow run deploy.yml -f environment=production
```

### Emergency Deploy (skip tests)

```bash
gh workflow run deploy.yml -f environment=production -f skip_tests=true
```

## Rollback Procedure

### Automatic Rollback

The deploy pipeline includes automatic rollback. If smoke tests fail after deployment, the pipeline will:

1. Identify the previous ECS task definition revision
2. Update the ECS service to use the previous revision
3. Wait for the rollback to stabilize
4. Send a notification to the team

### Manual Rollback

```bash
# 1. List recent task definition revisions
aws ecs list-task-definitions \
  --family-prefix esportsforge-backend \
  --sort DESC --max-items 5

# 2. Update service to a known-good revision
aws ecs update-service \
  --cluster esportsforge-prod \
  --service esportsforge-backend \
  --task-definition esportsforge-backend:<REVISION_NUMBER>

# 3. Wait for stabilization
aws ecs wait services-stable \
  --cluster esportsforge-prod \
  --services esportsforge-backend

# 4. Verify health
curl -sf https://api.esportsforge.gg/api/health | jq .
```

### Database Rollback

```bash
# Downgrade one Alembic revision
alembic downgrade -1

# Or downgrade to a specific revision
alembic downgrade <revision_id>
```

## Monitoring Endpoints

| Endpoint                  | Description                | Expected Response      |
|---------------------------|----------------------------|------------------------|
| `GET /api/health`         | Backend health check       | `{"status": "healthy"}`|
| `GET /api/v1/status`      | Platform status with components | Full status JSON  |
| `GET /api/docs`           | Swagger UI                 | HTML page              |

### Health Check URLs by Environment

| Environment | Backend                                      | Frontend                              |
|-------------|----------------------------------------------|---------------------------------------|
| Staging     | `https://api.staging.esportsforge.gg/api/health` | `https://staging.esportsforge.gg/` |
| Production  | `https://api.esportsforge.gg/api/health`     | `https://esportsforge.gg/`           |

## Troubleshooting

### Container won't start

```bash
# Check ECS service events
aws ecs describe-services --cluster <CLUSTER> --services <SERVICE> \
  --query 'services[0].events[:5]'

# Check container logs
aws logs tail /ecs/esportsforge-backend --follow
```

### Database connection issues

```bash
# Verify RDS security group allows ECS task security group
aws ec2 describe-security-groups --group-ids <RDS_SG_ID>

# Test connectivity from ECS exec
aws ecs execute-command --cluster <CLUSTER> --task <TASK_ID> \
  --container backend --interactive --command "/bin/bash"
```
