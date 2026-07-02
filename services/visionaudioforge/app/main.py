"""VisionAudioForge core service entry point.

Run with:
    cd services/visionaudioforge
    uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload

Phase 0 — skeleton. The architecture is real; the inner ML/OCR work is
stubbed until the next session.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api import health, ingest, sessions
from app.core.webhook import publisher

logger = logging.getLogger("vaf.main")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    flush_task = asyncio.create_task(publisher.flush_periodic())
    logger.info("vaf_started", extra={"version": __version__})
    try:
        yield
    finally:
        flush_task.cancel()
        try:
            await flush_task
        except asyncio.CancelledError:
            pass
        logger.info("vaf_stopped")


app = FastAPI(
    title="VisionAudioForge Core",
    version=__version__,
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(ingest.router)
