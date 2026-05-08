"""Anthropic Claude API provider."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Callable, Coroutine

from anthropic import AsyncAnthropic

from src.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Claude API provider with vision support."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 8192,
        temperature: float = 0.3,
    ):
        if not api_key:
            raise ValueError("Anthropic API key is required")
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    @property
    def name(self) -> str:
        return f"Claude ({self._model})"

    @property
    def supports_vision(self) -> bool:
        return True

    async def test_connection(self) -> str:
        """Lightweight connection test for Claude API."""
        await self._client.messages.create(
            model=self._model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Reply OK"}],
        )
        return "Connected successfully!"

    async def summarize(
        self,
        paper_text: str,
        image_paths: list[Path],
        system_prompt: str,
        user_message: str,
        on_progress: Callable[[str], Coroutine] | None = None,
    ) -> str:
        if on_progress:
            await on_progress("Building message with images...")

        # Build content blocks
        content_blocks: list[dict] = [{"type": "text", "text": user_message}]

        # Append images as base64 content blocks
        for img_path in image_paths:
            if on_progress:
                await on_progress(f"Encoding image: {img_path.name}")
            with open(img_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            content_blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_data,
                },
            })

        if on_progress:
            await on_progress(f"Sending to {self._model}...")

        response = await self._client.messages.create(
            model=self._model,
            system=system_prompt,
            messages=[{"role": "user", "content": content_blocks}],
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )

        # Extract text from response
        result_parts: list[str] = []
        for block in response.content:
            if block.type == "text":
                result_parts.append(block.text)

        return "\n".join(result_parts)
