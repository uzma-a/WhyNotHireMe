"""
main.py — FastAPI entry point for the WhyNotHireMe API.

Async Architecture
------------------
All CPU-heavy work (PDF parsing, NLP, model inference) runs inside a
ThreadPoolExecutor so it NEVER blocks the event loop.

This means 400 users uploading simultaneously will NOT freeze each other.
Each request gets a thread; the event loop stays free to accept new ones.

Endpoints
---------
POST /analyze        Upload resume PDF + JD text → full analysis JSON
POST /analyze/async  Same but returns job_id immediately (non-blocking)
GET  /result/{id}    Poll for async result
GET  /health         Liveness + readiness probe
GET  /stats          Live server stats (requests, avg time, queue depth)

Run (development)
-----------------
    uvicorn main:app --reload --port 8000

Run (production — 4 workers, handles ~400 concurrent users)
------------------------------------------------------------
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --timeout-keep-alive 30
"""

import asyncio
import logging
import os
import tempfile
import time
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

from parser import clean_text, extract_text_from_pdf
from matcher import compute_match, get_model
from analyzer import build_full_analysis
from email_generator import generate_rejection_email, EmailRequest
from database import get_db, create_tables
from models import Company, AnalysisRecord
from auth import (
    RegisterRequest, LoginRequest,
    register_company, login_company,
    get_current_company, CompanyProfile,
)
from email_service import send_rejection_email

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("whynotHireMe")

# ---------------------------------------------------------------------------
# Thread pool
#
# CPU-bound NLP work runs here — NOT on the async event loop.
#
# Why ThreadPoolExecutor (not ProcessPoolExecutor)?
#   Threads share the loaded NLP model (singleton in matcher.py).
#   No reload cost per request. For true multi-core parallelism,
#   run multiple uvicorn workers instead (--workers 4).
#
# max_workers=None → Python auto-sizes to min(32, cpu_count + 4).
# Tune down to 4-8 if your VPS has limited RAM.
# ---------------------------------------------------------------------------

_executor = ThreadPoolExecutor(max_workers=None)

# ---------------------------------------------------------------------------
# In-memory async job store  (replace with Redis in production)
# ---------------------------------------------------------------------------

_job_store: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Live stats counters (per-worker, resets on restart)
# ---------------------------------------------------------------------------

_stats: dict = defaultdict(float)
_stats["requests_total"]     = 0
_stats["requests_success"]   = 0
_stats["requests_failed"]    = 0
_stats["total_time_seconds"] = 0.0
_stats["queue_depth"]        = 0


