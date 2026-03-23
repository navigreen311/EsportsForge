# deploy-prod — Prepare Production Deployment

Prepare production deployment assets and a repeatable deployment pipeline.

## Arguments

$ARGUMENTS

Parse the following from the arguments:

| Argument          | Required | Default          | Description                                         |
|-------------------|----------|------------------|-----------------------------------------------------|
| `platform`        | Yes      | —                | Target: `vercel`, `aws`, `gcp`, `azure`, `docker`, `fly.io` |
| `region`          | No       | `us-east-1`     | Deployment region                                    |
| `runtime`         | No       | auto-detect      | Runtime: `node`, `python`, `go`, etc.                |
| `database`        | No       | —                | DB service: `postgres`, `mysql`, `mongo`, `sqlite`   |
| `secrets_source`  | No       | `env`            | Secrets from: `env`, `aws-ssm`, `vault`, `doppler`   |
| `zero_downtime`   | No       | `true`           | Whether to configure zero-downtime deploys            |

---

## Process

### Step 1: Architecture Diagram
1. Document the production architecture (Mermaid diagram).
2. Include: compute, database, CDN, load balancer, DNS, monitoring.
3. Save to `docs/deploy.md`.

### Step 2: Infrastructure / Platform Config
Based on `platform`, create the appropriate configuration:

- **Vercel**: `vercel.json` + environment variable setup guide
- **AWS**: CDK/CloudFormation/Terraform files in `infra/`
- **Docker**: `Dockerfile` + `docker-compose.prod.yml`
- **Fly.io**: `fly.toml` + deployment guide
- **GCP/Azure**: Equivalent IaC files

### Step 3: Build & Release Scripts
1. Create build script: `scripts/build.sh` (or npm script).
2. Create release script: `scripts/deploy.sh` with:
   - Environment validation
   - Build step
   - Database migration (if applicable)
   - Deployment command
   - Health check verification
3. Make scripts idempotent and safe to re-run.

### Step 4: Rollout Strategy
Configure based on `zero_downtime`:
- **Rolling deploy**: gradual instance replacement
- **Blue/green**: parallel environments with traffic switch
- **Canary**: percentage-based traffic shifting
- Document the **rollback procedure**.

### Step 5: Observability
1. Health check endpoint: `GET /health` or `/api/health`
2. Logging configuration (structured JSON logs).
3. Monitoring recommendations (error rates, latency, resource usage).
4. Alert thresholds and notification channels.

### Step 6: Staging Deploy & Smoke Test
1. Deploy to staging (or preview) environment.
2. Run smoke tests against staging.
3. Document staging URL and test results.

---

## Output

```
## DEPLOYMENT ASSETS
- [list of infra/config files created]

## HOW TO DEPLOY
- Staging: [exact commands]
- Production: [exact commands]

## ROLLBACK
- [rollback command or procedure]

## ARCHITECTURE
- [link to docs/deploy.md with diagram]

## FACT-CHECK LIST
- [ ] [platform] pricing tier supports [X concurrent connections]
- [ ] [database] version [X] is supported on [platform]
- [ ] SSL/TLS configured for all endpoints
- [ ] Secrets are NOT in version control
```

---

## Example Invocation

```
/deploy-prod platform=docker region=us-east-1 database=postgres secrets_source=env zero_downtime=true
```
