"""Markdown output builder with Obsidian-compatible YAML frontmatter."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from utils.helpers import slugify, make_filepath, today_str


class MarkdownWriter:
    """Builds and writes Obsidian-compatible markdown files."""

    def __init__(
        self,
        vault_path: str | Path,
        yaml_frontmatter: bool = True,
        default_tags: list[str] | None = None,
    ):
        self._vault_path = Path(vault_path)
        self._yaml_frontmatter = yaml_frontmatter
        self._default_tags = default_tags or ["paper", "summary"]

    # ── Frontmatter ──────────────────────────────────────────────────────

    def build_frontmatter(
        self,
        title: str,
        authors: list[str] | None = None,
        source_pdf: str | Path | None = None,
        arxiv_id: str | None = None,
        tags: list[str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> str:
        """Build YAML frontmatter string.

        Args:
            title: Paper title.
            authors: List of author names.
            source_pdf: Path to the original PDF file.
            arxiv_id: arXiv ID if applicable.
            tags: Additional tags (will be merged with defaults).
            extra: Extra key-value pairs to include in frontmatter.

        Returns:
            YAML frontmatter string including the --- delimiters.
        """
        lines = ["---"]
        lines.append(f'title: "{title}"')

        if authors:
            authors_str = ", ".join(authors)
            lines.append(f"authors: [{authors_str}]")

        lines.append(f"date: {today_str()}")
        lines.append(f"created: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        all_tags = list(self._default_tags)
        if tags:
            all_tags.extend(tags)
        tags_str = ", ".join(all_tags)
        lines.append(f"tags: [{tags_str}]")

        if source_pdf:
            lines.append(f"source: {source_pdf}")

        if arxiv_id:
            lines.append(f"arxiv: {arxiv_id}")

        if extra:
            for key, value in extra.items():
                lines.append(f"{key}: {value}")

        lines.append("---")
        return "\n".join(lines)

    # ── Body ─────────────────────────────────────────────────────────────

    # Section title translations for output
    _SECTION_TITLES: dict[str, dict[str, str]] = {
        "en": {
            "Motivation": "Motivation",
            "Contributions": "Contributions",
            "Methodology": "Methodology",
            "Experimental Setup": "Experimental Setup",
            "Strengths & Weaknesses": "Strengths & Weaknesses",
            "Final Short Note": "Final Short Note",
        },
        "zh": {
            "Motivation": "研究动机",
            "Contributions": "主要贡献",
            "Methodology": "研究方法",
            "Experimental Setup": "实验设置",
            "Strengths & Weaknesses": "优势与不足",
            "Final Short Note": "总结",
        },
    }

    @staticmethod
    def build_body(sections: dict[str, str], language: str = "en") -> str:
        """Build the markdown body from section dict.

        Args:
            sections: {section_title: section_content, ...}
                      Example keys: "Motivation", "Contributions", etc.
            language: "en" or "zh" for output section titles.

        Returns:
            Complete markdown body string.
        """
        titles = MarkdownWriter._SECTION_TITLES.get(language, MarkdownWriter._SECTION_TITLES["en"])
        parts: list[str] = []
        for i, (key, content) in enumerate(sections.items(), 1):
            cleaned_content = content.strip()
            display_title = titles.get(key, key)
            parts.append(f"## {i}. {display_title}\n")
            parts.append(cleaned_content if cleaned_content else "*Not stated in the paper.*")
            parts.append("")  # blank line after each section

        return "\n".join(parts)

    # ── Write ────────────────────────────────────────────────────────────

    def write(
        self,
        paper_title: str,
        frontmatter: str,
        body: str,
        filename: str | None = None,
    ) -> Path:
        """Write the complete markdown file to the vault.

        Args:
            paper_title: Used to generate filename if filename is None.
            frontmatter: YAML frontmatter string (with --- delimiters).
            body: Markdown body string.
            filename: Optional explicit filename.

        Returns:
            Path to the written file.
        """
        if filename:
            output_path = self._vault_path / filename
        else:
            output_path = make_filepath(paper_title, self._vault_path)

        self._vault_path.mkdir(parents=True, exist_ok=True)

        if self._yaml_frontmatter:
            content = f"{frontmatter}\n\n# {paper_title}\n\n{body}"
        else:
            content = f"# {paper_title}\n\n{body}"

        # Ensure trailing newline
        if not content.endswith("\n"):
            content += "\n"

        output_path.write_text(content, encoding="utf-8")
        return output_path
