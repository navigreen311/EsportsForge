"""Shared fixtures for VAF tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure `app.*` imports resolve from the service root, regardless of where
# pytest is invoked. The service has no top-level package wrapper.
SERVICE_ROOT = Path(__file__).resolve().parent.parent
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))
