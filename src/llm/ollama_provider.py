"""Ollama local model provider."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Callable, Coroutine

import httpx

from src.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    """Ollama provider for local LLMs.

    Supports vision models (e.g., llama3.2-vision, llava) and text-only models.
    For text-only models, images are silently dropped.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2-vision:latest",
        keep_alive: str = "5m",
        options: dict[str, Any] | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._keep_alive = keep_alive
        self._options = options or {}

    @property
    def name(self) -> str:
        return f"Ollama ({self._model})"

    @property
    def supports_vision(self) -> bool:
        return True

    async def test_connection(self) -> str:
        """Lightweight connection test for Ollama."""
        if not await self._check_available():
            raise ConnectionError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Make sure the Ollama server is running."
            )
        return f"Connected to Ollama at {self._base_url}"

    async def _check_available(self) -> bool:
        """Check if Ollama server is running."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except httpx.RequestError:
            return False

    async def summarize(
        self,
        paper_text: str,
        image_paths: list[Path],
        system_prompt: str,
        user_message: str,
        on_progress: Callable[[str], Coroutine] | None = None,
    ) -> str:
        if on_progress:
            await on_progress("Checking Ollama server...")

        if not await self._check_available():
            raise ConnectionError(
                "Ollama server is not running. "
                f"Start it with: ollama serve\nThen pull: ollama pull {self._model}"
            )

        if on_progress:
            await on_progress(f"Sending to local {self._model}...")

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # Encode images as base64
        images_b64: list[str] = []
        for img_path in image_paths:
            if on_progress:
                await on_progress(f"Encoding image: {img_path.name}")
            with open(img_path, "rb") as f:
                images_b64.append(base64.b64encode(f.read()).decode("utf-8"))

        # Add images to the user message if present
        if images_b64:
            # Ollama API: images go in the last message
            messages[-1]["images"] = images_b64

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "keep_alive": self._keep_alive,
            "options": self._options,
        }

        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            result = resp.json()

        return result.get("message", {}).get("content", "")
