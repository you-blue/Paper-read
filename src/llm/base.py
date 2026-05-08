"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Coroutine


class LLMProvider(ABC):
    """Abstract interface for LLM-based paper summarization.

    All providers (Claude, OpenAI, Ollama) must implement this interface.
    """

    async def test_connection(self) -> str:
        """Test whether the provider can connect successfully.

        Returns a success message on success.
        Raises an exception (with details) on failure.
        """
        # Default: try a minimal API call via summarize with empty text.
        # Providers should override this with a lighter test if possible.
        result = await self.summarize(
            paper_text="Hello",
            image_paths=[],
            system_prompt="Reply with exactly: OK",
            user_message="Hello",
        )
        return f"Connected successfully. Response: {result[:100]}"

    @abstractmethod
    async def summarize(
        self,
        paper_text: str,
        image_paths: list[Path],
        system_prompt: str,
        user_message: str,
        on_progress: Callable[[str], Coroutine | None] | None = None,
    ) -> str:
        """Send paper content to the LLM and return the summary markdown.

        Args:
            paper_text: Full extracted text from the PDF.
            image_paths: Paths to rendered PNG images for math/figure pages.
            system_prompt: The system-level instructions (6-section template).
            user_message: The user message containing paper text/context.
            on_progress: Optional async callback for status updates.

        Returns:
            The full summary as a markdown string.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""

    @property
    @abstractmethod
    def supports_vision(self) -> bool:
        """Whether this provider supports image inputs."""