# ---------------------------------------------------------------------------
# App lifecycle — warm the model before the first request arrives
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    On startup: pre-load the sentence-transformer model in a thread so
    the event loop is not blocked during the slow first load.
    On shutdown: drain in-flight threads gracefully.
    """
    logger.info("Pre-loading NLP model in background thread…")
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(_executor, get_model)
        logger.info("✓ NLP model ready. Server accepting requests.")
    except Exception as exc:
        logger.error("✗ Model pre-load failed: %s — will retry on first request.", exc)

    # Create database tables on startup
    logger.info("Creating database tables if not exist…")
    create_tables()
    logger.info("✓ Database ready.")
    yield
    logger.info("Draining thread pool (waiting for in-flight tasks)…")
    _executor.shutdown(wait=True)
    logger.info("Shutdown complete.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="WhyNotHireMe API",
    description=(
        "AI-powered resume analysis and hiring transparency system. "
        "Non-blocking async architecture — handles hundreds of concurrent users."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Config (override via .env)
# ---------------------------------------------------------------------------

MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_MB",   "10"))
MAX_JD_CHARS    = int(os.getenv("MAX_JD_CHARS", "20000"))
JOB_TTL_SECONDS = int(os.getenv("JOB_TTL",      "300"))  # async results live 5 min


# ---------------------------------------------------------------------------
# Sync helpers — called from the thread pool, never from the event loop
# ---------------------------------------------------------------------------

def _validate_pdf_bytes(raw_bytes: bytes) -> None:
    """Raise HTTPException if bytes are not a valid PDF within size limits."""
    size_mb = len(raw_bytes) / (1024 * 1024)
    if size_mb > MAX_PDF_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF exceeds {MAX_PDF_SIZE_MB} MB limit ({size_mb:.1f} MB received).",
        )
    if not raw_bytes.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Uploaded file does not appear to be a valid PDF.",
        )


def _run_full_pipeline(raw_bytes: bytes, job_description: str) -> dict:
    """
    Complete synchronous analysis pipeline.

    Designed to run inside ThreadPoolExecutor — it is intentionally
    sync so asyncio does not need to manage CPU-bound waits.

    Steps
    -----
    1. Validate PDF bytes
    2. Write temp file → extract text → delete temp file
    3. Clean both texts
    4. Compute semantic match + skill gap
    5. Build full analysis payload
    6. Return serialisable dict
    """
    t_start = time.perf_counter()

    # 1 — validate
    _validate_pdf_bytes(raw_bytes)

    # 2 — extract text
    tmp_path: Optional[str] = None
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.write(raw_bytes)
        tmp.close()
        tmp_path = tmp.name
        resume_raw = extract_text_from_pdf(tmp_path)
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    # 3 — clean
    resume_clean = clean_text(resume_raw)
    jd_clean     = clean_text(job_description)

    if len(resume_clean) < 50:
        raise ValueError(
            "Resume text too short after extraction. "
            "The PDF may be image-only or contain minimal text."
        )

    # 4 — match
    match_result = compute_match(resume_clean, jd_clean)

    # 5 — analyse
    payload = build_full_analysis(match_result, resume_clean, jd_clean)

    # 6 — attach processing metadata
    elapsed = round(time.perf_counter() - t_start, 3)
    payload["_meta"] = {
        "processing_time_seconds": elapsed,
        "resume_char_count":       len(resume_clean),
        "jd_char_count":           len(jd_clean),
    }

    logger.info(
        "Pipeline complete — score=%d | time=%.2fs | matched=%d | missing=%d",
        payload["match_score"], elapsed,
        len(payload["matched_skills"]), len(payload["missing_skills"]),
    )
    return payload


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", summary="Liveness & readiness probe")
async def health_check():
    """
    Safe to poll every 30 s from a load balancer.
    Never triggers a model load.
    Returns model_loaded=true once the warm-up completes.
    """
    model_ready = False
    try:
        from matcher import _model
        model_ready = _model is not None
    except Exception:
        pass

    return {
        "status":       "ok",
        "service":      "WhyNotHireMe",
        "version":      app.version,
        "model_loaded": model_ready,
        "workers":      os.getenv("WEB_CONCURRENCY", "1"),
    }


@app.get("/stats", summary="Live server statistics")
async def server_stats():
    """
    Per-worker request counters and latency averages.
    Use for lightweight monitoring without a full APM setup.
    """
    total = _stats["requests_total"] or 1
    return {
        "requests_total":     int(_stats["requests_total"]),
        "requests_success":   int(_stats["requests_success"]),
        "requests_failed":    int(_stats["requests_failed"]),
        "avg_time_seconds":   round(_stats["total_time_seconds"] / total, 3),
        "queue_depth":        int(_stats["queue_depth"]),
        "pending_async_jobs": len([j for j in _job_store.values()
                                   if j["status"] == "pending"]),
    }


# ---------------------------------------------------------------------------
# AUTH ROUTES
# ---------------------------------------------------------------------------

@app.post("/auth/register", summary="Register a new company", tags=["Auth"])
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register your company. Returns API key on success."""
    company = register_company(req, db)
    return {
        "message":      "Company registered successfully!",
        "company_id":   company.id,
        "company_name": company.company_name,
        "email":        company.email,
        "api_key":      company.api_key,
        "plan":         company.plan,
    }


