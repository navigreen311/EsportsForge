"""AI Agent endpoints — ForgeCore-powered intelligence services."""

from fastapi import APIRouter

from app.schemas.ai import (
    ImpactRankRequest, ImpactRankResponse,
    GameplanRequest, GameplanResponse,
    ScoutRequest, ScoutResponse,
    DrillBotRequest, DrillBotResponse,
    AdaptRequest, AdaptResponse,
    MetaRequest, MetaResponse,
    TiltGuardRequest, TiltGuardResponse,
    ClockRequest, ClockResponse,
    LoopRequest, LoopResponse,
    ConfidenceRequest, ConfidenceResponse,
    NarrativeRequest, NarrativeResponse,
)
from app.services.ai.forgecore import forgecore

router = APIRouter()


@router.post("/impactrank", response_model=ImpactRankResponse)
async def impact_rank(request: ImpactRankRequest):
    """Rank improvement priorities by competitive impact."""
    result = await forgecore.agent_query(
        agent="impactrank",
        message="Rank these weaknesses by competitive impact and provide prioritized improvement areas.",
        context=request.model_dump(),
    )
    return result


@router.post("/gameplan", response_model=GameplanResponse)
async def gameplan(request: GameplanRequest):
    """Generate a 10-play gameplan tailored to opponent weaknesses."""
    result = await forgecore.agent_query(
        agent="gameplan",
        message="Build a 10-play gameplan to exploit this opponent's weaknesses.",
        context=request.model_dump(),
    )
    return result


@router.post("/scout", response_model=ScoutResponse)
async def scout(request: ScoutRequest):
    """Scout an opponent and produce a dossier with kill sheet."""
    result = await forgecore.agent_query(
        agent="scout",
        message="Scout this opponent and produce a full dossier with tendencies, weaknesses, and kill sheet.",
        context=request.model_dump(),
    )
    return result


@router.post("/drillbot", response_model=DrillBotResponse)
async def drillbot(request: DrillBotRequest):
    """Generate a targeted drill queue based on weaknesses."""
    result = await forgecore.agent_query(
        agent="drillbot",
        message="Create a targeted drill queue to address these weaknesses at current mastery levels.",
        context=request.model_dump(),
    )
    return result


@router.post("/adapt", response_model=AdaptResponse)
async def adapt(request: AdaptRequest):
    """Provide real-time tactical adjustments based on in-game events."""
    result = await forgecore.agent_query(
        agent="adapt",
        message="Provide tactical adjustments based on what just happened in the game.",
        context=request.model_dump(),
    )
    return result


@router.post("/meta", response_model=MetaResponse)
async def meta(request: MetaRequest):
    """Analyze current meta ratings for a title and patch."""
    result = await forgecore.agent_query(
        agent="meta",
        message="Analyze the current meta for this title and patch version.",
        context=request.model_dump(),
    )
    return result


@router.post("/tiltguard", response_model=TiltGuardResponse)
async def tiltguard(request: TiltGuardRequest):
    """Assess mental state and recommend interventions if needed."""
    result = await forgecore.agent_query(
        agent="tiltguard",
        message="Assess this player's mental state and determine if intervention is needed.",
        context=request.model_dump(),
    )
    return result


@router.post("/clock", response_model=ClockResponse)
async def clock(request: ClockRequest):
    """Provide situational clock management decisions."""
    result = await forgecore.agent_query(
        agent="clock",
        message="Provide clock management advice for this game situation.",
        context=request.model_dump(),
    )
    return result


@router.post("/loop", response_model=LoopResponse)
async def loop(request: LoopRequest):
    """Process feedback to update AI model accuracy."""
    result = await forgecore.agent_query(
        agent="loop",
        message="Process this feedback loop — was the recommendation followed and what was the outcome?",
        context=request.model_dump(),
    )
    return result


@router.post("/confidence", response_model=ConfidenceResponse)
async def confidence(request: ConfidenceRequest):
    """Calculate confidence percentage for a recommendation."""
    result = await forgecore.agent_query(
        agent="confidence",
        message="Calculate confidence percentage for this recommendation given the data source and sample size.",
        context=request.model_dump(),
    )
    return result


@router.post("/narrative", response_model=NarrativeResponse)
async def narrative(request: NarrativeRequest):
    """Generate a weekly performance narrative."""
    result = await forgecore.agent_query(
        agent="narrative",
        message="Craft a weekly narrative summarizing this player's progress and story.",
        context=request.model_dump(),
    )
    return result
