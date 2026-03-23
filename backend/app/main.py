"""EsportsForge Backend — FastAPI Application Entry Point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title="EsportsForge API",
    description="AI-powered competitive gaming intelligence platform",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0", "service": "esportsforge"}


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
