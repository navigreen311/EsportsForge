# Runbook — VAF Webhook-Delivery Alarm (ADR 0003)

How to deploy and operate the webhook-delivery-health alarm. The alarm **is
already defined as code**; what remains is deploying + test-firing it in a live
AWS environment. Companion to [1a-drill-lab-flag.md](1a-drill-lab-flag.md).

## What it is (already defined as code)

`infra/aws/cloudwatch-vaf-alarms.yaml` (CloudFormation) defines
**`vaf-webhook-failure-rate-${Environment}`**:

| Property | Value |
|---|---|
| Namespace / Metric | `EsportsForge/VAF` / `WebhookFailureRate` |
| Threshold | `0.001` (**0.1%**, per ADR 0003) · `GreaterThanThreshold` |
| Window | `Period 60` × `EvaluationPeriods 60` × `DatapointsToAlarm 60` = **>0.1% sustained 60 min** |
| Missing data | `notBreaching` |
| **Action** | `AlarmActions → SNS vaf-on-call-${Environment}` (email paging; `OKActions` too) |

The same stack also defines `AdapterBudgetBreachAlarm` (>5%/15 min) and
`AdapterLatencyP95Alarm` (>80 ms/10 min) → same SNS topic.

**Metric source:** `services/visionaudioforge/app/core/metrics.py` (`MetricsClient`)
emits `WebhookFailureRate` every 60 s. It **lazy-imports boto3 and no-ops if
boto3 is absent or `VAF_METRICS_DISABLED=1`** — so it produces a real datapoint
only in an environment with boto3 + AWS credentials + IAM `cloudwatch:PutMetricData`
on `EsportsForge/VAF`.

## Deploy (needs a live AWS env — not runnable locally)

The alarm stack is a **separate CloudFormation deploy** (the app itself deploys
via GitHub Actions — `make deploy-staging` / `gh workflow run deploy.yml`, see
[deploy.md](../deploy.md)):

```bash
aws cloudformation deploy \
  --stack-name vaf-cloudwatch-alarms \
  --template-file infra/aws/cloudwatch-vaf-alarms.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides Environment=<staging|prod> NotificationEmail=oncall@<domain>
```

- Requires AWS credentials / the OIDC deploy role (`AWS_DEPLOY_ROLE_ARN`, per deploy.md).
- `NotificationEmail` is a placeholder — **fill in the on-call address at deploy** (the SNS email subscription must be confirmed once).
- **Post-deploy verification (part of the deferred AWS work):** confirm the alarm fires in test mode at >0.1% synthetic failure (state report §2.1 approval #2 / §8 "verify test-mode fires >0.1%").

## What the alarm does when it trips (ADR 0003)

On trip → SNS `vaf-on-call` pages the on-call (email; `vaf-alarms` Slack). Per
ADR 0003 this **triggers the Redis-Streams-upgrade evaluation and blocks
Phase 1c** — Phase 1a/1b may proceed even with it firing (their events are
recoverable from the next event).

**It does NOT auto-flip the Drill Lab flag.** Per state report §2.5 (the
authority): the webhook alarm's action is block-1c + page; the **auto-flip**
rollback is a *separate* wire (Drill Lab **page-error-rate** and
**WS-connection-failure-rate**, Spec #03 §4).

## Manual rollback (this exists today)

To roll Drill Lab back, flip the master flag off — `VAF_DRILL_LAB_ENABLED`
backend env off + restart (~30 s), per [1a-drill-lab-flag.md](1a-drill-lab-flag.md).
The alarm does not do this for you.

> Not to be confused with `deploy.md`'s "Automatic Rollback" — that is the ECS
> deploy pipeline reverting to the previous task-definition revision on
> smoke-test failure, a different mechanism from the Drill Lab flag rollback.

## Deferred (with reasons — do NOT build here)

- **Auto-FLIP rollback** — a *separate* wire (page-error / WS-failure rate) that would flip the master flag automatically. The master flag is env-only (`VAF_DRILL_LAB_ENABLED`, set at backend start; ADR 0001 = engineer edit + restart, **no runtime-mutable store**). An alarm can't edit env + restart a task, so this needs a runtime-settings mechanism (e.g. SNS→Lambda→settings-write + restart) — **the deferred runtime-settings wall.** Not built.
- **Deploy + drill** — require a live AWS environment (credentials, CloudWatch receiving the metric, the stack deployed). Not available in local dev. The end-to-end **drill** (force >0.1% failure → alarm → page) must be exercised in that environment; it has not been run.
