"""
test_api.py — Integration tests and a live demo for WhyNotHireMe.

Usage
-----
# Unit tests (no running server required):
    python test_api.py --unit

# Live API test (server must be running on localhost:8000):
    python test_api.py --live

# Both:
    python test_api.py
"""

import argparse
import json
import sys
import tempfile
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Sample fixtures
# ---------------------------------------------------------------------------

SAMPLE_JD = textwrap.dedent("""
    Senior Backend Engineer — FinTech Platform

    We are looking for a Senior Backend Engineer to join our growing team.

    Requirements:
    - 4+ years of experience in backend development
    - Strong proficiency in Python and FastAPI or Django
    - Experience with PostgreSQL and Redis
    - Solid understanding of Docker and Kubernetes for containerisation
    - Familiarity with AWS (ECS, S3, RDS) or equivalent cloud platform
    - Experience with CI/CD pipelines (GitHub Actions or Jenkins)
    - RESTful API design and GraphQL knowledge
    - Unit testing with pytest; TDD mindset
    - Basic understanding of machine learning or data pipelines is a plus

    Responsibilities:
    - Design and implement scalable microservices
    - Collaborate with frontend (React) and data teams
    - Maintain 99.9% uptime SLAs
    - Mentor junior engineers

    Nice to have: Kafka, Terraform, Go
""").strip()

SAMPLE_RESUME_TEXT = textwrap.dedent("""
    Jane Doe
    jane.doe@email.com | github.com/janedoe | LinkedIn

    SUMMARY
    Full-stack developer with 2 years of experience building web applications.
    Comfortable with Python, JavaScript, and modern frameworks.

    EXPERIENCE
    Software Engineer — StartupXYZ (Jan 2023 – Present, 1.5 years)
    - Built REST APIs using Python and Flask
    - Developed React dashboards consuming internal APIs
    - Wrote unit tests using pytest
    - Deployed applications on AWS EC2

    Junior Developer — Freelance (Jun 2022 – Dec 2022, 6 months)
    - Created WordPress sites and small Python automation scripts

    SKILLS
    Languages: Python, JavaScript, HTML, CSS, SQL
    Frameworks: React, Flask
    Tools: Git, pytest, PostgreSQL, AWS

    EDUCATION
    B.Sc. Computer Science — XYZ University (2022)
""").strip()


# ---------------------------------------------------------------------------
# Unit tests (no server required)
# ---------------------------------------------------------------------------

def run_unit_tests():
    print("=" * 60)
    print("Running unit tests…")
    print("=" * 60)

    # --- parser tests ---
    from parser import clean_text, extract_skills_from_text

    raw = "  Hello\xa0World\n\n\n\n   test   "
    cleaned = clean_text(raw)
    assert "Hello World" in cleaned, f"clean_text failed: {cleaned!r}"
    assert cleaned.count("\n\n\n") == 0, "clean_text: too many blank lines"
    print("✓ clean_text")

    # --- matcher tests ---
    from matcher import extract_skills, compute_semantic_similarity, parse_experience_years

    skills = extract_skills("Looking for Python, Docker, and AWS experience")
    assert "python" in skills, f"extract_skills missed 'python': {skills}"
    assert "docker" in skills, f"extract_skills missed 'docker': {skills}"
    print(f"✓ extract_skills → {skills}")

    years = parse_experience_years("We need 5+ years of experience in backend")
    assert years == 5.0, f"parse_experience_years returned {years}"
    print("✓ parse_experience_years")

    sim = compute_semantic_similarity("Python developer with FastAPI", "Backend engineer Python")
    assert 0.0 <= sim <= 1.0, f"similarity out of range: {sim}"
    print(f"✓ compute_semantic_similarity → {sim:.4f}")

    # --- full match ---
    from matcher import compute_match
    result = compute_match(SAMPLE_RESUME_TEXT, SAMPLE_JD)
    assert 0 <= result.match_score <= 100
    assert isinstance(result.matched_skills, list)
    assert isinstance(result.missing_skills, list)
    print(f"✓ compute_match → score={result.match_score}, "
          f"matched={result.matched_skills}, "
          f"missing={result.missing_skills}")

    # --- analyzer ---
    from analyzer import build_full_analysis
    payload = build_full_analysis(result, SAMPLE_RESUME_TEXT, SAMPLE_JD)
    required_keys = {
        "match_score", "matched_skills", "missing_skills",
        "experience_gap", "analysis", "rejection_reasons",
        "improvement_suggestions", "meta",
    }
    missing_keys = required_keys - payload.keys()
    assert not missing_keys, f"Missing keys in payload: {missing_keys}"
    print("✓ build_full_analysis — all required keys present")
    print()
    print("Sample payload (pretty-printed):")
    print(json.dumps(payload, indent=2))

    print()
    print("All unit tests passed ✓")


# ---------------------------------------------------------------------------
# Live API tests (server must be running)
# ---------------------------------------------------------------------------

def run_live_tests(base_url: str = "http://localhost:8000"):
    import io
    import requests
    from reportlab.pdfgen import canvas as pdf_canvas  # type: ignore

    print("=" * 60)
    print(f"Running live API tests against {base_url}…")
    print("=" * 60)

    # Health check
    r = requests.get(f"{base_url}/health", timeout=10)
    r.raise_for_status()
    print(f"✓ GET /health → {r.json()}")

    # Generate a minimal in-memory PDF from SAMPLE_RESUME_TEXT
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf)
    y = 750
    for line in SAMPLE_RESUME_TEXT.splitlines():
        c.drawString(40, y, line)
        y -= 14
        if y < 50:
            c.showPage()
            y = 750
    c.save()
    buf.seek(0)

    # POST /analyze
    files = {"resume": ("jane_doe_resume.pdf", buf, "application/pdf")}
    data = {"job_description": SAMPLE_JD}
    r = requests.post(f"{base_url}/analyze", files=files, data=data, timeout=120)
    r.raise_for_status()
    payload = r.json()
    print(f"✓ POST /analyze → HTTP {r.status_code}")
    print(json.dumps(payload, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WhyNotHireMe test runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--live", action="store_true", help="Run live API tests")
    parser.add_argument("--url", default="http://localhost:8000", help="Base API URL")
    args = parser.parse_args()

    run_unit = args.unit or (not args.unit and not args.live)
    run_live = args.live

    if run_unit:
        try:
            run_unit_tests()
        except AssertionError as e:
            print(f"FAIL: {e}", file=sys.stderr)
            sys.exit(1)

    if run_live:
        try:
            run_live_tests(args.url)
        except Exception as e:
            print(f"LIVE TEST FAIL: {e}", file=sys.stderr)
            sys.exit(1)