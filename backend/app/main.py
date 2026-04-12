"""EsportsForge Backend — FastAPI Application Entry Point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from app.core.config import settings
from app.db.base import engine, Base
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import all models so Base.metadata knows about them
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="EsportsForge API",
    description="AI-powered competitive gaming intelligence platform",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix="/api/v1")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    db_status = "connected"
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "esportsforge",
        "database": db_status,
        "environment": settings.environment,
    }


@app.get("/api/v1/status")
async def platform_status():
    """Platform status with backbone system states."""
    return {
        "platform": "EsportsForge",
        "phase": "1-mvp",
        "backbone": {
            "forge_data_fabric": "initializing",
            "forge_core": "initializing",
            "player_twin": "initializing",
            "impact_rank": "initializing",
            "truth_engine": "initializing",
            "loop_ai": "initializing",
        },
        "titles": {
            "madden26": "initializing",
            "cfb26": "initializing",
        },
    }
