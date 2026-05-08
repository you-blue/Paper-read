"""OpenAI API provider."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Callable, Coroutine

from openai import AsyncOpenAI

from src.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible provider (supports GPT, Qwen, DeepSeek, Custom).

    Works with any OpenAI-compatible API by setting base_url.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        supports_vision: bool = True,
    ):
        if not api_key:
            raise ValueError("API key is required")
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = AsyncOpenAI(**kwargs)
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._base_url = base_url
        self._supports_vision = supports_vision

    @property
    def name(self) -> str:
        prefix = "Custom" if self._base_url else "GPT"
        return f"{prefix} ({self._model})"

    @property
    def supports_vision(self) -> bool:
        return self._supports_vision

    async def test_connection(self) -> str:
        """Lightweight connection test via model list."""
        await self._client.models.list()
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

        # Build content parts: text + images
        content_parts: list[dict] = [{"type": "text", "text": user_message}]

        for img_path in image_paths:
            if on_progress:
                await on_progress(f"Encoding image: {img_path.name}")
            with open(img_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_data}",
                    "detail": "high",
                },
            })

        if on_progress:
            await on_progress(f"Sending to {self._model}...")

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content_parts},
            ],
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )

        return response.choices[0].message.content or ""
