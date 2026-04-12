"""ForgeCore — Central AI orchestrator wrapping Anthropic Claude API."""

import json
import logging

from anthropic import AsyncAnthropic

from app.core.config import settings
from app.services.ai.prompts import SYSTEM_PROMPTS

logger = logging.getLogger(__name__)


class ForgeCore:
    """Main AI engine that routes queries to Claude with appropriate system prompts."""

    def __init__(self):
        self.client = None
        if settings.anthropic_api_key and "YOUR_" not in settings.anthropic_api_key:
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    async def query(
        self, message: str, context: dict, system_prompt: str | None = None
    ) -> dict:
        """Send a query to Claude or return mock data if no API key configured."""
        if not self.client:
            return self._mock_response(message, context)

        try:
            system = system_prompt or SYSTEM_PROMPTS["default"]
            user_content = f"{message}\n\nContext:\n{json.dumps(context, default=str)}"

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system,
                messages=[{"role": "user", "content": user_content}],
            )

            text = response.content[0].text

            # Try to parse as JSON
            try:
                return {"status": "success", "data": json.loads(text), "source": "claude"}
            except json.JSONDecodeError:
                return {"status": "success", "data": {"response": text}, "source": "claude"}

        except Exception as e:
            logger.error("ForgeCore Claude API error: %s", e)
            return self._mock_response(message, context)

    async def agent_query(self, agent: str, message: str, context: dict) -> dict:
        """Route a query through a specific agent's system prompt."""
        system_prompt = SYSTEM_PROMPTS.get(agent, SYSTEM_PROMPTS["default"])
        return await self.query(message, context, system_prompt=system_prompt)

    def _mock_response(self, message: str, context: dict) -> dict:
        """Return intelligent mock data based on keywords in the message."""
        msg_lower = message.lower()

        if "rank" in msg_lower or "priority" in msg_lower:
            return {
                "status": "mock",
                "data": {
                    "priorities": [
                        {"rank": 1, "area": "coverage_reads", "impact": 0.85, "description": "Improve pre-snap coverage identification"},
                        {"rank": 2, "area": "pocket_movement", "impact": 0.72, "description": "Better pocket presence under pressure"},
                        {"rank": 3, "area": "route_timing", "impact": 0.68, "description": "Throwing timing on deep routes"},
                    ],
                    "confidence": 0.75,
                },
                "source": "mock",
            }

        if "gameplan" in msg_lower or "plan" in msg_lower:
            return {
                "status": "mock",
                "data": {
                    "plays": [
                        {"order": i, "play": f"Play_{i}", "formation": "Shotgun", "concept": "Quick read", "reason": "Exploits tendency"}
                        for i in range(1, 11)
                    ],
                    "adjustments": ["If blitz heavy, audible to hot routes", "If cover 3, attack seams"],
                    "confidence": 0.70,
                },
                "source": "mock",
            }

        if "scout" in msg_lower or "opponent" in msg_lower:
            return {
                "status": "mock",
                "data": {
                    "gamertag": context.get("gamertag", "Unknown"),
                    "tendencies": {"aggressive": 0.7, "conservative": 0.3},
                    "weaknesses": ["struggles vs zone pressure", "poor audible usage"],
                    "strengths": ["quick passing game", "run-after-catch"],
                    "kill_sheet": ["Blitz from edge on 3rd down", "Cover 4 on early downs"],
                    "confidence": 0.65,
                },
                "source": "mock",
            }

        if "drill" in msg_lower or "training" in msg_lower:
            return {
                "status": "mock",
                "data": {
                    "drills": [
                        {"name": "Coverage Read Drill", "duration_min": 10, "focus": "pre-snap reads", "difficulty": "medium"},
                        {"name": "Pocket Escape Drill", "duration_min": 8, "focus": "scramble timing", "difficulty": "hard"},
                        {"name": "Route Timing Drill", "duration_min": 12, "focus": "throw timing", "difficulty": "medium"},
                    ],
                    "total_time_min": 30,
                    "confidence": 0.72,
                },
                "source": "mock",
            }

        if "adapt" in msg_lower or "adjust" in msg_lower:
            return {
                "status": "mock",
                "data": {
                    "adjustment": "Switch to quick passing game — opponent is sending 5+ rushers",
                    "reasoning": "Blitz heavy opponents are vulnerable to quick slants and screens",
                    "plays_to_add": ["HB Screen", "Quick Slant", "Drag Route"],
                    "plays_to_remove": ["Deep Post", "PA Boot"],
                    "confidence": 0.78,
                },
                "source": "mock",
            }

        if "meta" in msg_lower:
            return {
                "status": "mock",
                "data": {
                    "meta_ratings": {
                        "top_strategies": ["Gun Bunch", "Pistol Strong", "Nickel 3-3-5"],
                        "patch_impact": "medium",
                        "shifts": ["Zone coverage buffed", "Man press nerfed"],
                    },
                    "confidence": 0.80,
                },
                "source": "mock",
            }

        if "tilt" in msg_lower or "mental" in msg_lower:
            return {
                "status": "mock",
                "data": {
                    "tilt_level": "low",
                    "status": "focused",
                    "intervention": None,
                    "recommendation": "Continue playing — mental state is stable",
                    "confidence": 0.82,
                },
                "source": "mock",
            }

        if "clock" in msg_lower or "time" in msg_lower:
            return {
                "status": "mock",
                "data": {
                    "decision": "Run the ball to burn clock",
                    "reasoning": "Up 7 with 2 minutes left — protect the lead",
                    "urgency": "high",
                    "confidence": 0.88,
                },
                "source": "mock",
            }

        if "loop" in msg_lower or "feedback" in msg_lower:
            return {
                "status": "mock",
                "data": {
                    "model_updated": True,
                    "accuracy_change": 0.02,
                    "new_accuracy": 0.77,
                    "insight": "Recommendation followed successfully — reinforcing pattern",
                    "confidence": 0.75,
                },
                "source": "mock",
            }

        if "confidence" in msg_lower:
            return {
                "status": "mock",
                "data": {
                    "confidence_pct": 72,
                    "factors": {
                        "data_quality": 0.8,
                        "sample_size_factor": 0.65,
                        "recency": 0.7,
                    },
                    "recommendation_reliable": True,
                },
                "source": "mock",
            }

        if "narrative" in msg_lower or "story" in msg_lower:
            return {
                "status": "mock",
                "data": {
                    "narrative": "This week you showed marked improvement in pre-snap reads, correctly identifying coverage 73% of the time (up from 61%). Your pocket presence remains an area of growth.",
                    "highlights": ["Coverage read accuracy +12%", "Win rate improved to 58%"],
                    "areas_to_watch": ["Deep ball accuracy", "4th quarter decision making"],
                    "confidence": 0.70,
                },
                "source": "mock",
            }

        # Default fallback
        return {
            "status": "mock",
            "data": {
                "response": "ForgeCore is analyzing your request. Configure ANTHROPIC_API_KEY for live AI responses.",
                "context_received": list(context.keys()),
            },
            "source": "mock",
        }


# Singleton instance
forgecore = ForgeCore()
