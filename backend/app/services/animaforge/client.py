"""AnimaForge HTTP client — wraps the external AnimaForge render service.

All EsportsForge code that needs to talk to AnimaForge goes through this
single class. Frontend never calls AnimaForge directly — the API key stays
on the backend.

Public surface (per contract §3):
  * ``AnimaForgeService.is_available()`` — health probe, swallows all errors.
  * ``AnimaForgeService.request_render(...)`` — POST a render job.
  * ``AnimaForgeService.get_job_status(job_id)`` — GET live status.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings
from app.services.animaforge.exceptions import AnimaForgeUnavailable

logger = logging.getLogger(__name__)


# Timeouts (seconds) — short for health probes, longer for render submits
_AVAILABILITY_TIMEOUT = 5.0
_RENDER_TIMEOUT = 30.0
_STATUS_TIMEOUT = 10.0


def _api_url() -> str:
    return (settings.animaforge_api_url or "").rstrip("/")


def _auth_headers() -> dict[str, str]:
    key = settings.animaforge_api_key or ""
    return {"Authorization": f"Bearer {key}"} if key else {}


def _default_webhook_url() -> str:
    base = (settings.animaforge_webhook_base_url or "").rstrip("/")
    return f"{base}/api/v1/animaforge/webhook"


class AnimaForgeService:
    """Static wrapper around AnimaForge REST API."""

    @staticmethod
    async def is_available() -> bool:
        """Return True iff AnimaForge `/health` responds 2xx within 5s.

        Swallows every error (network, timeout, missing config, non-2xx).
        Used by `/api/v1/animaforge/status` to gate the UI silently.
        """
        url = _api_url()
        if not url:
            return False
        try:
            async with httpx.AsyncClient(timeout=_AVAILABILITY_TIMEOUT) as client:
                resp = await client.get(f"{url}/health")
                return resp.status_code < 400
        except Exception as exc:  # noqa: BLE001 — intentional broad catch
            logger.debug("AnimaForge availability probe failed: %s", exc)
            return False

    @staticmethod
    async def request_render(
        *,
        type: str,
        title_id: str,
        spec: dict[str, Any],
        user_id: str,
        webhook_url: str | None = None,
    ) -> dict[str, Any]:
        """Submit a render job to AnimaForge.

        Returns a dict shaped either as:
          * ``{"video_url": "...", "thumbnail_url": "..."}`` (cached hit), or
          * ``{"job_id": "...", "estimated_seconds": int, "status": "pending"}``.

        Raises:
            AnimaForgeUnavailable: on network errors or 5xx responses.
        """
        url = _api_url()
        if not url:
            raise AnimaForgeUnavailable("AnimaForge API URL not configured")

        payload = {
            "type": type,
            "title_id": title_id,
            "data": spec,
            "user_id": user_id,
            "webhook_url": webhook_url or _default_webhook_url(),
        }
        try:
            async with httpx.AsyncClient(timeout=_RENDER_TIMEOUT) as client:
                resp = await client.post(
                    f"{url}/api/v1/render",
                    json=payload,
                    headers={**_auth_headers(), "Content-Type": "application/json"},
                )
        except httpx.HTTPError as exc:
            logger.warning("AnimaForge render request failed: %s", exc)
            raise AnimaForgeUnavailable(str(exc)) from exc

        if resp.status_code >= 500:
            raise AnimaForgeUnavailable(
                f"AnimaForge returned {resp.status_code}: {resp.text[:200]}"
            )
        if resp.status_code >= 400:
            # Treat 4xx as caller error — surface details but don't pretend it's
            # an outage.
            raise AnimaForgeUnavailable(
                f"AnimaForge rejected request ({resp.status_code}): {resp.text[:200]}"
            )

        try:
            return resp.json()
        except ValueError as exc:
            raise AnimaForgeUnavailable(
                f"AnimaForge returned non-JSON response: {exc}"
            ) from exc

    @staticmethod
    async def get_job_status(job_id: str) -> dict[str, Any]:
        """Fetch live status of an AnimaForge job.

        Returns a dict like::

            {"status": "pending"|"rendering"|"complete"|"failed",
             "video_url": str?, "thumbnail_url": str?, "progress": int?}

        Raises:
            AnimaForgeUnavailable: on network errors or 5xx responses.
        """
        url = _api_url()
        if not url:
            raise AnimaForgeUnavailable("AnimaForge API URL not configured")

        try:
            async with httpx.AsyncClient(timeout=_STATUS_TIMEOUT) as client:
                resp = await client.get(
                    f"{url}/api/v1/jobs/{job_id}",
                    headers=_auth_headers(),
                )
        except httpx.HTTPError as exc:
            logger.warning("AnimaForge status fetch failed: %s", exc)
            raise AnimaForgeUnavailable(str(exc)) from exc

        if resp.status_code >= 500:
            raise AnimaForgeUnavailable(
                f"AnimaForge returned {resp.status_code}"
            )
        if resp.status_code == 404:
            # Not found is informational, not an outage — but surface it as
            # unavailable so callers get a single failure mode.
            raise AnimaForgeUnavailable(f"Job {job_id} not found in AnimaForge")
        if resp.status_code >= 400:
            raise AnimaForgeUnavailable(
                f"AnimaForge status returned {resp.status_code}: {resp.text[:200]}"
            )
        try:
            return resp.json()
        except ValueError as exc:
            raise AnimaForgeUnavailable(
                f"AnimaForge returned non-JSON response: {exc}"
            ) from exc
