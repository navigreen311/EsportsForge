"""ForgeCore Chat endpoint — mock AI chat responses based on keywords."""

from fastapi import APIRouter
from pydantic import BaseModel

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
# Mock response logic
# ---------------------------------------------------------------------------

def _generate_response(message: str, context: str) -> ChatResponse:
    """Return mock responses based on keyword matching."""
    msg_lower = message.lower()

    if "cover 3" in msg_lower or "coverage" in msg_lower:
        return ChatResponse(
            response=(
                "Against Cover 3, I recommend attacking the seams and flats. "
                "The Flood concept (Corner + Flat + Curl) puts the flat defender "
                "in a bind. Your IR data shows you convert 73% of plays using "
                "Gun Bunch Flood Right vs Cover 3. Consider running PA Crossers "
                "on early downs to exploit the soft middle zone."
            ),
            actions=[
                ChatAction(label="View Kill Sheet", route="/gameplan/killsheet"),
                ChatAction(label="Run Drill", route="/drills"),
            ],
        )

    if "gameplan" in msg_lower or "game plan" in msg_lower or "build" in msg_lower:
        return ChatResponse(
            response=(
                "I can help you build a gameplan! Based on your recent opponents, "
                "I suggest focusing on: 1) Quick passes vs blitz-heavy teams, "
                "2) Establishing the run on first down (your success rate is 68%), "
                "3) Using no-huddle after big plays to keep momentum. "
                "Would you like me to generate a full situational gameplan?"
            ),
            actions=[
                ChatAction(label="Go to Gameplan", route="/gameplan"),
                ChatAction(label="View Opponents", route="/opponents"),
            ],
        )

    if "weakness" in msg_lower or "worst" in msg_lower or "struggle" in msg_lower:
        return ChatResponse(
            response=(
                "Based on your ImpactRank analysis, your biggest weakness is "
                "3rd-down conversion rate (currently 38%, league avg is 52%). "
                "Specifically, you struggle on 3rd-and-medium (4-7 yards) where "
                "you tend to force deep routes instead of taking the checkdown. "
                "I recommend the '3rd Down Confidence' drill series to improve."
            ),
            actions=[
                ChatAction(label="View Analytics", route="/analytics"),
                ChatAction(label="Start Drill", route="/drills"),
            ],
        )

    if "tilt" in msg_lower or "mental" in msg_lower or "frustrated" in msg_lower:
        return ChatResponse(
            response=(
                "TiltGuard detected elevated frustration markers in your last "
                "3 sessions. Here are some suggestions: 1) Take a 2-minute break "
                "after consecutive losses, 2) Focus on process goals not outcomes, "
                "3) Use the box-breathing technique (4-4-4-4) between games. "
                "Your win rate drops 23% when playing tilted."
            ),
            actions=[
                ChatAction(label="TiltGuard Settings", route="/settings"),
                ChatAction(label="Mental Drills", route="/drills"),
            ],
        )

    if "meta" in msg_lower or "patch" in msg_lower or "update" in msg_lower:
        return ChatResponse(
            response=(
                "MetaBot Analysis: This week's meta shifts include — "
                "1) Nickel formations are up 15% usage, "
                "2) Play-action is less effective due to run-commit nerfs, "
                "3) Slot corner blitzes are trending in high-ELO matches. "
                "I recommend adjusting your protection schemes and adding "
                "more quick-game concepts to your arsenal."
            ),
            actions=[
                ChatAction(label="View Meta Report", route="/analytics"),
                ChatAction(label="Update Gameplan", route="/gameplan"),
            ],
        )

    # Default response
    return ChatResponse(
        response=(
            f"I'm ForgeCore, your AI competitive gaming assistant. "
            f"I can help with strategy, gameplans, opponent analysis, "
            f"mental performance, and meta insights. "
            f"Currently viewing: {context}. What would you like to know?"
        ),
        actions=[
            ChatAction(label="View Dashboard", route="/dashboard"),
            ChatAction(label="Go to Gameplan", route="/gameplan"),
        ],
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message and return a mock ForgeCore response."""
    return _generate_response(request.message, request.context)
