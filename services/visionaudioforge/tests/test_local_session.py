"""Tests for local single-session mode (make-it-mine #2).

When VAF_LOCAL_SESSION=true, /api/v1/sessions/open returns ONE fixed id via
get-or-create, so every browser surface + the capture agent converge on the
same session with no manual pin. When the flag is off, the real multi-user
fresh-ULID-per-open path must be completely untouched.
"""

from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

# conftest.py puts the service root on sys.path.
from app.core.session import (
    LOCAL_SESSION_ID_DEFAULT,
    SessionRegistry,
    local_session_enabled,
    local_session_id,
)
from app.main import app
from app.schemas.enums import IntegrityMode

OPEN_BODY = {"user_id": "founder", "integrity_mode": "offline_lab", "active_title": "madden26"}


# --- registry.open_or_get: idempotent, state-preserving ---------------------


def test_open_or_get_returns_same_context_and_preserves_state():
    async def scenario():
        reg = SessionRegistry()
        first = await reg.open_or_get("ses_fixed", "u1", IntegrityMode.OFFLINE_LAB)
        first.frame_count = 42
        first.adapter_state["k"] = "v"
        second = await reg.open_or_get("ses_fixed", "u1", IntegrityMode.OFFLINE_LAB)
        return reg, first, second

    reg, first, second = asyncio.run(scenario())
    assert second is first  # same object, not a fresh one
    assert second.frame_count == 42  # in-flight state not wiped
    assert second.adapter_state["k"] == "v"
    assert reg.active_count() == 1  # not duplicated


def test_open_still_clobbers_by_design():
    # The plain open() path (real multi-user) intentionally creates fresh state.
    async def scenario():
        reg = SessionRegistry()
        a = await reg.open("ses_x", "u1", IntegrityMode.OFFLINE_LAB)
        a.frame_count = 7
        b = await reg.open("ses_x", "u1", IntegrityMode.OFFLINE_LAB)
        return a, b

    a, b = asyncio.run(scenario())
    assert b is not a
    assert b.frame_count == 0


# --- flag helpers -----------------------------------------------------------


def test_flag_helpers(monkeypatch):
    monkeypatch.delenv("VAF_LOCAL_SESSION", raising=False)
    monkeypatch.delenv("VAF_LOCAL_SESSION_ID", raising=False)
    assert local_session_enabled() is False
    assert local_session_id() == LOCAL_SESSION_ID_DEFAULT

    monkeypatch.setenv("VAF_LOCAL_SESSION", "true")
    monkeypatch.setenv("VAF_LOCAL_SESSION_ID", "ses_custom")
    assert local_session_enabled() is True
    assert local_session_id() == "ses_custom"

    # Only the exact string "true" enables it.
    monkeypatch.setenv("VAF_LOCAL_SESSION", "1")
    assert local_session_enabled() is False


# --- endpoint behaviour -----------------------------------------------------


def test_open_endpoint_local_mode_returns_fixed_id_twice(monkeypatch):
    monkeypatch.setenv("VAF_LOCAL_SESSION", "true")
    monkeypatch.delenv("VAF_LOCAL_SESSION_ID", raising=False)
    client = TestClient(app)

    r1 = client.post("/api/v1/sessions/open", json=OPEN_BODY)
    r2 = client.post("/api/v1/sessions/open", json=OPEN_BODY)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["session_id"] == LOCAL_SESSION_ID_DEFAULT
    assert r2.json()["session_id"] == LOCAL_SESSION_ID_DEFAULT  # shared, not fresh


def test_open_endpoint_default_mode_mints_fresh_ulids(monkeypatch):
    monkeypatch.delenv("VAF_LOCAL_SESSION", raising=False)
    client = TestClient(app)

    r1 = client.post("/api/v1/sessions/open", json=OPEN_BODY)
    r2 = client.post("/api/v1/sessions/open", json=OPEN_BODY)
    assert r1.status_code == 200 and r2.status_code == 200
    s1, s2 = r1.json()["session_id"], r2.json()["session_id"]
    assert s1 != s2  # real path untouched: fresh id per open
    assert s1.startswith("ses_") and s2.startswith("ses_")
