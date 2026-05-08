"""System prompt and response parser for paper summarization.

Reuses the 6-section structure from the summarise-paper skill.
"""

import re

SYSTEM_PROMPT = """You are a senior researcher summarising an academic paper. Your goal is to produce a "weeks-later readable" research note: after reading many papers, the reader should be able to reconstruct the paper's core ideas, methods, and evidence, and discuss it intelligently even without having read it recently.

## Core requirements

- **Faithfulness:** Use ONLY information supported by the paper. If a detail is missing or unclear, write "Not stated in the paper" rather than guessing.
- **Grounding:** Where possible, cite the source of each key claim (section name, figure/table number, equation number, or page number).
- **Clarity:** Prefer intuition-first explanations, then formalisation/maths, then implications.
- **Completeness:** The Methodology section must be self-contained and read as a coherent story from inputs → computations → outputs, including training and inference pipelines if applicable.
- **Language:** Use British English.

## Output format

Write the note using the EXACT structure and headings below. Use ## for main headings, ### for subheadings.

### 1. Motivation

- What problem is being addressed?
- What failure mode or limitation of prior work is targeted?
- Why it matters.

### 2. Contributions

- Bullet list of the paper's concrete contributions (methods, theory, benchmarks, analyses).
- Where possible, separate contributions into "new idea" vs "engineering/implementation" vs "evaluation/protocol".

### 3. Methodology

- MINI-PAPER STYLE, single coherent story.
- Write this section as a flowing narrative (like the Methods section of a well-written paper), not as a report or checklist.
- No sub-bullets or lettered substeps. Minimal headings are allowed, but prefer continuous prose.
- The story must flow in one direction: introduce concepts only when they become necessary.
- Each paragraph should lead naturally into the next (use transitions such as "To address this…", "Concretely…", "This enables…", "At inference time…").
- Include whichever of the following are relevant: problem setting and assumptions; core insight; main objects/components; key equations/objectives; the end-to-end procedure; inference-time behaviour; notable implementation details.

### 4. Experimental Setup

- A short "Implementation checklist" with 4–8 items ONLY if the paper provides those details. If not provided, write "Not stated in the paper."
- Datasets/tasks, baselines, evaluation protocol, and metrics.
- What ablations or sensitivity analyses were run.

### 5. Strengths & Weaknesses

- **Strengths:** 3–6 bullets with reasons tied to evidence in the paper.
- **Weaknesses/risks:** 3–6 bullets (e.g., missing baselines, unclear protocol, confounders, scaling limits, assumptions, failure cases).
- Include **"What I would ask the authors as a reviewer"** (2–3 questions).

### 6. Final Short Note

- 1–3 sentences giving a crisp description of what the paper does and the key result/claim.
- Key takeaways: 3–5 bullets covering what to steal/adapt, what to be cautious about, and one concrete follow-up experiment idea.
"""


def build_user_message(paper_text: str, paper_title: str, language: str = "en") -> str:
    """Build the user message containing the full paper text.

    Args:
        paper_text: Full text of the paper.
        paper_title: Title of the paper.
        language: Output language — "zh" for Chinese, "en" for English.
    """
    lang_instr = {
        "zh": "请用中文撰写总结。",
        "en": "Use British English.",
    }.get(language, "Use British English.")

    return f"""Please summarise the following paper: "{paper_title}"

---

{paper_text}

---

Provide a comprehensive summary following the structure specified in the system instructions.
{lang_instr}
"""


# ── Section title variants (English + Chinese) ──────────────────────────

_SECTION_KEYS = [
    "Motivation",
    "Contributions",
    "Methodology",
    "Experimental Setup",
    "Strengths & Weaknesses",
    "Final Short Note",
]

_TITLE_VARIANTS: dict[str, list[str]] = {
    "Motivation": ["Motivation", "动机", "研究动机", "研究背景"],
    "Contributions": ["Contributions", "贡献", "主要贡献", "创新点"],
    "Methodology": ["Methodology", "方法", "方法论", "研究方法"],
    "Experimental Setup": ["Experimental Setup", "实验设置", "实验设计", "实验"],
    "Strengths & Weaknesses": [
        "Strengths & Weaknesses", "Strengths and Weaknesses",
        "优势与不足", "优点与缺点",
    ],
    "Final Short Note": ["Final Short Note", "总结", "最终总结", "简要总结"],
}

# Build flattened lookup: normalized variant → canonical key
_VARIANT_TO_KEY: dict[str, str] = {}
for key, variants in _TITLE_VARIANTS.items():
    for v in variants:
        _VARIANT_TO_KEY[v.lower()] = key


