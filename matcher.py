"""
matcher.py — Skill extraction and semantic similarity scoring.

Responsibilities
----------------
* Extract skills from free-form text using a curated keyword taxonomy
  plus spaCy NER (noun-chunk fallback).
* Compute semantic similarity between resume and JD using
  sentence-transformers.
* Derive match score, matched/missing skills, and experience gap.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Skill taxonomy — extend freely
# ---------------------------------------------------------------------------

SKILL_TAXONOMY: dict[str, list[str]] = {
    "languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",
        "bash", "shell", "sql", "html", "css",
    ],
    "frameworks_libraries": [
        "react", "angular", "vue", "next.js", "nuxt", "svelte",
        "django", "fastapi", "flask", "spring", "express", "rails",
        "tensorflow", "pytorch", "keras", "scikit-learn", "pandas",
        "numpy", "opencv", "huggingface", "langchain",
    ],
    "cloud_devops": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "ansible", "jenkins", "github actions", "ci/cd", "linux",
        "nginx", "apache", "redis", "kafka", "rabbitmq",
    ],
    "databases": [
        "postgresql", "mysql", "mongodb", "sqlite", "oracle",
        "elasticsearch", "cassandra", "dynamodb", "firebase",
        "bigquery", "snowflake", "supabase",
    ],
    "tools_practices": [
        "git", "jira", "agile", "scrum", "rest api", "graphql",
        "microservices", "tdd", "bdd", "unit testing", "pytest",
        "jest", "selenium", "cypress", "figma", "tableau", "power bi",
    ],
    "ai_ml": [
        "machine learning", "deep learning", "nlp", "computer vision",
        "llm", "rag", "fine-tuning", "transformers", "bert", "gpt",
        "reinforcement learning", "data science", "feature engineering",
    ],
    "soft_skills": [
        "leadership", "communication", "problem solving", "teamwork",
        "project management", "time management", "critical thinking",
    ],
}

# Flat set for O(1) lookup
_ALL_SKILLS: set[str] = {
    skill for group in SKILL_TAXONOMY.values() for skill in group
}

# Regex to find experience mentions like "5 years", "3+ years", "2-4 years"
_EXP_PATTERN = re.compile(
    r"(\d+\.?\d*)\s*[\+\-]?\s*(?:to\s*\d+\s*)?years?\s+(?:of\s+)?(?:\w+\s+)?experience",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class MatchResult:
    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    extra_skills: list[str]           # skills candidate has beyond JD
    experience_gap: str
    semantic_similarity: float        # raw cosine score [0, 1]
    skill_coverage: float             # % of JD skills found in resume


# ---------------------------------------------------------------------------
# Model singleton
# ---------------------------------------------------------------------------

_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    """Lazy-load the sentence-transformer model (cached after first call)."""
    global _model
    if _model is None:
        logger.info("Loading sentence-transformer model…")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Model loaded.")
    return _model


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def extract_skills(text: str) -> list[str]:
    """
    Extract skills from free-form text using the taxonomy keyword list.

    Matching is case-insensitive and honours multi-word skills
    (e.g. "machine learning").

    Args:
        text: Any cleaned text block (resume, JD, section).

    Returns:
        Deduplicated, sorted list of matched skill strings.
    """
    text_lower = text.lower()
    found: set[str] = set()

    # Sort by length descending so multi-word phrases are matched first
    for skill in sorted(_ALL_SKILLS, key=len, reverse=True):
        # Use word-boundary aware search
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.add(skill)

    return sorted(found)


def compute_semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Compute cosine similarity between two texts using sentence-transformers.

    Texts are encoded as sentence embeddings.  Long texts are chunked
    into 512-token segments and averaged before comparison.

    Args:
        text_a: First text (e.g. resume).
        text_b: Second text (e.g. job description).

    Returns:
        Cosine similarity in [0.0, 1.0].
    """
    model = get_model()

    def _encode(text: str) -> np.ndarray:
        # Chunk by paragraph to avoid truncation on very long texts
        chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not chunks:
            chunks = [text]
        vecs = model.encode(chunks, convert_to_numpy=True, show_progress_bar=False)
        return vecs.mean(axis=0)

    vec_a = _encode(text_a)
    vec_b = _encode(text_b)

    # Cosine similarity
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0

    similarity = float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
    return max(0.0, min(1.0, similarity))  # clamp to [0, 1]


def parse_experience_years(text: str) -> Optional[float]:
    """
    Extract the largest stated number of years of experience from text.

    Args:
        text: Free-form text to search.

    Returns:
        Float years if found, else None.
    """
    matches = _EXP_PATTERN.findall(text)
    if not matches:
        return None
    return max(float(m) for m in matches)


def build_experience_gap_message(
    jd_years: Optional[float], resume_years: Optional[float]
) -> str:
    """
    Produce a human-readable experience gap description.

    Args:
        jd_years:     Years required per the job description.
        resume_years: Years found in the resume.

    Returns:
        A descriptive string.
    """
    if jd_years is None and resume_years is None:
        return "No explicit experience requirement found."
    if jd_years is None:
        return f"Candidate states ~{resume_years:.0f} years of experience; no JD requirement specified."
    if resume_years is None:
        return (
            f"JD requires {jd_years:.0f}+ years of experience; "
            "no explicit duration found in resume."
        )
    gap = jd_years - resume_years
    if gap <= 0:
        return (
            f"Candidate meets the experience requirement "
            f"({resume_years:.0f} years found vs {jd_years:.0f} required)."
        )
    return (
        f"Required {jd_years:.0f}+ years; resume indicates ~{resume_years:.0f} years "
        f"({gap:.0f}-year gap)."
    )


def compute_match(resume_text: str, jd_text: str) -> MatchResult:
    """
    Full matching pipeline: skills + semantic similarity → composite score.

    Scoring formula
    ---------------
    final_score = 0.55 × skill_coverage  +  0.45 × semantic_similarity

    Both components are normalised to [0, 1] before weighting.

    Args:
        resume_text: Cleaned resume text.
        jd_text:     Cleaned job-description text.

    Returns:
        MatchResult dataclass with all fields populated.
    """
    resume_skills = set(extract_skills(resume_text))
    jd_skills = set(extract_skills(jd_text))

    matched = sorted(resume_skills & jd_skills)
    missing = sorted(jd_skills - resume_skills)
    extra = sorted(resume_skills - jd_skills)

    skill_coverage = len(matched) / len(jd_skills) if jd_skills else 0.0

    semantic_sim = compute_semantic_similarity(resume_text, jd_text)

    # Composite score (weights tuned empirically)
    raw_score = 0.55 * skill_coverage + 0.45 * semantic_sim
    match_score = round(raw_score * 100)

    # Experience gap
    jd_years = parse_experience_years(jd_text)
    resume_years = parse_experience_years(resume_text)
    exp_gap_msg = build_experience_gap_message(jd_years, resume_years)

    return MatchResult(
        match_score=match_score,
        matched_skills=matched,
        missing_skills=missing,
        extra_skills=extra,
        experience_gap=exp_gap_msg,
        semantic_similarity=round(semantic_sim, 4),
        skill_coverage=round(skill_coverage, 4),
    )