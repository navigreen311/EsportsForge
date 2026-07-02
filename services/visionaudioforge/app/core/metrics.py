"""CloudWatch metrics publisher for VAF.

Phase 0 + post-PR-#62 review (L2): wire the per-session webhook failure-
rate metric so the ADR 0003 alarm has a real signal to fire on.

Design:
  - One MetricsClient per process. Lazy boto3 import; if boto3 is absent
    or `VAF_METRICS_DISABLED=1`, every method is a no-op (so dev runs
    without AWS creds don't blow up).
  - Per-session failure rate is published every 60 seconds. The
    CloudWatch alarm (defined in infra/aws/cloudwatch-vaf-alarms.yaml)
    fires on >0.1% sustained over 60 min — i.e., a 60-datapoint window
    on a 1-minute resolution metric.
  - Namespace is `EsportsForge/VAF`. Dimensions: `SessionId`, `Title`.

This module deliberately avoids importing boto3 at the top level —
many dev paths don't need it, and we don't want to pull a 30 MB
dependency on CI for code that only matters in production.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

logger = logging.getLogger("vaf.metrics")

NAMESPACE = "EsportsForge/VAF"
METRIC_FAILURE_RATE = "WebhookFailureRate"
METRIC_LATENCY_P95 = "AdapterLatencyP95Ms"
METRIC_BUDGET_BREACH_RATE = "AdapterBudgetBreachRate"


class MetricsClient:
    """Thin wrapper over `cloudwatch.put_metric_data`. No-op when disabled."""

    _instance: "MetricsClient | None" = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._enabled = os.environ.get("VAF_METRICS_DISABLED") != "1"
        self._client = None
        self._client_init_failed = False

    @classmethod
    def get(cls) -> "MetricsClient":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _ensure_client(self) -> Any | None:
        if not self._enabled or self._client_init_failed:
            return None
        if self._client is not None:
            return self._client
        try:
            import boto3  # type: ignore
        except ImportError:
            logger.info("metrics_disabled_no_boto3")
            self._client_init_failed = True
            return None
        try:
            region = os.environ.get("AWS_REGION", "us-east-1")
            self._client = boto3.client("cloudwatch", region_name=region)
            logger.info("cloudwatch_client_ready", extra={"region": region})
            return self._client
        except Exception as exc:  # noqa: BLE001
            logger.warning("cloudwatch_client_init_failed", extra={"exc": str(exc)})
            self._client_init_failed = True
            return None

    def publish_failure_rate(
        self,
        *,
        session_id: str,
        title: str,
        rate: float,
        delivered: int,
        failed: int,
    ) -> None:
        """Publish per-session webhook failure rate.

        Rate is a fraction (0.0–1.0). The alarm threshold is 0.001
        (0.1%) sustained for 60 datapoints — see the alarm template.
        """
        client = self._ensure_client()
        if client is None:
            return
        try:
            client.put_metric_data(
                Namespace=NAMESPACE,
                MetricData=[
                    {
                        "MetricName": METRIC_FAILURE_RATE,
                        "Dimensions": [
                            {"Name": "SessionId", "Value": session_id},
                            {"Name": "Title", "Value": title},
                        ],
                        "Value": rate,
                        "Unit": "None",
                        "StorageResolution": 60,
                    },
                    # Also publish raw counts for follow-up analysis.
                    {
                        "MetricName": "WebhookEventsDelivered",
                        "Dimensions": [{"Name": "Title", "Value": title}],
                        "Value": delivered,
                        "Unit": "Count",
                    },
                    {
                        "MetricName": "WebhookEventsFailed",
                        "Dimensions": [{"Name": "Title", "Value": title}],
                        "Value": failed,
                        "Unit": "Count",
                    },
                ],
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("publish_failure_rate_failed", extra={"exc": str(exc)})

    def publish_latency(
        self,
        *,
        session_id: str,
        title: str,
        p95_ms: float,
        breach_rate: float,
    ) -> None:
        """Publish per-session adapter latency. Used by Phase 1a's
        budget-breach alarm; defined here so the metric shape is
        symmetric with the failure-rate metric."""
        client = self._ensure_client()
        if client is None:
            return
        try:
            client.put_metric_data(
                Namespace=NAMESPACE,
                MetricData=[
                    {
                        "MetricName": METRIC_LATENCY_P95,
                        "Dimensions": [
                            {"Name": "SessionId", "Value": session_id},
                            {"Name": "Title", "Value": title},
                        ],
                        "Value": p95_ms,
                        "Unit": "Milliseconds",
                        "StorageResolution": 60,
                    },
                    {
                        "MetricName": METRIC_BUDGET_BREACH_RATE,
                        "Dimensions": [{"Name": "Title", "Value": title}],
                        "Value": breach_rate,
                        "Unit": "None",
                    },
                ],
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("publish_latency_failed", extra={"exc": str(exc)})
