"""Pipeline orchestrator: coordinates PDF processing, LLM summarization, and output."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Coroutine

from src.config.settings import ConfigManager
from src.pdf.extractor import PDFExtractor
from src.pdf.detector import PageTypeDetector
from src.pdf.renderer import PDFRenderer
from src.llm import create_provider
from src.output.markdown import MarkdownWriter
from utils import prompts
from utils.helpers import slugify


class SummarizationPipeline:
    """Orchestrates the full paper summarization workflow."""

    def __init__(self, config: ConfigManager):
        self._config = config

    async def run(
        self,
        pdf_path: str | Path,
        on_progress: Callable[[str], Coroutine] | None = None,
        override_provider: str | None = None,
        override_model: str | None = None,
        override_api_key: str | None = None,
        override_base_url: str | None = None,
        hybrid_mode: bool | None = None,
        output_vault: str | Path | None = None,
        tags: list[str] | None = None,
        output_language: str = "en",
    ) -> Path:
        """Run the full pipeline: PDF -> LLM -> Markdown.

        Args:
            pdf_path: Path to the PDF file.
            on_progress: Async callback for status updates.
            override_provider: Override default LLM provider.
            override_model: Override default model.
            override_api_key: Override default API key.
            override_base_url: Override default API base URL (for custom).
            hybrid_mode: Override hybrid mode setting.
            output_vault: Override output vault path.
            tags: Override default tags.

        Returns:
            Path to the generated markdown file.
        """
        pdf_path = Path(pdf_path)

        # ── Phase 1: PDF text extraction ─────────────────────────────────
        if on_progress:
            await on_progress(f"Loading PDF: {pdf_path.name}")

        with PDFExtractor(pdf_path) as extractor:
            metadata = extractor.extract_metadata()
            all_text = extractor.extract_all_text()
            page_count = extractor.page_count

        if on_progress:
            await on_progress(f"PDF loaded: {page_count} pages")

        # ── Phase 2: Page classification ─────────────────────────────────
        if on_progress:
            await on_progress("Classifying pages for hybrid processing...")

        use_hybrid = hybrid_mode if hybrid_mode is not None else self._config.get("pdf", "hybrid_mode", default=True)

        image_paths: list[Path] = []
        if use_hybrid:
            detector = PageTypeDetector(
                math_threshold=self._config.get("pdf", "detection", "math_pattern_threshold", default=3),
                low_text_threshold=self._config.get("pdf", "detection", "low_text_threshold", default=100),
                always_render_first=self._config.get("pdf", "detection", "always_render_first_page", default=True),
            )
            image_pages = detector.get_image_pages(all_text)

            if on_progress:
                await on_progress(
                    f"{len(image_pages)}/{page_count} pages need image rendering "
                    f"(math/figures)"
                )

            # ── Phase 3: Image rendering ────────────────────────────────
            renderer = None
            if image_pages:
                if on_progress:
                    await on_progress(f"Rendering {len(image_pages)} pages...")

                renderer = PDFRenderer(
                    pdf_path=pdf_path,
                    dpi=self._config.get("pdf", "dpi", default=200),
                    poppler_path=self._config.get_poppler_path(),
                )
                image_paths = renderer.render_pages(image_pages)
                if on_progress:
                    await on_progress(f"Rendered {len(image_paths)} page images")
        else:
            if on_progress:
                await on_progress("Hybrid mode disabled, using text only")

        # ── Phase 4: LLM summarization ───────────────────────────────────
        # Build paper context
        paper_title = metadata.get("title") or pdf_path.stem
        full_text = "\n\n---\n\n".join(all_text)

        if override_provider:
            provider_name = override_provider
        else:
            provider_name = self._config.get("llm", "default_provider", default="anthropic")

        # Build provider kwargs
        provider_kwargs = {"api_key": override_api_key} if override_api_key else {}

        if override_model:
            provider_kwargs["model"] = override_model
        else:
            provider_kwargs["model"] = self._config.get("llm", provider_name, "model", default="claude-sonnet-4-20250514")

        # Add provider-specific extra config
        if provider_name == "anthropic":
            provider_kwargs["max_tokens"] = self._config.get("llm", "anthropic", "max_tokens", default=8192)
            provider_kwargs["temperature"] = self._config.get("llm", "anthropic", "temperature", default=0.3)
        elif provider_name in ("openai", "qwen", "deepseek", "custom"):
            provider_kwargs["max_tokens"] = self._config.get("llm", provider_name, "max_tokens", default=8192)
            provider_kwargs["temperature"] = self._config.get("llm", provider_name, "temperature", default=0.3)
            # Pass base_url if explicitly provided
            if override_base_url:
                provider_kwargs["base_url"] = override_base_url
        elif provider_name == "ollama":
            provider_kwargs["base_url"] = self._config.get("llm", "ollama", "base_url", default="http://localhost:11434")
            provider_kwargs["options"] = self._config.get("llm", "ollama", "options", default={})

        if on_progress:
            await on_progress(f"Creating {provider_name} provider...")

        provider = create_provider(provider_name, **provider_kwargs)

        if on_progress:
            await on_progress(f"Sending to {provider.name} for summarization...")

        # Drop images if provider doesn't support vision (e.g. DeepSeek)
        if not provider.supports_vision:
            image_paths = []
            if on_progress:
                await on_progress("Provider does not support vision, using text only")

        user_message = prompts.build_user_message(full_text, paper_title, language=output_language)

        summary_md = await provider.summarize(
            paper_text=full_text,
            image_paths=image_paths,
            system_prompt=prompts.SYSTEM_PROMPT,
            user_message=user_message,
            on_progress=on_progress,
        )

        # Clean up rendered images — no longer needed after LLM call
        if renderer and self._config.get("pdf", "cleanup_temp", default=True):
            renderer.cleanup()

        if on_progress:
            await on_progress("Building markdown output...")

        # ── Phase 5: Write markdown ──────────────────────────────────────
        vault_path = Path(output_vault) if output_vault else self._config.get_vault_path()

        writer = MarkdownWriter(
            vault_path=vault_path,
            yaml_frontmatter=self._config.get("output", "yaml_frontmatter", default=True),
            default_tags=tags or self._config.get("output", "tags", default=["paper", "summary"]),
        )

        # Extract author info from metadata
        authors = None
        if metadata.get("author"):
            authors = [a.strip() for a in metadata["author"].split(";") if a.strip()]

        frontmatter = writer.build_frontmatter(
            title=paper_title,
            authors=authors,
            source_pdf=str(pdf_path.resolve()),
            tags=tags,
        )

        output_path = writer.write(
            paper_title=paper_title,
            frontmatter=frontmatter,
            body=summary_md,
        )

        if on_progress:
            await on_progress(f"Done! Saved to {output_path}")

        return output_path
