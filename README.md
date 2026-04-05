---
title: WhyNotHireMe
emoji: 🎯
colorFrom: yellow
colorTo: green
sdk: docker
pinned: false
---

# WhyNotHireMe 🚀

**AI-Powered Resume Analysis & Hiring Transparency System**

Upload a resume and a job description — get back a detailed match score, skill gap analysis, rejection reasons, and actionable improvement suggestions.

---

## Architecture

```
whynotHireMe/
├── main.py          ← FastAPI app + endpoint definitions
├── parser.py        ← PDF text extraction + text cleaning
├── matcher.py       ← Skill extraction + semantic similarity scoring
├── analyzer.py      ← AI explanation generation (HuggingFace + rule-based)
├── requirements.txt
├── Dockerfile
├── .env.example
└── test_api.py      ← Unit + integration tests
```

### Processing pipeline

```
PDF Upload + JD text
        │
        ▼
  [parser.py]
  extract_text_from_pdf()
  clean_text()
  extract_sections()
        │
        ▼
  [matcher.py]
  extract_skills(resume)   ←── Taxonomy-based keyword matching
  extract_skills(jd)
  compute_semantic_similarity()  ←── sentence-transformers all-MiniLM-L6-v2
  compute_match()
        │
        ▼
  [analyzer.py]
  generate_analysis_summary()   ←── flan-t5-base (with rule-based fallback)
  _rule_based_rejection_reasons()
  _rule_based_suggestions()
  build_full_analysis()
        │
        ▼
  JSON Response
```

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/yourname/whynotHireMe.git
cd whynotHireMe

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# edit .env if needed (defaults work for local dev)
```

### 3. Run the server

```bash
uvicorn main:app --reload --port 8000
```

Server starts at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

### Run the html file (Frontend)

```bash
python -m http.server 3000
```

### 4. Test with curl

```bash
# Health check
curl http://localhost:8000/health

# Analyse a resume
curl -X POST http://localhost:8000/analyze \
  -F "resume=@/path/to/resume.pdf" \
  -F "job_description=We are looking for a Python developer with 3+ years of experience in FastAPI, Docker, and AWS..."
```

### 5. Run tests

```bash
# Unit tests only (no server needed)
python test_api.py --unit

# Live API tests (server must be running)
python test_api.py --live
```

---

## API Reference

### `GET /health`

```json
{
  "status": "ok",
  "service": "WhyNotHireMe",
  "version": "1.0.0",
  "model_loaded": true
}
```

### `POST /analyze`

**Request** — `multipart/form-data`

| Field             | Type   | Description                       |
|-------------------|--------|-----------------------------------|
| `resume`          | File   | Resume in PDF format (max 10 MB)  |
| `job_description` | string | Full JD text (max 20 000 chars)   |

**Response** — `200 OK`

```json
{
  "match_score": 72,
  "matched_skills": ["python", "react", "postgresql", "aws", "pytest"],
  "missing_skills": ["docker", "kubernetes", "graphql", "kafka"],
  "extra_skills": ["flask", "javascript"],
  "experience_gap": "Required 4+ years; resume indicates ~2 years (2-year gap).",
  "analysis": "Candidate demonstrates solid Python and frontend capabilities but lacks containerisation and DevOps experience critical for this senior role.",
  "rejection_reasons": [
    "The following key skills listed in the job description are absent: docker, kubernetes, graphql, kafka.",
    "Experience gap detected: Required 4+ years; resume indicates ~2 years."
  ],
  "improvement_suggestions": [
    "Learn Docker by containerising a personal project. A simple 3-tier app with docker-compose is a great starting point.",
    "Complete a hands-on Kubernetes tutorial (killer.sh) and deploy a project to a managed K8s cluster.",
    "Consider tailoring your resume keywords to mirror the exact language used in the JD."
  ],
  "meta": {
    "semantic_similarity": 0.6823,
    "skill_coverage": 0.5556,
    "total_jd_skills_detected": 9,
    "total_resume_skills_detected": 7
  },
  "_meta": {
    "processing_time_seconds": 1.243,
    "resume_char_count": 1842,
    "jd_char_count": 987
  }
}
```

---

## Docker

```bash
# Build
docker build -t whynotHireMe .

# Run
docker run -p 8000:8000 whynotHireMe
```

---

## Scoring formula

```
match_score = round((0.55 × skill_coverage + 0.45 × semantic_similarity) × 100)
```

- **skill_coverage** = `matched_skills / total_jd_skills` (keyword taxonomy)
- **semantic_similarity** = cosine similarity of mean sentence embeddings (`all-MiniLM-L6-v2`)

---

## Extending the skill taxonomy

Edit the `SKILL_TAXONOMY` dict in `matcher.py`:

```python
SKILL_TAXONOMY["your_domain"] = ["tool_a", "framework_b", "language_c"]
```

---

## Phase 2 Roadmap

- [ ] Upgrade LLM to Mistral-7B-Instruct (quantised GGUF) for richer explanations
- [ ] Add resume section scoring (education, projects, certifications separately)
- [ ] ATS keyword density analysis
- [ ] React + Tailwind frontend
- [ ] HuggingFace Spaces deployment with Gradio wrapper

---

## License

MIT