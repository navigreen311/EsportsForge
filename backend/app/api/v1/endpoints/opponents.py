"""Opponent Intelligence API endpoints.

Exposes scouting dossiers, archetype classification, next-call prediction,
rival intelligence, and behavioral signal reading.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.opponent import Opponent
from app.models.user import User
from app.schemas.opponent import (
    Archetype,
    BehavioralSignal,
    CounterPackage,
    OpponentDossier,
    Prediction,
    RivalDossier,
)
from app.services.backbone import (
    archetype_ai,
    behavioral_signal,
    opponent_prediction,
    rival_intelligence,
    scout_bot,
)

router = APIRouter(tags=["opponents"])


# ---------------------------------------------------------------------------
# Schemas — list / create
# ---------------------------------------------------------------------------


class OpponentSummary(BaseModel):
    id: str
    gamertag: str
    title: str
    archetype: str | None
    encounter_count: int
    has_dossier: bool

    model_config = {"from_attributes": False}


class OpponentCreate(BaseModel):
    gamertag: str
    title: str
    archetype: str | None = None


# ---------------------------------------------------------------------------
# List / Create — current user's opponents
# ---------------------------------------------------------------------------


@router.get("/list", response_model=list[OpponentSummary])
async def list_opponents(
    title: str | None = Query(default=None),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[OpponentSummary]:
    """List opponents the user has scouted, optionally filtered by title."""
    stmt = select(Opponent)
    if title:
        stmt = stmt.where(Opponent.title == title)
    stmt = stmt.order_by(Opponent.last_seen_at.desc().nullslast(), Opponent.gamertag.asc())
    rows = list((await db.execute(stmt)).scalars().all())
    return [
        OpponentSummary(
            id=str(r.id),
            gamertag=r.gamertag,
            title=r.title,
            archetype=r.archetype,
            encounter_count=r.encounter_count,
            has_dossier=bool(r.tendencies),
        )
        for r in rows
    ]


@router.post("", response_model=OpponentSummary, status_code=status.HTTP_201_CREATED)
async def create_opponent(
    payload: OpponentCreate,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OpponentSummary:
    """Create a new opponent record. Tendencies start empty until scouted."""
    opp = Opponent(
        gamertag=payload.gamertag,
        title=payload.title,
        archetype=payload.archetype,
        encounter_count=0,
        last_seen_at=datetime.now(timezone.utc),
    )
    db.add(opp)
    await db.flush()
    await db.refresh(opp)
    return OpponentSummary(
        id=str(opp.id),
        gamertag=opp.gamertag,
        title=opp.title,
        archetype=opp.archetype,
        encounter_count=opp.encounter_count,
        has_dossier=False,
    )


# ---------------------------------------------------------------------------
# Scout — populate tendencies via Claude (or deterministic mock)
# ---------------------------------------------------------------------------


import json as _json  # noqa: E402
from app.services.ai.claude_client import ClaudeClient  # noqa: E402

_scout_claude = ClaudeClient()

_SCOUT_SYSTEM = (
    "You are ScoutBot for EsportsForge. Given an opponent's gamertag, archetype, "
    "and any prior tendency observations, build a structured tendency dossier "
    "for use by GameplanAI. Respond with strict JSON only — no markdown."
)


class ScoutResponse(BaseModel):
    opponent: OpponentSummary
    tendencies: dict[str, Any]
    source: str


def _mock_tendencies(archetype: str | None) -> dict[str, Any]:
    arche = (archetype or "").lower()
    if "blitz" in arche or "aggressive" in arche:
        return {
            "topCoverage": "Cover 1 Robber",
            "topCoveragePercent": 47,
            "blitzRate": 58,
            "tendency3": "Pressure 3rd & medium",
            "tendency3Percent": 64,
            "thirdDownPlayCallTrend": ["man-blitz", "double-A-gap", "fire-zone"],
            "redZoneTendency": "Goal-line stand vs run-heavy looks",
            "behavioralSignals": ["Telegraphs blitz with safety creep", "Predictable on 2nd-and-long"],
            "_source": "mock-archetype-heuristic",
        }
    if "zone" in arche or "schemer" in arche:
        return {
            "topCoverage": "Cover 3",
            "topCoveragePercent": 62,
            "blitzRate": 24,
            "tendency3": "Drop 8 on long downs",
            "tendency3Percent": 71,
            "thirdDownPlayCallTrend": ["cover-3-cloud", "tampa-2", "quarters"],
            "redZoneTendency": "Zone shell, dare you to throw the fade",
            "behavioralSignals": ["Rotates safeties late", "Disguises Tampa-2 as Cover-3"],
            "_source": "mock-archetype-heuristic",
        }
    return {
        "topCoverage": "Cover 2",
        "topCoveragePercent": 50,
        "blitzRate": 30,
        "tendency3": "Mixed coverage on 3rd downs",
        "tendency3Percent": 52,
        "thirdDownPlayCallTrend": ["cover-2-zone", "man-free", "cover-3"],
        "redZoneTendency": "Balanced — mixes zone and man",
        "behavioralSignals": ["No strong tells yet — keep scouting"],
        "_source": "mock-archetype-heuristic",
    }


@router.post("/{opponent_id}/scout", response_model=ScoutResponse)
async def scout_opponent(
    opponent_id: str,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScoutResponse:
    """Build (or refresh) a tendency dossier for an opponent and persist it.

    When ANTHROPIC_API_KEY is set, asks Claude to extrapolate from the
    archetype + any prior tendency notes. Otherwise returns a deterministic
    archetype-keyed dossier so the rest of the gameplan flow has something
    to consume.
    """
    result = await db.execute(select(Opponent).where(Opponent.id == opponent_id))
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Opponent not found.")

    if _scout_claude.is_available:
        prompt = _json.dumps({
            "gamertag": opp.gamertag,
            "title": opp.title,
            "archetype": opp.archetype,
            "prior_tendencies": opp.tendencies or {},
            "schema": {
                "topCoverage": "string",
                "topCoveragePercent": "int 0-100",
                "blitzRate": "int 0-100",
                "tendency3": "string",
                "tendency3Percent": "int 0-100",
                "thirdDownPlayCallTrend": ["short strings"],
                "redZoneTendency": "string",
                "behavioralSignals": ["short strings"],
            },
            "instructions": "If you don't know something, write a sensible default and note it as inferred.",
        })
        try:
            data = await _scout_claude.generate_json(
                prompt,
                system=_SCOUT_SYSTEM,
                max_tokens=600,
                temperature=0.4,
            )
            tendencies = {**data, "_source": "claude"}
            source = "claude"
        except Exception as exc:  # noqa: BLE001
            logger.info("ScoutBot fell back to mock: %s", exc)
            tendencies = _mock_tendencies(opp.archetype)
            source = "mock"
    else:
        tendencies = _mock_tendencies(opp.archetype)
        source = "mock"

    opp.tendencies = tendencies
    opp.last_seen_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(opp)

    return ScoutResponse(
        opponent=OpponentSummary(
            id=str(opp.id),
            gamertag=opp.gamertag,
            title=opp.title,
            archetype=opp.archetype,
            encounter_count=opp.encounter_count,
            has_dossier=True,
        ),
        tendencies=tendencies,
        source=source,
    )


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    """Body for the predict endpoint."""
    situation: str
    history: list[dict[str, Any]] | None = None


class SignalsRequest(BaseModel):
    """Query params are simpler but we expose as GET with defaults."""


# ---------------------------------------------------------------------------
# Scout / Dossier
# ---------------------------------------------------------------------------

@router.get(
    "/opponents/{opponent_id}/dossier",
    response_model=OpponentDossier,
    summary="Full scouting dossier",
)
async def get_dossier(
    opponent_id: str,
    title: str = Query(default="madden26", description="Game title"),
):
    """Build and return a full scouting dossier for an opponent."""
    dossier = scout_bot.scout_opponent(opponent_id, title)
    return dossier


# ---------------------------------------------------------------------------
# Archetype
# ---------------------------------------------------------------------------

@router.get(
    "/opponents/{opponent_id}/archetype",
    response_model=Archetype,
    summary="Classify opponent archetype",
)
async def get_archetype(
    opponent_id: str,
    title: str = Query(default="madden26", description="Game title"),
    signals: str = Query(default="", description="Comma-separated trait signals"),
):
    """Classify an opponent into an archetype based on available signals."""
    signal_list = [s.strip() for s in signals.split(",") if s.strip()] if signals else []
    data = {"signals": signal_list, "title": title, "opponent_id": opponent_id}
    archetype = archetype_ai.classify_opponent(data)
    return archetype


@router.get(
    "/opponents/{opponent_id}/archetype/counter",
    response_model=CounterPackage,
    summary="Counter package for opponent archetype",
)
async def get_archetype_counter(
    opponent_id: str,
    title: str = Query(default="madden26"),
    signals: str = Query(default=""),
):
    """Get the counter strategy package for an opponent's archetype."""
    signal_list = [s.strip() for s in signals.split(",") if s.strip()] if signals else []
    data = {"signals": signal_list, "title": title}
    archetype = archetype_ai.classify_opponent(data)
    return archetype_ai.get_counter_package(archetype)


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

