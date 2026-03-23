"""Thin async wrapper around the Anthropic Python SDK.

Provides a single ``generate`` method that the Madden 26 agents call.
Falls back gracefully when no API key is configured.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Lazy-import so the app boots even when ``anthropic`` is not installed.
try:
    import anthropic  # type: ignore[import-untyped]

    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False


class ClaudeClient:
    """Async Claude API client with graceful fallback."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self._api_key = api_key or settings.anthropic_api_key
        self._model = model or settings.claude_model
        self._client: Any = None

        if self.is_available:
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_available(self) -> bool:
        """Return True when the SDK is installed and a real key is configured."""
        return (
            _HAS_ANTHROPIC
            and bool(self._api_key)
            and self._api_key != "YOUR_ANTHROPIC_API_KEY_HERE"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        system: str = "",
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        """Send a prompt to Claude and return the text response.

        Raises ``RuntimeError`` if called when the client is not available.
        Callers should check ``is_available`` first or use the agent-level
        fallback pattern.
        """
        if not self.is_available or self._client is None:
            raise RuntimeError("Claude client is not available (missing SDK or API key).")

        effective_model = model or self._model
        logger.info("ClaudeClient.generate  model=%s  prompt_len=%d", effective_model, len(prompt))

        message = await self._client.messages.create(
            model=effective_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract text from the response content blocks
        text_parts: list[str] = []
        for block in message.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        return "\n".join(text_parts)

    async def generate_json(
        self,
        prompt: str,
        system: str = "",
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Call ``generate`` and parse the response as JSON.

        The prompt should instruct Claude to reply with valid JSON only.
        """
        raw = await self.generate(
            prompt=prompt,
            system=system,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Strip markdown fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            # Remove opening fence (```json or ```)
            first_newline = cleaned.index("\n")
            cleaned = cleaned[first_newline + 1 :]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        return json.loads(cleaned.strip())
