"""End-to-end tests for AnimaForge core endpoints (Agent #1).

Uses the project's standard ``client`` async fixture (sqlite test DB +
ASGITransport) and monkeypatches the AnimaForge service layer so no real
HTTP traffic is attempted.

Users are created directly in the test DB and JWTs are minted in-process,
bypassing the per-IP rate limiter on ``/auth/register`` and ``/auth/login``
(which is shared global state across the whole test session).
"""

from __future__ import annotations

import pytest

from app.core.security import create_access_token, hash_password
from app.models.animaforge import AnimaForgeJob
from app.models.user import User, UserRole
from app.services.animaforge import client as animaforge_client_module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _make_user(
    test_db, *, email: str, username: str
) -> tuple[str, str]:
    """Create a user directly in the DB and return ``(user_id, token)``."""
    user = User(
        email=email,
        username=username,
        hashed_password=hash_password("SecurePass123!"),
        display_name=username,
        role=UserRole.FREE,
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    token = create_access_token(subject=user.id)
    return user.id, token


async def _seed_job(test_db, *, user_id: str, **overrides) -> AnimaForgeJob:
    job = AnimaForgeJob(
        user_id=user_id,
        job_id=overrides.pop("job_id", "af_test_001"),
        type=overrides.pop("type", "weapon-diagram"),
        source_id=overrides.pop("source_id", "weapon-1"),
        title_id=overrides.pop("title_id", "madden-26"),
        status=overrides.pop("status", "pending"),
        **overrides,
    )
    test_db.add(job)
    await test_db.commit()
    await test_db.refresh(job)
    return job


# ---------------------------------------------------------------------------
# GET /status
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_status_returns_true_when_available(client, monkeypatch):
    async def fake_is_available() -> bool:
        return True

    monkeypatch.setattr(
        animaforge_client_module.AnimaForgeService,
        "is_available",
        staticmethod(fake_is_available),
    )

    resp = await client.get("/api/v1/animaforge/status")
    assert resp.status_code == 200
    assert resp.json() == {"available": True}


@pytest.mark.asyncio
async def test_status_returns_false_when_offline(client, monkeypatch):
    async def fake_is_available() -> bool:
        return False

    monkeypatch.setattr(
        animaforge_client_module.AnimaForgeService,
        "is_available",
        staticmethod(fake_is_available),
    )

    resp = await client.get("/api/v1/animaforge/status")
    assert resp.status_code == 200
    assert resp.json() == {"available": False}


@pytest.mark.asyncio
async def test_status_no_auth_required(client, monkeypatch):
    """The ``/status`` endpoint must be callable without an Authorization header."""
    async def fake_is_available() -> bool:
        return False

    monkeypatch.setattr(
        animaforge_client_module.AnimaForgeService,
        "is_available",
        staticmethod(fake_is_available),
    )

    resp = await client.get("/api/v1/animaforge/status")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /jobs (list)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_jobs_requires_auth(client):
    resp = await client.get("/api/v1/animaforge/jobs")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_list_jobs_empty_for_new_user(client, test_db):
    _, token = await _make_user(
        test_db, email="anima1@example.com", username="anima1"
    )
    resp = await client.get(
        "/api/v1/animaforge/jobs", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["items"] == []


@pytest.mark.asyncio
async def test_list_jobs_returns_user_rows(client, test_db):
    user_id, token = await _make_user(
        test_db, email="anima2@example.com", username="anima2"
    )
    await _seed_job(
        test_db, user_id=user_id, job_id="af_a", type="weapon-diagram"
    )
    await _seed_job(
        test_db, user_id=user_id, job_id="af_b", type="drill-demo"
    )
    # Another user's job — must NOT appear in the list.
    await _seed_job(
        test_db,
        user_id="other-user-id",
        job_id="af_other",
        type="weapon-diagram",
    )

    resp = await client.get(
        "/api/v1/animaforge/jobs", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    job_ids = {item["job_id"] for item in body["items"]}
    assert job_ids == {"af_a", "af_b"}


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_job_returns_terminal_row_without_calling_animaforge(
    client, test_db, monkeypatch
):
    user_id, token = await _make_user(
        test_db, email="anima3@example.com", username="anima3"
    )
    await _seed_job(
        test_db,
        user_id=user_id,
        job_id="af_done",
        status="complete",
        video_url="https://v/done.mp4",
    )

    called = {"n": 0}

    async def fake_status(job_id: str):  # pragma: no cover - shouldn't be reached
        called["n"] += 1
        return {"status": "complete"}

    monkeypatch.setattr(
        animaforge_client_module.AnimaForgeService,
        "get_job_status",
        staticmethod(fake_status),
    )

    resp = await client.get(
        "/api/v1/animaforge/jobs/af_done",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "complete"
    assert body["video_url"] == "https://v/done.mp4"
    assert called["n"] == 0  # terminal — no live fetch


@pytest.mark.asyncio
async def test_get_job_merges_live_status_when_pending(
    client, test_db, monkeypatch
):
    user_id, token = await _make_user(
        test_db, email="anima4@example.com", username="anima4"
    )
    await _seed_job(
        test_db, user_id=user_id, job_id="af_live", status="pending"
    )

    async def fake_status(job_id: str):
        assert job_id == "af_live"
        return {
            "status": "rendering",
            "video_url": None,
            "progress": 42,
        }

    monkeypatch.setattr(
        animaforge_client_module.AnimaForgeService,
        "get_job_status",
        staticmethod(fake_status),
    )

    resp = await client.get(
        "/api/v1/animaforge/jobs/af_live",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "rendering"
    assert body["progress"] == 42


@pytest.mark.asyncio
async def test_get_job_falls_back_when_animaforge_unavailable(
    client, test_db, monkeypatch
):
    from app.services.animaforge import AnimaForgeUnavailable

    user_id, token = await _make_user(
        test_db, email="anima5@example.com", username="anima5"
    )
    await _seed_job(
        test_db, user_id=user_id, job_id="af_pending", status="pending"
    )

    async def fake_status(job_id: str):
        raise AnimaForgeUnavailable("offline")

    monkeypatch.setattr(
        animaforge_client_module.AnimaForgeService,
        "get_job_status",
        staticmethod(fake_status),
    )

    resp = await client.get(
        "/api/v1/animaforge/jobs/af_pending",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    # Falls back to DB status without crashing.
    assert resp.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_get_job_404_for_other_users_job(client, test_db):
    _user_id, token = await _make_user(
        test_db, email="anima6@example.com", username="anima6"
    )
    await _seed_job(
        test_db,
        user_id="some-other-user",
        job_id="af_secret",
        status="complete",
    )

    resp = await client.get(
        "/api/v1/animaforge/jobs/af_secret",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /jobs/{job_id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_job_removes_user_row(client, test_db):
    user_id, token = await _make_user(
        test_db, email="anima7@example.com", username="anima7"
    )
    await _seed_job(test_db, user_id=user_id, job_id="af_kill")

    resp = await client.delete(
        "/api/v1/animaforge/jobs/af_kill",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"deleted": True, "job_id": "af_kill"}

    # Confirm gone
    resp2 = await client.get(
        "/api/v1/animaforge/jobs/af_kill",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_job_404_for_other_users_job(client, test_db):
    _user_id, token = await _make_user(
        test_db, email="anima8@example.com", username="anima8"
    )
    await _seed_job(
        test_db, user_id="another-user", job_id="af_locked", status="complete"
    )

    resp = await client.delete(
        "/api/v1/animaforge/jobs/af_locked",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
