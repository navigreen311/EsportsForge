"""Anthropic Claude API client wrapper with retry, rate-limiting, and token tracking.

Usage::

    from app.services.ai.claude_client import ClaudeClient
    client = ClaudeClient()
    result = await client.generate("Tell me about esports strategy")
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import anthropic
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Token usage tracker
# ---------------------------------------------------------------------------

@dataclass
class TokenUsage:
    """Cumulative token usage across all calls."""

    total_input: int = 0
    total_output: int = 0
    call_count: int = 0
    _history: list[dict[str, Any]] = field(default_factory=list)

    def record(self, input_tokens: int, output_tokens: int, model: str) -> None:
        self.total_input += input_tokens
        self.total_output += output_tokens
        self.call_count += 1
        self._history.append(
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": model,
                "timestamp": time.time(),
            }
        )

    @property
    def total_tokens(self) -> int:
        return self.total_input + self.total_output

    def summary(self) -> dict[str, Any]:
        return {
            "total_input": self.total_input,
            "total_output": self.total_output,
            "total_tokens": self.total_tokens,
            "call_count": self.call_count,
        }


# ---------------------------------------------------------------------------
# Simple rate limiter (token bucket)
# ---------------------------------------------------------------------------

class _RateLimiter:
    """Lightweight token-bucket rate limiter for API calls."""

    def __init__(self, max_calls: int = 50, period: float = 60.0) -> None:
        self._max_calls = max_calls
        self._period = period
        self._timestamps: list[float] = []

    def acquire(self) -> None:
        """Block-free check; raises if limit exceeded."""
        now = time.time()
        self._timestamps = [t for t in self._timestamps if now - t < self._period]
        if len(self._timestamps) >= self._max_calls:
            raise anthropic.RateLimitError(
                message="Local rate limit exceeded",
                response=None,  # type: ignore[arg-type]
                body=None,
            )
        self._timestamps.append(now)


# ---------------------------------------------------------------------------
# Retry predicate — retry on transient errors only
# ---------------------------------------------------------------------------
_RETRYABLE = (
    anthropic.RateLimitError,
    anthropic.APIConnectionError,
    anthropic.InternalServerError,
)

# ---------------------------------------------------------------------------
# Claude Client
# ---------------------------------------------------------------------------

class ClaudeClient:
    """Async wrapper around the Anthropic Messages API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_calls_per_minute: int = 50,
    ) -> None:
        self._api_key = api_key or settings.anthropic_api_key
        self._model = model or settings.claude_model
        self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        self._rate_limiter = _RateLimiter(max_calls=max_calls_per_minute)
        self.usage = TokenUsage()

    # -- core call -----------------------------------------------------------

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        """Send a single prompt to Claude and return the text response."""
        model = model or self._model
        self._rate_limiter.acquire()

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        logger.debug("claude.request", model=model, prompt_len=len(prompt))
        response = await self._client.messages.create(**kwargs)

        # Track tokens
        self.usage.record(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=model,
        )

        text = response.content[0].text
        logger.debug(
            "claude.response",
            model=model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        return text

    # -- structured JSON output ----------------------------------------------

    async def generate_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Call Claude and parse the response as JSON.

        The system prompt should instruct the model to respond with valid JSON.
        We strip markdown fences if present, then parse.
        """
        raw = await self.generate(
            prompt, system=system, model=model,
            max_tokens=max_tokens, temperature=temperature,
        )
        return self._parse_json(raw)

    # -- high-level convenience methods --------------------------------------

    async def analyze(
        self,
        context: dict[str, Any],
        question: str,
    ) -> dict[str, Any]:
        """Analysis-focused call: provide context and a question, get JSON back."""
        system = (
            "You are an expert esports analyst. Analyze the provided context "
            "and answer the question. Respond with valid JSON only — no markdown "
            "fences, no extra text."
        )
        prompt = json.dumps({"context": context, "question": question})
        return await self.generate_json(prompt, system=system)

    async def decide(
        self,
        options: list[str],
        context: dict[str, Any],
        criteria: str,
    ) -> dict[str, Any]:
        """Decision-focused call: evaluate options against criteria, return JSON."""
        system = (
            "You are a decision-making AI for competitive esports. Evaluate the "
            "options against the given criteria and context. Respond with valid JSON:\n"
            '{"chosen": "<option>", "reasoning": "<why>", "confidence": <0-1>, '
            '"ranking": [{"option": "<name>", "score": <0-1>}]}'
        )
        prompt = json.dumps({
            "options": options,
            "context": context,
            "criteria": criteria,
        })
        return await self.generate_json(prompt, system=system)

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        """Parse JSON from Claude response, stripping markdown fences if present."""
        text = raw.strip()
        # Strip ```json ... ``` wrappers
        if text.startswith("```"):
            lines = text.split("\n")
            # Drop first and last fence lines
            lines = [ln for ln in lines if not ln.strip().startswith("```")]
            text = "\n".join(lines)
        return json.loads(text)
