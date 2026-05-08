"""Helper utilities for filename handling, date formatting, etc."""

import re
import unicodedata
from datetime import date
from pathlib import Path


def slugify(text: str, max_length: int = 80) -> str:
    """Convert text to a URL-safe, readable slug.

    Examples:
        "Attention Is All You Need" -> "attention-is-all-you-need"
        "Deep Learning (3rd ed.)" -> "deep-learning-3rd-ed"
    """
    # Normalize unicode
    text = unicodedata.normalize("NFKD", text)
    # Remove non-ASCII characters
    text = text.encode("ascii", "ignore").decode("ascii")
    # Lowercase
    text = text.lower()
    # Replace non-alphanumeric chars (except spaces/hyphens) with nothing
    text = re.sub(r"[^\w\s-]", "", text)
    # Replace whitespace with hyphens
    text = re.sub(r"[\s_]+", "-", text)
    # Collapse multiple hyphens
    text = re.sub(r"-{2,}", "-", text)
    # Strip leading/trailing hyphens
    text = text.strip("-")
    # Truncate
    if len(text) > max_length:
        text = text[:max_length].rstrip("-")
    return text


def sanitize_filename(name: str) -> str:
    """Remove characters that are invalid in Windows filenames."""
    # Invalid: \ / : * ? " < > |
    sanitized = re.sub(r'[\\/:*?"<>|]', "", name)
    # Also replace newlines
    sanitized = sanitized.replace("\n", " ").replace("\r", " ")
    return sanitized.strip() or "untitled"


def today_str() -> str:
    """Return today's date as YYYY-MM-DD."""
    return date.today().isoformat()


def make_filepath(title: str, output_dir: str | Path, ext: str = ".md") -> Path:
    """Build the output file path from a paper title.

    Example:
        make_filepath("Attention Is All You Need", "/Papers")
        -> /Papers/attention-is-all-you-need.md
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    filename = slugify(title) + ext
    return output_path / filename


def estimate_tokens(text: str) -> int:
    """Rough token count estimate (4 chars per token)."""
    return len(text) // 4
