"""
analyzer.py — AI-powered explanation and improvement suggestions.

Uses a lightweight HuggingFace text-generation pipeline to produce
human-readable rejection reasons and actionable improvement tips.

Design decision: we use a locally-run model (flan-t5-base) so the
system works fully offline without API keys.  Swap out `_MODEL_NAME`
for any instruction-tuned model on HuggingFace Hub.
"""

import logging
import textwrap
from typing import Optional

from matcher import MatchResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

# flan-t5-base is small (~250 MB), fast, and instruction-tuned.
# Upgrade to "google/flan-t5-large" or a Mistral GGUF for better quality.
_MODEL_NAME = "google/flan-t5-base"
_MAX_NEW_TOKENS = 200

_pipeline = None  # lazy-loaded


def _get_pipeline():
    """Lazy-load and cache the HuggingFace text2text pipeline."""
    global _pipeline
    if _pipeline is None:
        try:
            from transformers import pipeline as hf_pipeline
            logger.info("Loading HuggingFace pipeline (%s)…", _MODEL_NAME)
            _pipeline = hf_pipeline(
                "text2text-generation",
                model=_MODEL_NAME,
                max_new_tokens=_MAX_NEW_TOKENS,
                do_sample=False,
            )
            logger.info("HuggingFace pipeline ready.")
        except Exception as exc:
            logger.error("Failed to load HuggingFace pipeline: %s", exc)
            _pipeline = None
    return _pipeline


# ---------------------------------------------------------------------------
# Rule-based fallback (always available, no model needed)
# ---------------------------------------------------------------------------

def _rule_based_rejection_reasons(result: MatchResult) -> list[str]:
    """
    Generate deterministic rejection reasons from the MatchResult.

    This is the fallback when the LLM is unavailable and also serves
    as a structured supplement to LLM output.
    """
    reasons: list[str] = []

    if result.match_score < 40:
        reasons.append(
            "The overall skill and semantic alignment with the job description is low, "
            "suggesting a significant mismatch in profile and role requirements."
        )

    if result.missing_skills:
        top_missing = result.missing_skills[:5]
        skills_str = ", ".join(top_missing)
        reasons.append(
            f"The following key skills listed in the job description are absent from "
            f"the resume: {skills_str}."
        )

    if result.skill_coverage < 0.4 and result.matched_skills:
        pct = round(result.skill_coverage * 100)
        reasons.append(
            f"Only {pct}% of required skills were matched. "
            "Recruiters typically look for ≥ 60% skill overlap."
        )

    if "gap" in result.experience_gap.lower() and "year" in result.experience_gap.lower():
        reasons.append(f"Experience gap detected: {result.experience_gap}")

    if not reasons:
        reasons.append(
            "Profile shows reasonable alignment but may lack differentiation "
            "from other applicants on key technical competencies."
        )

    return reasons


def _rule_based_suggestions(result: MatchResult) -> list[str]:
    """Generate actionable improvement suggestions based on gap analysis."""
    suggestions: list[str] = []

    # Skill-specific suggestions
    for skill in result.missing_skills[:6]:
        if skill in {"docker", "kubernetes"}:
            suggestions.append(
                f"Learn {skill.title()} by containerising a personal project. "
                "A simple 3-tier app with docker-compose is a great starting point."
            )
        elif skill in {"aws", "azure", "gcp"}:
            suggestions.append(
                f"Get certified in {skill.upper()} (e.g., Cloud Practitioner for AWS). "
                "Free-tier accounts let you build real projects at no cost."
            )
        elif skill in {"machine learning", "deep learning", "tensorflow", "pytorch"}:
            suggestions.append(
                f"Complete a hands-on {skill.title()} course (fast.ai or Coursera) "
                "and publish a Kaggle notebook to demonstrate practical skills."
            )
        elif skill in {"react", "angular", "vue", "next.js"}:
            suggestions.append(
                f"Build a full CRUD application with {skill.title()} and deploy it "
                "on Vercel or Netlify. Add it to your GitHub profile."
            )
        else:
            suggestions.append(
                f"Gain hands-on experience with {skill.title()} through a "
                "side project or open-source contribution."
            )

    # Score-based meta-suggestions
    if result.match_score < 50:
        suggestions.append(
            "Consider tailoring your resume keywords to mirror the exact language "
            "used in the job description to improve ATS screening scores."
        )

    if result.semantic_similarity < 0.35:
        suggestions.append(
            "Rewrite your professional summary to align more closely with the "
            "role's domain (e.g., if the JD focuses on backend systems, "
            "emphasise your backend impact, not just responsibilities)."
        )

    if len(result.extra_skills) > len(result.matched_skills):
        suggestions.append(
            "You have many skills not mentioned in the JD. "
            "Consider creating a role-specific resume that surfaces the most "
            "relevant ones rather than a generic skills list."
        )

    return suggestions[:8]  # cap at 8 for readability


