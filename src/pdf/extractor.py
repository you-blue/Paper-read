"""PDF text and metadata extraction using PyMuPDF."""

from pathlib import Path
from typing import Any

import fitz


class PDFExtractionError(Exception):
    """Raised when PDF extraction fails."""


class PDFExtractor:
    """Extracts text content and metadata from a PDF file."""

    def __init__(self, pdf_path: str | Path):
        self._path = Path(pdf_path)
        if not self._path.exists():
            raise PDFExtractionError(f"PDF file not found: {self._path}")

        self._doc: fitz.Document | None = None

    def _ensure_open(self) -> fitz.Document:
        if self._doc is None:
            self._doc = fitz.open(str(self._path))
        return self._doc

    def close(self) -> None:
        if self._doc is not None:
            self._doc.close()
            self._doc = None

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ── Basic info ──────────────────────────────────────────────────────

    @property
    def page_count(self) -> int:
        return len(self._ensure_open())

    @property
    def path(self) -> Path:
        return self._path

    # ── Metadata ─────────────────────────────────────────────────────────

    def extract_metadata(self) -> dict[str, Any]:
        """Extract PDF metadata including title, author, subject, etc."""
        doc = self._ensure_open()
        meta = doc.metadata or {}
        return {
            "title": (meta.get("title") or "").strip(),
            "author": (meta.get("author") or "").strip(),
            "subject": (meta.get("subject") or "").strip(),
            "keywords": (meta.get("keywords") or "").strip(),
        }

    # ── Text extraction ──────────────────────────────────────────────────

    def extract_page_text(self, page_num: int) -> str:
        """Extract text from a single page (0-indexed)."""
        doc = self._ensure_open()
        if page_num < 0 or page_num >= len(doc):
            raise PDFExtractionError(f"Page number out of range: {page_num}")
        page = doc[page_num]
        return page.get_text("text")

    def extract_all_text(self) -> list[str]:
        """Extract text from all pages. Returns list[str] where [i] = page i."""
        doc = self._ensure_open()
        return [page.get_text("text") for page in doc]

    def extract_page_blocks(self, page_num: int) -> list[dict]:
        """Extract text blocks with position info from a single page."""
        doc = self._ensure_open()
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        result = []
        for block in blocks:
            if block["type"] == 0:  # text block
                text = "".join(
                    span["text"]
                    for line in block["lines"]
                    for span in line["spans"]
                )
                result.append({
                    "type": "text",
                    "text": text.strip(),
                    "bbox": block["bbox"],
                    "font": block["lines"][0]["spans"][0]["font"]
                    if block["lines"]
                    else "",
                })
            elif block["type"] == 1:  # image block
                result.append({
                    "type": "image",
                    "bbox": block["bbox"],
                })
        return result