@app.post("/auth/login", summary="Login and get JWT token", tags=["Auth"])
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password.
    Returns JWT token — use in Authorization: Bearer <token> header.
    """
    return login_company(req, db)


@app.get("/auth/me", summary="Get current company profile", tags=["Auth"])
async def get_me(company: Company = Depends(get_current_company)):
    """Returns logged-in company profile. Requires JWT token."""
    return {
        "id":             company.id,
        "company_name":   company.company_name,
        "email":          company.email,
        "plan":           company.plan,
        "analyses_count": company.analyses_count,
        "api_key":        company.api_key,
        "created_at":     company.created_at.isoformat(),
    }


@app.get("/auth/history", summary="Get all past analyses", tags=["Auth"])
async def get_history(
    company: Company = Depends(get_current_company),
    db:      Session = Depends(get_db),
    limit:   int = 20,
    offset:  int = 0,
):
    """Returns all analyses run by this company. Paginated."""
    records = (
        db.query(AnalysisRecord)
        .filter(AnalysisRecord.company_id == company.id)
        .order_by(AnalysisRecord.created_at.desc())
        .offset(offset).limit(limit).all()
    )
    return {
        "total": company.analyses_count,
        "records": [
            {
                "id":              r.id,
                "candidate_name":  r.candidate_name,
                "candidate_email": r.candidate_email,
                "role_title":      r.role_title,
                "match_score":     r.match_score,
                "matched_skills":  r.matched_skills,
                "missing_skills":  r.missing_skills,
                "email_generated": r.email_generated,
                "email_sent":      r.email_sent,
                "created_at":      r.created_at.isoformat(),
            }
            for r in records
        ],
    }


# ---------------------------------------------------------------------------
# POST /analyze — synchronous (awaits result before responding)
#
# The heavy work still runs in a thread so other requests are never blocked.
# Good for direct API calls, Swagger UI, and the React frontend.
# ---------------------------------------------------------------------------

@app.post(
    "/analyze",
    summary="Analyse resume (responds when complete)",
    response_description="Full match report JSON",
)
async def analyze_resume(
    resume: UploadFile = File(..., description="Resume PDF (max 10 MB)"),
    job_description: str = Form(..., description="Full JD text (max 20 000 chars)"),
):
    """
    Upload resume + JD → receive full analysis in one request.

    The NLP pipeline runs in a thread pool, so 400 users can hit this
    endpoint simultaneously without blocking each other.

    If you need fire-and-forget behaviour use POST /analyze/async instead.
    """
    # Fast input validation on the event loop (no I/O cost)
    if not job_description or not job_description.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="job_description cannot be empty.",
        )
    if len(job_description) > MAX_JD_CHARS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"job_description exceeds {MAX_JD_CHARS} character limit.",
        )

    # Async file read — does not block the event loop
    raw_bytes = await resume.read()

    _stats["requests_total"] += 1
    _stats["queue_depth"]    += 1

    loop = asyncio.get_event_loop()
    try:
        # ── KEY LINE ──────────────────────────────────────────────────────
        # run_in_executor offloads _run_full_pipeline to a thread.
        # The event loop is FREE to handle other requests while this runs.
        # Without this, one slow PDF would freeze all other users.
        # ─────────────────────────────────────────────────────────────────
        payload = await loop.run_in_executor(
            _executor,
            _run_full_pipeline,
            raw_bytes,
            job_description,
        )

        _stats["requests_success"]   += 1
        _stats["total_time_seconds"] += payload["_meta"]["processing_time_seconds"]
        return JSONResponse(content=payload)

    except HTTPException:
        _stats["requests_failed"] += 1
        raise  # re-raise validation errors as-is

    except FileNotFoundError as exc:
        _stats["requests_failed"] += 1
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    except ValueError as exc:
        _stats["requests_failed"] += 1
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )

    except Exception as exc:
        _stats["requests_failed"] += 1
        logger.exception("Unexpected pipeline error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {exc}",
        )
    finally:
        _stats["queue_depth"] -= 1


# ---------------------------------------------------------------------------
# POST /analyze/async — fire and forget, result polled via /result/{job_id}
#
# Returns in ~50 ms regardless of analysis time.
# Best for high-traffic scenarios (400+ simultaneous users).
# ---------------------------------------------------------------------------

@app.post(
    "/analyze/async",
    summary="Analyse resume (returns job_id immediately)",
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_resume_async(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
):
    """
    Instant acknowledgement endpoint.

    1. Call this → get job_id in ~50 ms.
    2. Poll GET /result/{job_id} every 2 s.
    3. When status == 'done', the full report is in data.

    No user ever waits at the HTTP level, even during peak traffic.
    """
    if not job_description or not job_description.strip():
        raise HTTPException(status_code=422, detail="job_description cannot be empty.")
    if len(job_description) > MAX_JD_CHARS:
        raise HTTPException(status_code=422, detail="job_description too long.")

    raw_bytes = await resume.read()
    job_id    = str(uuid.uuid4())

    _job_store[job_id] = {
        "status":     "pending",
        "created_at": time.time(),
        "result":     None,
        "error":      None,
    }
    _stats["queue_depth"] += 1

    loop = asyncio.get_event_loop()

    async def _background_task():
        try:
            result = await loop.run_in_executor(
                _executor, _run_full_pipeline, raw_bytes, job_description
            )
            _job_store[job_id]["status"] = "done"
            _job_store[job_id]["result"] = result
            _stats["requests_success"] += 1
        except Exception as exc:
            logger.error("Async job %s failed: %s", job_id, exc)
            _job_store[job_id]["status"] = "failed"
            _job_store[job_id]["error"]  = str(exc)
            _stats["requests_failed"]   += 1
        finally:
            _stats["queue_depth"] -= 1

    # Schedule without blocking this response
    asyncio.create_task(_background_task())

    return {
        "job_id":   job_id,
        "status":   "pending",
        "poll_url": f"/result/{job_id}",
        "message":  "Analysis started. Poll poll_url every 2 seconds.",
    }


@app.get("/result/{job_id}", summary="Poll for async job result")
async def get_result(job_id: str):
    """
    Poll after calling POST /analyze/async.

    Responses
    ---------
    - status='pending' → still running, try again in 2 s
    - status='done'    → full report is in 'data'
    - status='failed'  → error details in 'error'
    """
    job = _job_store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found. It may have expired (TTL: {JOB_TTL_SECONDS}s).",
        )

    # Auto-expire stale pending jobs
    if time.time() - job["created_at"] > JOB_TTL_SECONDS and job["status"] == "pending":
        _job_store[job_id]["status"] = "failed"
        _job_store[job_id]["error"]  = "Job timed out."

    response = {"job_id": job_id, "status": job["status"]}

    if job["status"] == "done":
        response["data"] = job["result"]
        del _job_store[job_id]          # free memory after delivery

    elif job["status"] == "failed":
        response["error"] = job["error"]
        del _job_store[job_id]

    return response


# ---------------------------------------------------------------------------
# POST /generate-rejection-email
# Company-facing endpoint: takes resume + JD + company details,
# returns a ready-to-send personalised rejection email with feedback.
# ---------------------------------------------------------------------------

@app.post(
    "/generate-rejection-email",
    summary="Generate a humane rejection email with candidate feedback",
    response_description="Subject line, plain text body, and HTML email body",
)
async def generate_rejection_email_endpoint(
    resume:           UploadFile = File(...,  description="Candidate resume PDF"),
    job_description:  str        = Form(...,  description="Full job description text"),
    candidate_name:   str        = Form(...,  description="Candidate full name e.g. Uzma Aasiya"),
    role_title:       str        = Form(...,  description="Role they applied for e.g. Backend Engineer"),
    company_name:     str        = Form(...,  description="Your company name e.g. Razorpay"),
    hiring_manager:   str        = Form("",   description="Hiring manager name (optional)"),
    candidate_email:  str        = Form("",   description="Candidate email address (optional, for display)"),
):
    """
    The core WhyNotHireMe feature.

    A company uploads the candidate's resume + their JD, provides basic
    details, and receives a fully written rejection email that:

    - Is warm, respectful, and human in tone
    - Includes the candidate's match score
    - Lists their strengths honestly
    - Explains exactly where the gap was
    - Gives specific, actionable improvement steps
    - Is ready to copy-paste and send immediately

    Returns both plain text and HTML versions of the email.
    """
    # Validate inputs
    if not job_description.strip():
        raise HTTPException(status_code=422, detail="job_description cannot be empty.")
    if not candidate_name.strip():
        raise HTTPException(status_code=422, detail="candidate_name cannot be empty.")
    if not role_title.strip():
        raise HTTPException(status_code=422, detail="role_title cannot be empty.")
    if not company_name.strip():
        raise HTTPException(status_code=422, detail="company_name cannot be empty.")
    if len(job_description) > MAX_JD_CHARS:
        raise HTTPException(status_code=422, detail="job_description too long.")

    raw_bytes = await resume.read()

    _stats["requests_total"] += 1
    _stats["queue_depth"]    += 1

    def _pipeline_with_email():
        """Run full analysis + generate email — all in one thread."""
        # Step 1: run the standard analysis pipeline
        analysis = _run_full_pipeline(raw_bytes, job_description)

        # Step 2: reconstruct MatchResult from payload for email generator
        from matcher import MatchResult
        match_result = MatchResult(
            match_score        = analysis["match_score"],
            matched_skills     = analysis["matched_skills"],
            missing_skills     = analysis["missing_skills"],
            extra_skills       = analysis["extra_skills"],
            experience_gap     = analysis["experience_gap"],
            semantic_similarity= analysis["meta"]["semantic_similarity"],
            skill_coverage     = analysis["meta"]["skill_coverage"],
        )

        # Step 3: generate the rejection email
        req = EmailRequest(
            candidate_name  = candidate_name.strip(),
            role_title      = role_title.strip(),
            company_name    = company_name.strip(),
            match_result    = match_result,
            hiring_manager  = hiring_manager.strip() or None,
            candidate_email = candidate_email.strip() or None,
        )
        email = generate_rejection_email(req)

        return {
            "analysis": analysis,
            "email":    email,
        }

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(_executor, _pipeline_with_email)
        _stats["requests_success"]   += 1
        _stats["total_time_seconds"] += result["analysis"]["_meta"]["processing_time_seconds"]

        logger.info(
            "Rejection email generated — candidate=%s, role=%s, score=%d",
            candidate_name, role_title, result["analysis"]["match_score"],
        )
        return JSONResponse(content=result)

    except HTTPException:
        _stats["requests_failed"] += 1
        raise
    except ValueError as exc:
        _stats["requests_failed"] += 1
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        _stats["requests_failed"] += 1
        logger.exception("Email generation error")
        raise HTTPException(status_code=500, detail=f"Email generation failed: {exc}")
    finally:
        _stats["queue_depth"] -= 1


# ---------------------------------------------------------------------------
# POST /send-rejection-email
# Generate + SEND email directly to candidate via SendGrid
# ---------------------------------------------------------------------------

@app.post(
    "/send-rejection-email",
    summary="Generate AND send rejection email to candidate",
    tags=["Email"],
)
async def send_rejection_email_endpoint(
    resume:           UploadFile = File(...),
    job_description:  str        = Form(...),
    candidate_name:   str        = Form(...),
    candidate_email:  str        = Form(...),   # Required for sending
    role_title:       str        = Form(...),
    company_name:     str        = Form(...),
    hiring_manager:   str        = Form(""),
    db:               Session    = Depends(get_db),
    company:          Company    = Depends(get_current_company),
):
    """
    The full pipeline — analyze + generate + SEND.

    Unlike /generate-rejection-email which only returns the email text,
    this endpoint actually delivers the email to the candidate's inbox
    via SendGrid.

    Requires:
    - Valid JWT token (company must be logged in)
    - SENDGRID_API_KEY in .env
    - candidate_email is mandatory (we need to know where to send!)

    Saves delivery status to database automatically.
    """
    if not candidate_email or "@" not in candidate_email:
        raise HTTPException(status_code=422, detail="Valid candidate_email is required to send email.")
    if not job_description.strip():
        raise HTTPException(status_code=422, detail="job_description cannot be empty.")

    raw_bytes = await resume.read()

    _stats["requests_total"] += 1
    _stats["queue_depth"]    += 1

    def _full_pipeline():
        # Step 1 — analyze
        analysis = _run_full_pipeline(raw_bytes, job_description)

        # Step 2 — build MatchResult
        from matcher import MatchResult
        match_result = MatchResult(
            match_score         = analysis["match_score"],
            matched_skills      = analysis["matched_skills"],
            missing_skills      = analysis["missing_skills"],
            extra_skills        = analysis["extra_skills"],
            experience_gap      = analysis["experience_gap"],
            semantic_similarity = analysis["meta"]["semantic_similarity"],
            skill_coverage      = analysis["meta"]["skill_coverage"],
        )

        # Step 3 — generate email
        req = EmailRequest(
            candidate_name  = candidate_name.strip(),
            role_title      = role_title.strip(),
            company_name    = company_name.strip(),
            match_result    = match_result,
            hiring_manager  = hiring_manager.strip() or None,
            candidate_email = candidate_email.strip(),
        )
        email = generate_rejection_email(req)

        # Step 4 — SEND via SendGrid
        send_result = send_rejection_email(
            candidate_email = candidate_email.strip(),
            candidate_name  = candidate_name.strip(),
            email_data      = email,
            company_name    = company_name.strip(),
        )

        return analysis, email, send_result

    loop = asyncio.get_event_loop()
    try:
        analysis, email_data, send_result = await loop.run_in_executor(
            _executor, _full_pipeline
        )

        # Save to database
        record = AnalysisRecord(
            company_id              = company.id,
            candidate_name          = candidate_name.strip(),
            candidate_email         = candidate_email.strip(),
            role_title              = role_title.strip(),
            match_score             = analysis["match_score"],
            semantic_similarity     = analysis["meta"]["semantic_similarity"],
            skill_coverage          = analysis["meta"]["skill_coverage"],
            matched_skills          = analysis["matched_skills"],
            missing_skills          = analysis["missing_skills"],
            extra_skills            = analysis["extra_skills"],
            experience_gap          = analysis["experience_gap"],
            analysis_summary        = analysis["analysis"],
            rejection_reasons       = analysis["rejection_reasons"],
            improvement_suggestions = analysis["improvement_suggestions"],
            resume_char_count       = analysis["_meta"]["resume_char_count"],
            jd_char_count           = analysis["_meta"]["jd_char_count"],
            processing_time         = analysis["_meta"]["processing_time_seconds"],
            email_generated         = True,
            email_sent              = send_result["success"],
        )
        db.add(record)

        # Update company analysis count
        company.analyses_count += 1
        db.commit()

        _stats["requests_success"] += 1

        logger.info(
            "Rejection email %s → %s | score=%d | sent=%s",
            company_name, candidate_email,
            analysis["match_score"], send_result["success"],
        )

        return JSONResponse(content={
            "analysis":    analysis,
            "email":       email_data,
            "delivery":    send_result,
            "record_id":   record.id,
            "message":     "Email sent successfully!" if send_result["success"]
                           else f"Email generated but not sent: {send_result['message']}",
        })

    except HTTPException:
        _stats["requests_failed"] += 1
        raise
    except ValueError as exc:
        _stats["requests_failed"] += 1
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        _stats["requests_failed"] += 1
        logger.exception("Send email pipeline error")
        raise HTTPException(status_code=500, detail=f"Failed: {exc}")
    finally:
        _stats["queue_depth"] -= 1


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    is_dev = os.getenv("ENV", "development") == "development"

    uvicorn.run(
        "main:app",
        host              = "0.0.0.0",
        port              = int(os.getenv("PORT", "8000")),
        reload            = is_dev,
        # In production set ENV=production and WEB_CONCURRENCY=4
        workers           = 1 if is_dev else int(os.getenv("WEB_CONCURRENCY", "4")),
        log_level         = "info",
        timeout_keep_alive = 30,    # keep connections alive for async polling
    )