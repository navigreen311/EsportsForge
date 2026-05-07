"""Adapter registry — the single dispatch point.

Adding a new title is: drop a new module under adapters/<title>/,
import its adapter class here, register it in ADAPTERS. The core
itself doesn't change. (Rule 5 of the Forge pattern.)
"""

from __future__ import annotations

import logging

from app.adapters.base import TitleAdapter
from app.adapters.madden26 import Madden26Adapter
from app.schemas.enums import TitleEnum

logger = logging.getLogger("vaf.adapters")


_ADAPTER_CLASSES: dict[TitleEnum, type] = {
    TitleEnum.MADDEN26: Madden26Adapter,
    # CFB26: Phase 2.
    # NBA2K26, EAFC26, MLB26: Phase 3.
    # WARZONE, FORTNITE: Phase 4.
    # UFC5, UNDISPUTED: Phase 5.
    # PGA2K25, VIDEO_POKER: Phase 5.
}


# Instantiated lazily on first use; ML models load in __init__ so we
# only pay the cost for adapters that actually run.
_ADAPTER_INSTANCES: dict[TitleEnum, TitleAdapter] = {}


def get_adapter(title: TitleEnum) -> TitleAdapter | None:
    """Return the singleton adapter for a title, or None if not registered."""
    if title not in _ADAPTER_CLASSES:
        return None

    inst = _ADAPTER_INSTANCES.get(title)
    if inst is None:
        cls = _ADAPTER_CLASSES[title]
        inst = cls()
        _ADAPTER_INSTANCES[title] = inst
        logger.info("adapter_loaded", extra={"title": title.value, "version": inst.version})
    return inst


def registered_titles() -> list[TitleEnum]:
    return list(_ADAPTER_CLASSES.keys())