def _strip_heading(s: str) -> str:
    """Strip markdown heading markers, numbers, and punctuation from a line."""
    for ch in ["#", "*", ".", ",", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
        s = s.replace(ch, "")
    return " ".join(s.strip().lower().split())


def _find_section_key(line: str) -> str | None:
    """Check if a line is a section heading; return canonical key or None."""
    cleaned = _strip_heading(line)
    for variant_lower, canonical_key in _VARIANT_TO_KEY.items():
        # Variant should be a substantial part of the heading
        if variant_lower in cleaned:
            # Verify the line looks like a heading (short, starts with #/*/number)
            stripped = line.strip()
            looks_like_heading = (
                stripped.startswith("#")
                or stripped.startswith("*")
                or re.match(r"^\d+\.?\s", stripped)
            )
            if looks_like_heading:
                return canonical_key
    return None


def _split_numbered_sections(response: str) -> dict[str, str]:
    """Ultimate fallback: split response by numbered items (1., 2., etc.) and
    try to map each to a section key. Handles cases like plain text:
    '1. Motivation\\ncontent\\n2. Contributions\\ncontent'"""
    sections: dict[str, str] = {}
    lines = response.split("\n")
    current_key = None
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Match "1. Anything" or "1、Anything" at line start
        m = re.match(r"^(\d+)[.、]\s*(.*)", stripped)
        if m:
            num = int(m.group(1))
            rest = m.group(2)
            if current_key is not None:
                sections[current_key] = "\n".join(current_lines).strip()

            # Try to identify the section from the rest of the heading text
            rest_clean = _strip_heading(rest)
            matched = False
            for variant_lower, canonical_key in _VARIANT_TO_KEY.items():
                if variant_lower in rest_clean:
                    current_key = canonical_key
                    current_lines = []
                    matched = True
                    break
            if not matched and 1 <= num <= 6:
                # Use positional mapping as last resort
                positional = {
                    1: "Motivation", 2: "Contributions", 3: "Methodology",
                    4: "Experimental Setup", 5: "Strengths & Weaknesses",
                    6: "Final Short Note",
                }
                current_key = positional.get(num)
                current_lines = []
        elif current_key is not None:
            current_lines.append(line)

    if current_key is not None:
        sections[current_key] = "\n".join(current_lines).strip()

    return sections


def parse_llm_response(response: str, language: str = "en") -> dict[str, str]:
    """Parse the LLM response into structured sections.

    Uses three strategies in order:
      1. Detect markdown section headers (### 1. Motivation, etc.)
      2. Fallback: split on ## headings or numbered lines
      3. Last resort: split on numbered items (1., 2.) using position

    Supports both English and Chinese section titles.
    Returns dict with keys matching the 6 sections. Missing sections
    are filled with a placeholder.
    """
    if not response or not response.strip():
        return {k: "*Not generated in the response.*" for k in _SECTION_KEYS}

    # Strategy 1: Markdown heading detection
    sections: dict[str, str] = {}
    current_section = None
    current_lines: list[str] = []

    for line in response.split("\n"):
        matched_key = _find_section_key(line)
        if matched_key:
            if current_section is not None:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = matched_key
            current_lines = []
        elif current_section is not None:
            current_lines.append(line)

    if current_section is not None:
        sections[current_section] = "\n".join(current_lines).strip()

    # Strategy 2: Fallback parse (heading/numbered line split)
    if len(sections) < len(_SECTION_KEYS):
        fallback = _fallback_parse(response)
        for key in _SECTION_KEYS:
            if (key not in sections or not sections[key].strip()) and key in fallback:
                sections[key] = fallback[key]

    # Strategy 3: Numbered section split
    if len(sections) < len(_SECTION_KEYS):
        numbered = _split_numbered_sections(response)
        for key in _SECTION_KEYS:
            if (key not in sections or not sections[key].strip()) and key in numbered:
                sections[key] = numbered[key]

    # Fill missing
    for key in _SECTION_KEYS:
        if key not in sections or not sections[key].strip():
            sections[key] = "*Not generated in the response.*"

    return sections


def _fallback_parse(response: str) -> dict[str, str]:
    """Split on markdown headings (## or ###) or numbered lines (1. ...),
    map to canonical section keys using variant lookup."""
    lines = response.split("\n")
    sections: dict[str, str] = {}
    current_key = None
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Match headings or numbered starts
        is_heading = bool(re.match(r"^#{1,4}\s", stripped)) or bool(re.match(r"^\d+\.\s", stripped))
        if is_heading:
            if current_key is not None:
                sections[current_key] = "\n".join(current_lines).strip()
            matched_key = _find_section_key(stripped)
            if matched_key:
                current_key = matched_key
                current_lines = []
            else:
                current_key = stripped.lstrip("#").strip()
                current_lines = []
        elif current_key is not None:
            current_lines.append(line)

    if current_key is not None:
        sections[current_key] = "\n".join(current_lines).strip()

    return sections
