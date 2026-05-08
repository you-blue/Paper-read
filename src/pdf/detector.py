"""Smart page-type detection for hybrid text+image PDF processing.

Classifies each page as 'text', 'math', 'figure', or 'mixed' to decide
whether image rendering is needed for accurate LLM analysis.
"""

import re
from typing import Sequence


# ── Pattern sets ───────────────────────────────────────────────────────────

MATH_PATTERNS: list[re.Pattern] = [
    re.compile(r'\$[^$]+\$'),               # inline math $...$
    re.compile(r'\$\$[^$]*\$\$'),           # display math $$...$$
    re.compile(r'\\begin\{(equation|align|gather|flalign|multline)\}'),
    re.compile(r'\\end\{(equation|align|gather|flalign|multline)\}'),
    re.compile(r'\\\[.*?\\\]', re.DOTALL),  # \[ ... \]
    re.compile(r'\\sum\s*_{?'),             # \sum_ or \sum{  (subscript often follows)
    re.compile(r'\\int\s*_{?'),             # \int_
    re.compile(r'\\frac\{'),                # \frac{...}{...}
    re.compile(r'\\partial'),               # \partial
    re.compile(r'\\alpha|\\beta|\\gamma|\\theta|\\sigma|\\lambda|\\phi|\\omega|\\epsilon|\\mu|\\pi'),
    re.compile(r'\\mathbf|\\mathcal|\\mathbb|\\mathsf|\\mathtt'),
    re.compile(r'\\rightarrow|\\leftarrow|\\Rightarrow|\\Leftarrow'),
    re.compile(r'\\nabla|\\propto|\\infty|\\approx|\\equiv'),
    re.compile(r'\\binom\{'),               # \binom{...}{...}
    re.compile(r'\\text\{.*?\}'),           # \text{...} (common in math mode)
    # Unicode math operators (common in PDF text extraction)
    re.compile(r'[∀-⋿]'),         # Mathematical Operators (∀, ∂, ∑, ∫, ≈, etc.)
    re.compile(r'[←-⇿]'),         # Arrows (→, ⇒, ⇔, etc.)
    re.compile(r'[≠-≥]'),         # ≠, ≤, ≥
    re.compile(r'[⊂-⊊]'),         # ⊂, ⊃, ⊆, ⊇, ⊈, ⊉, ⊊, ⊋
    re.compile(r'[°-³]'),         # °, ±, ², ³
    re.compile(r'[⁰-₟]'),         # Superscripts and Subscripts
]

FIGURE_PATTERNS: list[re.Pattern] = [
    re.compile(r'^Figure\s+\d+', re.MULTILINE),
    re.compile(r'^Fig\.?\s+\d+', re.MULTILINE),
    re.compile(r'^Table\s+\d+', re.MULTILINE),
    re.compile(r'^Algorithm\s+\d+', re.MULTILINE),
]

# ── Detector ──────────────────────────────────────────────────────────────

class PageTypeDetector:
    """Classifies PDF pages for hybrid text+image processing."""

    # Thresholds (configurable via init)
    MATH_THRESHOLD: int = 2          # min math pattern hits → math page
    LOW_TEXT_THRESHOLD: int = 100    # words below this → likely figure/image page
    ALWAYS_RENDER_FIRST: bool = True  # always render page 0 (often has figures)

    def __init__(
        self,
        math_threshold: int = MATH_THRESHOLD,
        low_text_threshold: int = LOW_TEXT_THRESHOLD,
        always_render_first: bool = ALWAYS_RENDER_FIRST,
    ):
        self.math_threshold = math_threshold
        self.low_text_threshold = low_text_threshold
        self.always_render_first = always_render_first

    # ── Classification ──────────────────────────────────────────────────

    def classify_page(self, text: str, page_num: int) -> str:
        """Classify a single page.

        Returns one of: 'text', 'math', 'figure', 'mixed'.
        """
        if self.always_render_first and page_num == 0:
            return "mixed"

        word_count = len(text.split())
        math_hits = sum(1 for p in MATH_PATTERNS if p.search(text))
        figure_hits = sum(1 for p in FIGURE_PATTERNS if p.search(text))

        # Low text density → likely image-only page
        if word_count < self.low_text_threshold:
            if figure_hits > 0:
                return "figure"
            if math_hits > 0:
                return "math"
            return "text"  # short text but no visual clues → no image needed

        # Math-heavy page
        if math_hits >= self.math_threshold:
            return "math"

        # Figure page
        if figure_hits > 0 and word_count < 200:
            return "figure"

        # Mixed: moderate math + figures
        if math_hits > 0 and figure_hits > 0:
            return "mixed"

        return "text"

    def needs_image(self, text: str, page_num: int) -> bool:
        """True if this page should be rendered as image alongside text."""
        return self.classify_page(text, page_num) != "text"

    def get_image_pages(self, all_text: Sequence[str]) -> list[int]:
        """Return 0-indexed page numbers that need image rendering."""
        return [
            i for i, text in enumerate(all_text)
            if self.needs_image(text, i)
        ]
