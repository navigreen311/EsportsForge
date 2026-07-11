"""Unit tests for the AnimaForge webhook receiver.

Covers:
    * Bad signature -> 401
    * Unknown job_id -> 404
    * Valid signature + complete -> row updated, notification created,
      push hook called
    * ``user_id == "system"`` -> row updated, notification NOT created,
      push hook NOT called

Uses an in-memory SQLite engine, overrides the ``get_db`` dependency, and
mounts the webhook router onto the FastAPI app for local exercise (Agent #1
owns the canonical route mount in router.py — this test mounts independently
so Agent #2's branch can be verified in isolation).
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.v1.endpoints import animaforge_webhook as webhook_module
from app.db.base import Base, get_db
from app.main import app
from app.models.animaforge import (
    AnimaForgeJob,
    JOB_TYPE_DRILL,
    JOB_TYPE_WEAPON,
    STATUS_PENDING,
)
from app.models.notification import Notification


# ---------------------------------------------------------------------------
# Constants / helpers
# ---------------------------------------------------------------------------

WEBHOOK_PATH = "/api/v1/animaforge/webhook"
TEST_SECRET = "test-animaforge-webhook-secret"


def _sign(body_bytes: bytes, secret: str = TEST_SECRET) -> str:
    return hmac.new(
        secret.encode("utf-8"), body_bytes, hashlib.sha256
    ).hexdigest()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_db() -> AsyncIterator[AsyncSession]:
    """In-memory async SQLite session with all models created."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    # Make sure every model is registered before metadata.create_all.
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_maker() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(
    test_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[AsyncClient]:
    """HTTPX async client with webhook router mounted + ``get_db`` overridden."""
    # Mount the webhook router under the canonical prefix if it isn't already.
    prefix = "/api/v1/animaforge"
    already_mounted = any(
        getattr(r, "path", "").startswith(prefix) for r in app.routes
    )
    if not already_mounted:
        app.include_router(webhook_module.router, prefix=prefix)

    # Inject the webhook secret. Agent #1 owns the canonical
    # ``settings.animaforge_webhook_secret`` field; pydantic-settings rejects
    # unknown fields at runtime, so we monkeypatch the resolver helper that
    # the webhook uses (``_get_webhook_secret``) instead.
    monkeypatch.setattr(
        webhook_module, "_get_webhook_secret", lambda: TEST_SECRET
    )

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    # FastAPI is a valid ASGI app; httpx's ASGITransport.app type is narrower.
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def push_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Capture every ``send_animaforge_push`` invocation."""
    calls: list[dict] = []

    async def fake_send(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)

    monkeypatch.setattr(webhook_module, "send_animaforge_push", fake_send)
    return calls


# ---------------------------------------------------------------------------
# Test data helpers
# ---------------------------------------------------------------------------

async def _seed_job(
    db: AsyncSession,
    *,
    user_id: str = "user-123",
    job_id: str = "af_job_abc",
    job_type: str = JOB_TYPE_WEAPON,
    source_id: str = "weapon-uuid-1",
    title_id: str = "madden-26",
) -> AnimaForgeJob:
    job = AnimaForgeJob(
        user_id=user_id,
        job_id=job_id,
        type=job_type,
        source_id=source_id,
        title_id=title_id,
        status=STATUS_PENDING,
    )
    db.add(job)
    await db.flush()
    return job


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSignatureVerification:
    """The webhook MUST reject any request whose signature doesn't validate."""

    @pytest.mark.asyncio
    async def test_missing_signature_header_returns_401(
        self, client: AsyncClient, test_db: AsyncSession, push_calls: list[dict]
    ):
        await _seed_job(test_db)
        body = json.dumps({"jobId": "af_job_abc", "status": "complete"})
        resp = await client.post(WEBHOOK_PATH, content=body)
        assert resp.status_code == 401
        assert resp.json()["detail"] == "invalid signature"
        assert push_calls == []

    @pytest.mark.asyncio
    async def test_bad_signature_returns_401(
        self, client: AsyncClient, test_db: AsyncSession, push_calls: list[dict]
    ):
        await _seed_job(test_db)
        body = json.dumps({"jobId": "af_job_abc", "status": "complete"})
        resp = await client.post(
            WEBHOOK_PATH,
            content=body,
            headers={"X-AnimaForge-Signature": "deadbeef" * 8},
        )
        assert resp.status_code == 401
        assert push_calls == []

    @pytest.mark.asyncio
    async def test_signature_over_modified_body_returns_401(
        self, client: AsyncClient, test_db: AsyncSession, push_calls: list[dict]
    ):
        """Sign one body but send a different one — must still 401."""
        await _seed_job(test_db)
        signed_body = json.dumps({"jobId": "af_job_abc", "status": "rendering"})
        sent_body = json.dumps({"jobId": "af_job_abc", "status": "complete"})
        resp = await client.post(
            WEBHOOK_PATH,
            content=sent_body,
            headers={"X-AnimaForge-Signature": _sign(signed_body.encode())},
        )
        assert resp.status_code == 401
        assert push_calls == []


class TestUnknownJob:
    @pytest.mark.asyncio
    async def test_unknown_job_id_returns_404(
        self, client: AsyncClient, push_calls: list[dict]
    ):
        body_bytes = json.dumps(
            {"jobId": "af_does_not_exist", "status": "complete"}
        ).encode()
        resp = await client.post(
            WEBHOOK_PATH,
            content=body_bytes,
            headers={"X-AnimaForge-Signature": _sign(body_bytes)},
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "job not found"
        assert push_calls == []


class TestCompleteFlow:
    @pytest.mark.asyncio
    async def test_complete_updates_row_creates_notification_fires_push(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        push_calls: list[dict],
    ):
        await _seed_job(
            test_db,
            user_id="user-xyz",
            job_id="af_complete_1",
            job_type=JOB_TYPE_WEAPON,
            source_id="weapon-uuid-9",
        )
        body = {
            "jobId": "af_complete_1",
            "status": "complete",
            "videoUrl": "https://cdn.example.com/v.mp4",
            "thumbnailUrl": "https://cdn.example.com/t.jpg",
        }
        body_bytes = json.dumps(body).encode()
        resp = await client.post(
            WEBHOOK_PATH,
            content=body_bytes,
            headers={"X-AnimaForge-Signature": _sign(body_bytes)},
        )
        assert resp.status_code == 200
        assert resp.json() == {"received": True}

        # Row updated.
        row = (
            await test_db.execute(
                select(AnimaForgeJob).where(
                    AnimaForgeJob.job_id == "af_complete_1"
                )
            )
        ).scalar_one()
        assert row.status == "complete"
        assert row.video_url == "https://cdn.example.com/v.mp4"
        assert row.thumbnail_url == "https://cdn.example.com/t.jpg"
        assert row.completed_at is not None

        # Notification created.
        notifs = (
            await test_db.execute(
                select(Notification).where(Notification.user_id == "user-xyz")
            )
        ).scalars().all()
        assert len(notifs) == 1
        assert notifs[0].type == "animaforge-complete"
        assert notifs[0].title == "Animation Ready"
        assert "Arsenal" in notifs[0].body
        assert notifs[0].action_url == (
            "/dashboard/arsenal?weaponId=weapon-uuid-9"
        )

        # Push hook called once with matching payload.
        assert len(push_calls) == 1
        call = push_calls[0]
        assert call["user_id"] == "user-xyz"
        assert call["title"] == "Animation Ready"
        assert call["action_url"] == (
            "/dashboard/arsenal?weaponId=weapon-uuid-9"
        )

    @pytest.mark.asyncio
    async def test_failed_status_updates_row_no_notification(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        push_calls: list[dict],
    ):
        await _seed_job(
            test_db, user_id="user-1", job_id="af_failed_1"
        )
        body = {
            "jobId": "af_failed_1",
            "status": "failed",
            "errorMessage": "render service exploded",
        }
        body_bytes = json.dumps(body).encode()
        resp = await client.post(
            WEBHOOK_PATH,
            content=body_bytes,
            headers={"X-AnimaForge-Signature": _sign(body_bytes)},
        )
        assert resp.status_code == 200

        row = (
            await test_db.execute(
                select(AnimaForgeJob).where(
                    AnimaForgeJob.job_id == "af_failed_1"
                )
            )
        ).scalar_one()
        assert row.status == "failed"
        assert row.error_message == "render service exploded"
        assert row.completed_at is not None  # terminal

        # No notification, no push for failed jobs.
        notifs = (
            await test_db.execute(select(Notification))
        ).scalars().all()
        assert notifs == []
        assert push_calls == []


class TestSystemUser:
    @pytest.mark.asyncio
    async def test_system_user_updates_row_but_skips_notification(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        push_calls: list[dict],
    ):
        """Drill demos render under user_id='system' and are shared.

        We MUST update the row (so the cached video_url is available) but
        MUST NOT create per-user notifications or fire push for the literal
        ``"system"`` user.
        """
        await _seed_job(
            test_db,
            user_id="system",
            job_id="af_drill_shared_1",
            job_type=JOB_TYPE_DRILL,
            source_id="madden-26:pre-snap-reads",
        )
        body = {
            "jobId": "af_drill_shared_1",
            "status": "complete",
            "videoUrl": "https://cdn.example.com/drill.mp4",
        }
        body_bytes = json.dumps(body).encode()
        resp = await client.post(
            WEBHOOK_PATH,
            content=body_bytes,
            headers={"X-AnimaForge-Signature": _sign(body_bytes)},
        )
        assert resp.status_code == 200
        assert resp.json() == {"received": True}

        # Row IS updated.
        row = (
            await test_db.execute(
                select(AnimaForgeJob).where(
                    AnimaForgeJob.job_id == "af_drill_shared_1"
                )
            )
        ).scalar_one()
        assert row.status == "complete"
        assert row.video_url == "https://cdn.example.com/drill.mp4"

        # Notification is NOT created.
        notifs = (
            await test_db.execute(select(Notification))
        ).scalars().all()
        assert notifs == []

        # Push hook NOT called.
        assert push_calls == []


class TestActionUrlMapping:
    """Each job type maps to a specific dashboard action_url."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "job_type,source_id,expected",
        [
            ("weapon-diagram", "wpn-1", "/dashboard/arsenal?weaponId=wpn-1"),
            ("drill-demo", "madden-26:read", "/dashboard/drills?drillKey=madden-26:read"),
            ("play-diagram", "play-7:cover-3", "/dashboard/gameplan?playId=play-7:cover-3"),
        ],
    )
    async def test_action_url_per_type(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        push_calls: list[dict],
        job_type: str,
        source_id: str,
        expected: str,
    ):
        # Use a regular user so the notification IS created (and its
        # action_url is what we want to assert against).
        job_id = f"af_{job_type}_url"
        await _seed_job(
            test_db,
            user_id="user-mapping",
            job_id=job_id,
            job_type=job_type,
            source_id=source_id,
        )
        body_bytes = json.dumps(
            {"jobId": job_id, "status": "complete"}
        ).encode()
        resp = await client.post(
            WEBHOOK_PATH,
            content=body_bytes,
            headers={"X-AnimaForge-Signature": _sign(body_bytes)},
        )
        assert resp.status_code == 200

        notif = (
            await test_db.execute(
                select(Notification).where(
                    Notification.user_id == "user-mapping"
                ).order_by(Notification.created_at.desc())
            )
        ).scalars().first()
        assert notif is not None
        assert notif.action_url == expected
        # Reset push capture for next param run.
        push_calls.clear()
