"""PDF page rendering to PNG images via PyMuPDF."""

import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Sequence

import fitz


class PDFRenderError(Exception):
    """Raised when PDF rendering fails."""


class PDFRenderer:
    """Converts selected PDF pages to PNG images using PyMuPDF."""

    def __init__(
        self,
        pdf_path: str | Path,
        dpi: int = 200,
        output_dir: str | Path | None = None,
        poppler_path: str | None = None,
    ):
        self._pdf_path = Path(pdf_path)
        if not self._pdf_path.exists():
            raise PDFRenderError(f"PDF file not found: {self._pdf_path}")

        self._dpi = dpi
        # poppler_path kept for API compat but not needed by PyMuPDF
        self._poppler_path = poppler_path

        # Use provided temp dir or system default
        if output_dir:
            self._output_dir = Path(output_dir)
            self._output_dir.mkdir(parents=True, exist_ok=True)
        else:
            self._output_dir = Path(tempfile.mkdtemp(prefix="pdf_render_"))

        self._cleanup_needed = output_dir is None

    @property
    def output_dir(self) -> Path:
        return self._output_dir

    # ── Rendering ────────────────────────────────────────────────────────

    def render_page(self, page_num: int) -> Path:
        """Render a single page (0-indexed) to PNG. Returns the image path."""
        doc = fitz.open(self._pdf_path)
        try:
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=self._dpi)
            img_path = self._output_dir / f"page_{page_num + 1:04d}.png"
            pix.save(str(img_path))
        finally:
            doc.close()
        return img_path

    def render_pages(self, page_nums: Sequence[int], max_workers: int = 4) -> list[Path]:
        """Render multiple pages in parallel. Returns list of PNG paths."""
        paths: list[Path] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            fut_map = {
                executor.submit(self.render_page, p): p for p in page_nums
            }
            for future in as_completed(fut_map):
                paths.append(future.result())
        return sorted(paths)

    # ── Cleanup ──────────────────────────────────────────────────────────

    def cleanup(self) -> None:
        """Remove temporary output directory and its contents."""
        if self._cleanup_needed and self._output_dir.exists():
            shutil.rmtree(self._output_dir, ignore_errors=True)