# ---------------------------------------------------------------------------
# LLM-enhanced generation (with rule-based fallback)
# ---------------------------------------------------------------------------

def _llm_generate(prompt: str) -> Optional[str]:
    """
    Run the prompt through the local HuggingFace pipeline.

    Returns None if the pipeline is unavailable or the call fails.
    """
    pipe = _get_pipeline()
    if pipe is None:
        return None
    try:
        result = pipe(prompt, max_new_tokens=_MAX_NEW_TOKENS)
        return result[0]["generated_text"].strip()
    except Exception as exc:
        logger.warning("LLM generation failed: %s", exc)
        return None


def generate_analysis_summary(
    result: MatchResult,
    jd_snippet: str = "",
) -> str:
    """
    Produce a concise natural-language analysis paragraph.

    Tries LLM first; falls back to a template-based summary.

    Args:
        result:     MatchResult from matcher.compute_match().
        jd_snippet: First 300 chars of the JD for context.

    Returns:
        A 2–4 sentence analysis string.
    """
    # Attempt LLM
    prompt = textwrap.dedent(f"""
        You are a senior recruiter. Write a 2-3 sentence analysis of this candidate.

        Match score: {result.match_score}/100
        Matched skills: {', '.join(result.matched_skills[:6]) or 'none'}
        Missing skills: {', '.join(result.missing_skills[:6]) or 'none'}
        Experience: {result.experience_gap}
        Job context: {jd_snippet[:300]}

        Provide an honest, specific, professional assessment.
    """).strip()

    llm_output = _llm_generate(prompt)
    if llm_output and len(llm_output) > 30:
        return llm_output

    # Rule-based fallback
    score = result.match_score
    if score >= 75:
        tone = "strong"
        verdict = "This candidate is a strong fit for the role."
    elif score >= 50:
        tone = "moderate"
        verdict = "This candidate shows potential but has notable gaps."
    else:
        tone = "weak"
        verdict = "This candidate's profile does not closely align with the role requirements."

    parts = [verdict]
    if result.matched_skills:
        parts.append(
            f"Demonstrated strengths include: {', '.join(result.matched_skills[:4])}."
        )
    if result.missing_skills:
        parts.append(
            f"Key gaps: {', '.join(result.missing_skills[:4])}."
        )
    parts.append(result.experience_gap)

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def build_full_analysis(
    result: MatchResult,
    resume_text: str,
    jd_text: str,
) -> dict:
    """
    Assemble the complete analysis payload returned by the API.

    Args:
        result:      MatchResult from matcher.compute_match().
        resume_text: Cleaned resume text.
        jd_text:     Cleaned JD text.

    Returns:
        Dict ready to be serialised as the API JSON response.
    """
    jd_snippet = jd_text[:300]

    analysis_summary = generate_analysis_summary(result, jd_snippet)
    rejection_reasons = _rule_based_rejection_reasons(result)
    improvement_suggestions = _rule_based_suggestions(result)

    return {
        "match_score": result.match_score,
        "matched_skills": result.matched_skills,
        "missing_skills": result.missing_skills,
        "extra_skills": result.extra_skills,
        "experience_gap": result.experience_gap,
        "analysis": analysis_summary,
        "rejection_reasons": rejection_reasons,
        "improvement_suggestions": improvement_suggestions,
        "meta": {
            "semantic_similarity": result.semantic_similarity,
            "skill_coverage": result.skill_coverage,
            "total_jd_skills_detected": len(result.matched_skills) + len(result.missing_skills),
            "total_resume_skills_detected": len(result.matched_skills) + len(result.extra_skills),
        },
    }