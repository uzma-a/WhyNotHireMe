"""
models.py — Database table definitions.

Two tables:
1. Company     — companies that use the tool
2. AnalysisRecord — every resume analysis saved permanently
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float,
    DateTime, Text, ForeignKey, Boolean, JSON
)
from sqlalchemy.orm import relationship
from database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Company(Base):
    """
    Companies that register and use WhyNotHireMe.

    Each company gets:
    - Their own login (email + password)
    - API key for direct integration
    - History of all analyses they ran
    """
    __tablename__ = "companies"

    id              = Column(String, primary_key=True, default=generate_uuid)
    company_name    = Column(String(200), nullable=False)
    email           = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(500), nullable=False)
    api_key         = Column(String(100), unique=True, index=True)
    is_active       = Column(Boolean, default=True)
    plan            = Column(String(50), default="free")  # free / pro / enterprise
    analyses_count  = Column(Integer, default=0)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship — one company has many analysis records
    analyses = relationship("AnalysisRecord", back_populates="company")

    def __repr__(self):
        return f"<Company {self.company_name} ({self.email})>"


class AnalysisRecord(Base):
    """
    Every resume analysis saved permanently.

    Stores:
    - Who ran it (company)
    - Candidate details
    - Full analysis result
    - Whether email was sent
    """
    __tablename__ = "analysis_records"

    id               = Column(String, primary_key=True, default=generate_uuid)
    company_id       = Column(String, ForeignKey("companies.id"), nullable=False)

    # Candidate info
    candidate_name   = Column(String(200))
    candidate_email  = Column(String(200))
    role_title       = Column(String(200))

    # Scores
    match_score      = Column(Integer)
    semantic_similarity = Column(Float)
    skill_coverage   = Column(Float)

    # Skills (stored as JSON arrays)
    matched_skills   = Column(JSON, default=list)
    missing_skills   = Column(JSON, default=list)
    extra_skills     = Column(JSON, default=list)

    # Full analysis text
    experience_gap   = Column(Text)
    analysis_summary = Column(Text)
    rejection_reasons = Column(JSON, default=list)
    improvement_suggestions = Column(JSON, default=list)

    # Email tracking
    email_generated  = Column(Boolean, default=False)
    email_sent       = Column(Boolean, default=False)
    email_sent_at    = Column(DateTime, nullable=True)

    # Metadata
    resume_char_count = Column(Integer)
    jd_char_count     = Column(Integer)
    processing_time   = Column(Float)
    created_at        = Column(DateTime, default=datetime.utcnow)

    # Relationship
    company = relationship("Company", back_populates="analyses")

    def __repr__(self):
        return f"<Analysis {self.candidate_name} — {self.role_title} — {self.match_score}/100>"