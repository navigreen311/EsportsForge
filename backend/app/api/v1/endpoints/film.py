"""API endpoints for FilmAI, MetaVersion Engine, and Onboarding Intelligence."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.schemas.film import (
    FilmBreakdown,
    FirstGameplan,
    MetaSnapshot,
    MetaVersionStamp,
    OnboardingProfile,
    PatternDetection,
    ReplayAnalysis,
    StaleAdviceAlert,
    TaggedMoment,
)
from app.services.backbone import film_ai, meta_version_engine, onboarding_intelligence

router = APIRouter(tags=["FilmAI / MetaVersion / Onboarding"])


# ── FilmAI ────────────────────────────────────────────────────────────────

@router.post("/film/analyze", response_model=ReplayAnalysis)
async def analyze_replay(payload: dict[str, Any]):
    """Submit replay data for analysis (Phase 1 = manual tags)."""
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    try:
        return film_ai.analyze_replay(user_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/film/{user_id}/patterns", response_model=list[PatternDetection])
async def get_user_patterns(
    user_id: str,
    title: str = Query(..., description="Game title"),
    sessions: int = Query(10, ge=1, le=100, description="Sessions to scan"),
):
    """Detect recurring patterns across recent replays."""
    return film_ai.detect_patterns(user_id, title, sessions)


@router.post("/film/tag", response_model=TaggedMoment)
async def tag_moment(payload: dict[str, Any]):
    """Manually tag a moment in a replay."""
    replay_id = payload.get("replay_id")
    timestamp = payload.get("timestamp")
    tag = payload.get("tag")
    if not all([replay_id, timestamp is not None, tag]):
        raise HTTPException(
            status_code=400,
            detail="replay_id, timestamp, and tag are required",
        )
    return film_ai.tag_moment(
        replay_id=replay_id,
        timestamp=float(timestamp),
        tag=tag,
        notes=payload.get("notes", ""),
    )


@router.get("/film/{replay_id}/breakdown", response_model=FilmBreakdown)
async def get_film_breakdown(replay_id: str):
    """Full film breakdown for a previously-analyzed replay."""
    try:
        return film_ai.generate_breakdown(replay_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── MetaVersion Engine ────────────────────────────────────────────────────

@router.get("/meta-version/{title}/snapshot", response_model=MetaSnapshot)
async def get_meta_snapshot(
    title: str,
    patch_version: str = Query(..., description="Patch version to retrieve"),
):
    """Retrieve a historical meta snapshot for a title + patch."""
    try:
        return meta_version_engine.get_snapshot(title, patch_version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/meta-version/snapshot", response_model=MetaSnapshot)
async def create_meta_snapshot(payload: dict[str, Any]):
    """Create a new meta snapshot."""
    title = payload.get("title")
    patch_version = payload.get("patch_version")
    if not title or not patch_version:
        raise HTTPException(
            status_code=400, detail="title and patch_version are required"
        )
    return meta_version_engine.create_snapshot(
        title=title,
        patch_version=patch_version,
        top_strategies=payload.get("top_strategies", []),
        tier_list=payload.get("tier_list", {}),
        meta_notes=payload.get("meta_notes", ""),
        changelog_notes=payload.get("changelog_notes", []),
    )


@router.post("/meta-version/stamp", response_model=MetaVersionStamp)
async def stamp_recommendation(payload: dict[str, Any]):
    """Stamp a recommendation with patch version info."""
    recommendation = payload.get("recommendation")
    patch_version = payload.get("patch_version")
    title = payload.get("title")
    if not all([recommendation, patch_version, title]):
        raise HTTPException(
            status_code=400,
            detail="recommendation, patch_version, and title are required",
        )
    return meta_version_engine.stamp_recommendation(
        recommendation=recommendation,
        patch_version=patch_version,
        title=title,
    )


@router.post("/meta-version/check-stale", response_model=list[StaleAdviceAlert])
async def check_stale_advice(payload: dict[str, Any]):
    """Detect recommendations that may be stale for the current patch."""
    title = payload.get("title")
    current_patch = payload.get("current_patch")
    if not title or not current_patch:
        raise HTTPException(
            status_code=400, detail="title and current_patch are required"
        )
    return meta_version_engine.detect_stale_advice(title, current_patch)


# ── Onboarding Intelligence ──────────────────────────────────────────────

@router.post("/onboarding/start", response_model=OnboardingProfile)
async def start_onboarding(payload: dict[str, Any]):
    """Begin the onboarding flow for a new user + title."""
    user_id = payload.get("user_id")
    title = payload.get("title")
    if not user_id or not title:
        raise HTTPException(
            status_code=400, detail="user_id and title are required"
        )
    try:
        return onboarding_intelligence.start_onboarding(user_id, title)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/onboarding/session", response_model=OnboardingProfile)
async def process_onboarding_session(payload: dict[str, Any]):
    """Submit a session for onboarding processing (auto-detects which step)."""
    user_id = payload.get("user_id")
    session_data = payload.get("session_data", payload)
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    title = session_data.get("title", "unknown")
    key = (user_id, title)

    # Look up current phase to route to the right processor
    profile = onboarding_intelligence._profiles.get(key)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"No onboarding in progress for user {user_id} in {title}",
        )

    phase = profile.current_phase
    try:
        from app.schemas.film import OnboardingPhase
        if phase == OnboardingPhase.SESSION_1:
            return onboarding_intelligence.process_first_session(user_id, session_data)
        elif phase == OnboardingPhase.SESSION_2:
            return onboarding_intelligence.process_second_session(user_id, session_data)
        elif phase == OnboardingPhase.SESSION_3:
            return onboarding_intelligence.process_third_session(user_id, session_data)
        else:
            raise HTTPException(
                status_code=409,
                detail=f"Onboarding phase '{phase.value}' does not accept sessions",
            )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/onboarding/{user_id}/progress")
async def get_onboarding_progress(
    user_id: str,
    title: str = Query(None, description="Filter by game title"),
):
    """Progress through onboarding steps."""
    return onboarding_intelligence.get_onboarding_progress(user_id, title)


@router.post("/onboarding/{user_id}/gameplan", response_model=FirstGameplan)
async def install_first_gameplan(
    user_id: str,
    title: str = Query(..., description="Game title"),
):
    """Generate the initial gameplan after onboarding completes."""
    try:
        return onboarding_intelligence.install_first_gameplan(user_id, title)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
