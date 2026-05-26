"""Anthropic API wrapper for seeding and combination engine."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

from anthropic import AsyncAnthropic, Anthropic


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0

    def add(self, other: TokenUsage) -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class AnthropicUsageTracker:
    usage: TokenUsage = field(default_factory=TokenUsage)
    model: str = "claude-sonnet-4-6"

    # Approximate pricing per million tokens (Sonnet 4.6 — adjust if pricing changes)
    INPUT_COST_PER_M: float = 3.0
    OUTPUT_COST_PER_M: float = 15.0

    def record(self, input_tokens: int, output_tokens: int) -> None:
        self.usage.input_tokens += input_tokens
        self.usage.output_tokens += output_tokens

    def estimated_cost_usd(self) -> float:
        inp = self.usage.input_tokens / 1_000_000 * self.INPUT_COST_PER_M
        out = self.usage.output_tokens / 1_000_000 * self.OUTPUT_COST_PER_M
        return round(inp + out, 4)


def get_model_name() -> str:
    return (
        os.environ.get("ANTHROPIC_MODEL")
        or os.environ.get("SEED_MODEL")  # backward compatible
        or "claude-sonnet-4-6"
    )


def get_combination_model_name() -> str:
    return os.environ.get("COMBINATION_MODEL") or get_model_name()


def strip_json_fences(text: str) -> str:
    """Remove markdown code fences if the model wraps JSON despite instructions."""
    text = text.strip()
    fence_match = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```$", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return text


def parse_json_response(text: str) -> dict:
    cleaned = strip_json_fences(text)
    return json.loads(cleaned)


class AnthropicService:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ["ANTHROPIC_API_KEY"]
        self.model = model or get_model_name()
        self.client = Anthropic(api_key=self.api_key)
        self.async_client = AsyncAnthropic(api_key=self.api_key)
        self.tracker = AnthropicUsageTracker(model=self.model)

    def complete_json(self, system: str, user: str, max_tokens: int = 8192) -> dict:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        self.tracker.record(response.usage.input_tokens, response.usage.output_tokens)
        text = response.content[0].text
        return parse_json_response(text)

    async def complete_json_async(self, system: str, user: str, max_tokens: int = 8192) -> dict:
        response = await self.async_client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        self.tracker.record(response.usage.input_tokens, response.usage.output_tokens)
        text = response.content[0].text
        return parse_json_response(text)
