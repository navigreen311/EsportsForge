"""ForgeCore Chat endpoint — real Claude API integration via ForgeCore."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ai.forgecore import forgecore

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    context: str = "dashboard"


class ChatAction(BaseModel):
    label: str
    route: str


class ChatResponse(BaseModel):
    response: str
    actions: list[ChatAction] = []


# ---------------------------------------------------------------------------
# Action generation helpers
# ---------------------------------------------------------------------------

ACTION_KEYWORDS: list[tuple[str, ChatAction]] = [
    ("gameplan", ChatAction(label="Go to Gameplan", route="/gameplan")),
    ("game plan", ChatAction(label="Go to Gameplan", route="/gameplan")),
    ("drill", ChatAction(label="Start Drill", route="/drills")),
    ("training", ChatAction(label="Start Drill", route="/drills")),
    ("opponent", ChatAction(label="View Opponents", route="/opponents")),
    ("scout", ChatAction(label="View Opponents", route="/opponents")),
    ("analytics", ChatAction(label="View Analytics", route="/analytics")),
    ("meta", ChatAction(label="View Meta Report", route="/analytics")),
    ("tilt", ChatAction(label="TiltGuard Settings", route="/settings")),
    ("mental", ChatAction(label="TiltGuard Settings", route="/settings")),
    ("kill sheet", ChatAction(label="View Kill Sheet", route="/gameplan/killsheet")),
]


def _build_actions(response_text: str) -> list[ChatAction]:
    """Generate action buttons based on keywords found in the AI response."""
    text_lower = response_text.lower()
    seen_routes: set[str] = set()
    actions: list[ChatAction] = []
    for keyword, action in ACTION_KEYWORDS:
        if keyword in text_lower and action.route not in seen_routes:
            actions.append(action)
            seen_routes.add(action.route)
    return actions


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = (
    "You are ForgeCore, the master AI orchestrator for EsportsForge competitive gaming platform.\n"
    "Current page context: {context}\n"
    "Always give ONE decisive recommendation. Never hedge. Be a war room advisor, not a coach.\n"
    "Keep responses under 150 words unless a detailed breakdown is explicitly requested.\n"
    "If the question is about strategy, give gameplan advice.\n"
    "If about an opponent, give scouting advice.\n"
    "If about mental state, give TiltGuard advice.\n"
    "If about meta/patches, give MetaBot advice.\n"
    "Respond in plain text, not JSON."
)


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message through ForgeCore (Claude API)."""
    ctx = {
        "page": request.context,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=json.dumps(ctx, default=str))

    result = await forgecore.query(
        message=request.message,
        context=ctx,
        system_prompt=system_prompt,
    )

    # Extract text from ForgeCore result
    data = result.get("data", {})
    if "response" in data:
        text = data["response"]
    else:
        # Stringify the data dict for non-response payloads
        text = " ".join(str(v) for v in data.values())

    actions = _build_actions(text)

    return ChatResponse(response=text, actions=actions)
