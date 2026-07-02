"""Title-agnostic temporal smoother (M5c sub-task 6).

Closes the M4.5 field_position gap (single-frame OCR errors) and stabilises the
OCR-of-overlay formation reads, and does so for every future title adapter — the
engine lives in core/ and is driven by a per-adapter smoothing_schema (Forge
Rule 5: adapters add smoothing config, not core code).

The categorical-vs-numeric pattern
----------------------------------
Two value families, aggregated differently across a rolling per-field window:

  * CATEGORICAL -> mode (majority vote). Classifier/label outputs prone to
    single-frame errors: formation, possession, down. A stray misread is
    outvoted by the surrounding frames.
  * NUMERIC -> median. OCR numeric readings with a bounded change rate:
    field_position, distance, score, play_clock. The median ignores a single
    outlier misread; the returned value keeps its original string formatting
    (e.g. "+41", "OPP_22") by picking the buffered value nearest the median.

A `string_clock` kind is a categorical-style mode over "M:SS" strings (a
monotonically-decreasing value where mode-of-window trails by <=1 frame — below
human perception; see ADR references in the methodology doc).

Context-switch reset (shared by all kinds)
------------------------------------------
Every field carries a context tag. When it changes — e.g. the HUD flips between
`live_gameplay` and `play_call` — that field's window is CLEARED, so values are
never smoothed across a context boundary (you must not mode-vote a formation
across a play-call<->gameplay switch). Sub-task 6.5 validates this explicitly.

Future title adapters: CFB 26 formation classifier -> categorical mode; NBA 2K26
play concepts -> categorical; EA FC 26 tactical formation -> categorical. Same
engine, different schema.
"""

from __future__ import annotations

import re
import statistics
from collections import Counter
from dataclasses import dataclass, field as _dc_field
from typing import Any

CATEGORICAL = "categorical"
NUMERIC = "numeric"
STRING_CLOCK = "string_clock"


def _to_number(value: Any) -> float | None:
    """Extract a signed number from an int/float or a string like '+41'/'OPP_22'."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        m = re.search(r"-?\d+", value)
        if m:
            return float(m.group())
    return None


def _aggregate(kind: str, buf: list[Any]) -> Any:
    if not buf:
        return None
    if kind == CATEGORICAL or kind == STRING_CLOCK:
        return Counter(buf).most_common(1)[0][0]
    if kind == NUMERIC:
        nums = [n for n in (_to_number(v) for v in buf) if n is not None]
        if not nums:
            return buf[-1]
        med = statistics.median(nums)
        # keep original formatting: buffered value whose number is nearest median
        return min(buf, key=lambda v: abs((_to_number(v) if _to_number(v) is not None else 1e18) - med))
    return buf[-1]


@dataclass
class _FieldWindow:
    context: str
    buf: list[Any] = _dc_field(default_factory=list)


class TemporalSmoother:
    """Per-(session,field) rolling smoother. One instance per session.

    smooth() is called each frame with the raw field value and its per-field
    config; it returns the smoothed value (or passes the raw value through until
    the window has >= min_window samples). None values are not buffered (a frame
    that couldn't read a field doesn't dilute the window) but still return the
    current smoothed estimate once warm.
    """

    def __init__(self) -> None:
        self._windows: dict[str, _FieldWindow] = {}

    def smooth(self, field: str, value: Any, *, kind: str, window: int,
               min_window: int = 1, context: str = "default") -> Any:
        fw = self._windows.get(field)
        if fw is None or fw.context != context:
            fw = _FieldWindow(context=context)      # context switch -> reset
            self._windows[field] = fw
        if value is not None:
            fw.buf.append(value)
            while len(fw.buf) > window:
                fw.buf.pop(0)
        if len(fw.buf) < min_window:
            return value                            # warming up -> pass through
        agg = _aggregate(kind, fw.buf)
        return agg if agg is not None else value

    def reset(self, field: str | None = None) -> None:
        """Clear one field's window, or all of them (e.g. on session teardown)."""
        if field is None:
            self._windows.clear()
        else:
            self._windows.pop(field, None)

    def current_context(self, field: str) -> str | None:
        fw = self._windows.get(field)
        return fw.context if fw else None

    def samples(self, field: str) -> int:
        """Number of buffered samples for a field (0 if unseen)."""
        fw = self._windows.get(field)
        return len(fw.buf) if fw else 0


def apply_schema(smoother: TemporalSmoother, values: dict[str, Any],
                 schema: dict[str, dict], context: str) -> dict[str, Any]:
    """Smooth a dict of raw field values per an adapter's smoothing_schema.

    Fields absent from the schema pass through unchanged. This is the generic
    entry point an adapter (or the dispatcher) calls each frame; it keeps the
    engine title-agnostic — only the schema is per-title.
    """
    out = dict(values)
    for fld, cfg in schema.items():
        if fld in out:
            out[fld] = smoother.smooth(
                fld, out[fld], kind=cfg["kind"], window=cfg["window"],
                min_window=cfg.get("min_window", 1), context=context,
            )
    return out