@router.post(
    "/opponents/{opponent_id}/predict",
    response_model=Prediction,
    summary="Predict opponent next call",
)
async def predict_next(opponent_id: str, body: PredictRequest):
    """Predict the opponent's next action in the given situation."""
    prediction = opponent_prediction.predict_next_call(
        opponent_id=opponent_id,
        situation=body.situation,
        history=body.history,
    )
    return prediction


# ---------------------------------------------------------------------------
# Rival Intelligence
# ---------------------------------------------------------------------------

@router.get(
    "/rivals/{opponent_id}",
    response_model=RivalDossier,
    summary="Rival dossier",
)
async def get_rival(
    opponent_id: str,
    user_id: str = Query(default="current_user", description="Requesting user ID"),
):
    """Return the deep rival dossier for a repeat opponent."""
    dossier = rival_intelligence.get_rival_dossier(user_id, opponent_id)
    return dossier


# ---------------------------------------------------------------------------
# Behavioral Signals
# ---------------------------------------------------------------------------

@router.get(
    "/opponents/{opponent_id}/signals",
    response_model=list[BehavioralSignal],
    summary="Behavioral signals",
)
async def get_signals(
    opponent_id: str,
    score_differential: int = Query(default=0),
    recent_turnovers: int = Query(default=0),
):
    """Read behavioral signals from the current game state.

    Accepts lightweight query params; in a real integration the full
    game state would come from the live data feed.
    """
    game_state: dict[str, Any] = {
        "opponent_id": opponent_id,
        "score_differential": score_differential,
        "recent_turnovers": recent_turnovers,
    }
    signals = behavioral_signal.read_signals(game_state)
    return signals
