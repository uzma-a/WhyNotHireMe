"""
parser.py — Resume and Job Description text extraction + preprocessing.

Handles PDF parsing via pdfplumber (with PyMuPDF as fallback),
text cleaning, and structured section detection.
"""

import re
import logging
from pathlib import Path
from typing import Optional

import pdfplumber

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file_path: str | Path) -> str:
    """
    Extract raw text from a PDF resume.

    Uses pdfplumber for layout-aware extraction.  Falls back to a
    character-level join when a page has no detected words.

    Args:
        file_path: Absolute or relative path to the PDF file.

    Returns:
        Concatenated text from all pages.

    Raises:
        FileNotFoundError: If the PDF does not exist.
        ValueError: If no text could be extracted at all.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {path}")

    pages_text: list[str] = []

    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(x_tolerance=2, y_tolerance=3)
            if text:
                pages_text.append(text)
            else:
                # Fallback: join individual chars (handles some scanned PDFs)
                chars = page.chars
                if chars:
                    fallback = "".join(c.get("text", "") for c in chars)
                    pages_text.append(fallback)
                    logger.warning(
                        "Page %d: used character fallback extraction.", page_num
                    )
                else:
                    logger.warning(
                        "Page %d: no text found — may be image-only.", page_num
                    )

    if not pages_text:
        raise ValueError(
            "Could not extract any text from the PDF. "
            "The file may be image-only or encrypted."
        )

    return "\n".join(pages_text)


def clean_text(raw: str) -> str:
    """
    Normalise extracted text for downstream NLP.

    Steps
    -----
    1. Collapse unicode whitespace variants to ASCII space / newline.
    2. Remove non-printable / control characters.
    3. Collapse runs of blank lines to at most two.
    4. Strip leading / trailing whitespace per line.

    Args:
        raw: Raw text from a PDF page or user input.

    Returns:
        Cleaned, normalised string.
    """
    # Replace various unicode spaces and dashes with ASCII equivalents
    text = raw.replace("\xa0", " ").replace("\u2022", "-").replace("\u2019", "'")

    # Drop control characters except newline and tab
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00C0-\u024F]", " ", text)

    # Normalise whitespace within each line
    lines = [" ".join(line.split()) for line in text.splitlines()]

    # Collapse sequences of empty lines (max 2)
    cleaned_lines: list[str] = []
    blank_run = 0
    for line in lines:
        if line == "":
            blank_run += 1
            if blank_run <= 2:
                cleaned_lines.append(line)
        else:
            blank_run = 0
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def extract_sections(text: str) -> dict[str, str]:
    """
    Heuristically split a resume into named sections.

    Detects headings by scanning for lines that are short (≤ 60 chars),
    ALL-CAPS or Title-Case, and match known resume section keywords.

    Args:
        text: Cleaned resume text.

    Returns:
        Dict mapping section name → section body text.
        Always includes a ``"full"`` key with the entire text.
    """
    section_patterns = [
        r"(SUMMARY|OBJECTIVE|PROFILE|ABOUT)",
        r"(EXPERIENCE|WORK\s+EXPERIENCE|EMPLOYMENT|CAREER)",
        r"(EDUCATION|ACADEMIC|QUALIFICATIONS)",
        r"(SKILLS|TECHNICAL\s+SKILLS|CORE\s+COMPETENCIES|TECHNOLOGIES)",
        r"(PROJECTS|PORTFOLIO|WORK\s+SAMPLES)",
        r"(CERTIFICATIONS?|LICENSES?|COURSES?)",
        r"(AWARDS?|HONORS?|ACHIEVEMENTS?)",
        r"(LANGUAGES?)",
        r"(PUBLICATIONS?|RESEARCH)",
        r"(VOLUNTEER|COMMUNITY)",
    ]
    combined_pattern = re.compile(
        r"^(" + "|".join(f"(?:{p})" for p in section_patterns) + r")\s*[:\-]?\s*$",
        re.IGNORECASE | re.MULTILINE,
    )

    sections: dict[str, str] = {"full": text}
    lines = text.splitlines()
    current_section: Optional[str] = None
    buffer: list[str] = []

    for line in lines:
        if combined_pattern.match(line.strip()):
            if current_section and buffer:
                sections[current_section] = "\n".join(buffer).strip()
            current_section = line.strip().upper().split()[0]
            buffer = []
        else:
            buffer.append(line)

    if current_section and buffer:
        sections[current_section] = "\n".join(buffer).strip()

    return sections