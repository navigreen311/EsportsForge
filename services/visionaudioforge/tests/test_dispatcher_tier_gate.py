"""Tier-aware budget gate in the dispatcher (M5c sub-task 7.5.3, ADR 0015).

A hot-path frame (no OCR) over 80ms drops; a sampled OCR-tier frame is allowed
its own ~500ms budget and is NOT dropped for merely exceeding the hot-path
budget — otherwise every event-producing frame would be dropped (the Phase 0
zero-events failure)."""

import time

import numpy as np

from app.core.dispatcher import Dispatcher
from app.core.session import SessionContext
from app.schemas.enums import IntegrityMode, TitleEnum

FRAME = np.zeros((120, 200, 3), dtype=np.uint8)


class _FakeAdapter:
    title = TitleEnum.MADDEN26
    version = "fake@0"
    max_processing_ms = 80
    max_ocr_tier_ms = 500
    integrity_rules: dict = {}

    def __init__(self, tier: str, sleep_ms: float):
        self._tier = tier
        self._sleep = sleep_ms / 1000.0

    def process_frame(self, frame, session):
        session.adapter_state["_last_tier"] = self._tier
        if self._sleep:
            time.sleep(self._sleep)
        return ["EVENT"]


def _dispatch(monkeypatch, adapter):
    session = SessionContext.open("s", "u", IntegrityMode.OFFLINE_LAB)
    session.title = TitleEnum.MADDEN26          # skip title detection
    monkeypatch.setattr("app.adapters.registry.get_adapter", lambda title: adapter)
    disp = Dispatcher(session)
    return disp, disp.process_frame(FRAME)


def test_hot_frame_under_budget_passes(monkeypatch):
    disp, events = _dispatch(monkeypatch, _FakeAdapter("hot", 0))
    assert events == ["EVENT"]
    assert disp.latency_by_tier["hot"] and not disp.latency_by_tier["ocr"]


def test_ocr_tier_frame_over_hot_budget_is_NOT_dropped(monkeypatch):
    # ~150ms: over the 80ms hot budget, under the 500ms OCR budget.
    disp, events = _dispatch(monkeypatch, _FakeAdapter("ocr", 150))
    assert events == ["EVENT"]                  # the key fix: OCR frames survive
    assert disp.latency_by_tier["ocr"]


def test_hot_frame_over_budget_is_dropped(monkeypatch):
    # ~150ms on the hot path is a genuine "behind real time" breach -> drop.
    disp, events = _dispatch(monkeypatch, _FakeAdapter("hot", 150))
    assert events == []
