"""Guard: OpenSessionRequest carries no per-session webhook_url (Finding 1).

Core routes webhooks GLOBALLY via one publisher targeting ESF_BACKEND_URL
(app/core/webhook.py) — there is no per-session routing. A `webhook_url` field
on the open-session request was dead/ignored and implied routing that doesn't
exist; it was removed. This test guards against it creeping back.
"""

from __future__ import annotations

from app.api.sessions import OpenSessionRequest


def test_open_session_request_has_no_webhook_url():
    assert "webhook_url" not in OpenSessionRequest.model_fields
