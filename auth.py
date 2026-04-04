"""
auth.py — Authentication logic.

Handles:
- Password hashing and verification
- JWT token creation and validation
- Company registration and login
- API key generation
- FastAPI dependency for protected routes
"""

import os
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import get_db
from models import Company

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security    = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password[:72])


def verify_password(plain: str, hashed: str) -> bool:
    """Verify plain password against hashed version."""
    return pwd_context.verify(plain[:72], hashed)


# ---------------------------------------------------------------------------
# API Key generation
# ---------------------------------------------------------------------------

def generate_api_key() -> str:
    """
    Generate a secure random API key.
    Format: wnhm_<40 random chars>
    Example: wnhm_xK9mP2qR7vL...
    """
    chars = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(chars) for _ in range(40))
    return f"wnhm_{random_part}"


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT token.

    Args:
        data: Payload to encode (usually {"sub": company_id})
        expires_delta: How long token is valid

    Returns:
        Signed JWT string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    """
    Decode JWT token and return company_id (sub claim).
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# Pydantic schemas (request/response models)
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    company_name: str
    email:        str
    password:     str

    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "Razorpay",
                "email":        "hr@razorpay.com",
                "password":     "StrongPass123"
            }
        }


class LoginRequest(BaseModel):
    email:    str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    company_id:   str
    company_name: str
    api_key:      str


class CompanyProfile(BaseModel):
    id:             str
    company_name:   str
    email:          str
    plan:           str
    analyses_count: int
    api_key:        str
    created_at:     datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# FastAPI dependency — get current logged-in company
# ---------------------------------------------------------------------------

def get_current_company(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Company:
    """
    FastAPI dependency for protected routes.

    Extracts JWT from Authorization header,
    validates it, returns the Company object.

    Usage:
        @app.get("/protected")
        def route(company: Company = Depends(get_current_company)):
            ...
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    company_id = decode_token(credentials.credentials)
    if not company_id:
        raise credentials_exception

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company or not company.is_active:
        raise credentials_exception

    return company


# ---------------------------------------------------------------------------
# Auth service functions
# ---------------------------------------------------------------------------

def register_company(req: RegisterRequest, db: Session) -> Company:
    """
    Register a new company.

    Raises HTTPException if:
    - Email already exists
    - Password too short
    """
    # Validate password length
    if len(req.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters.",
        )

    # Check email uniqueness
    existing = db.query(Company).filter(Company.email == req.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A company with this email already exists.",
        )

    company = Company(
        company_name    = req.company_name.strip(),
        email           = req.email.lower().strip(),
        hashed_password = hash_password(req.password),
        api_key         = generate_api_key(),
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def login_company(req: LoginRequest, db: Session) -> TokenResponse:
    """
    Authenticate company and return JWT token.

    Raises HTTPException if credentials are wrong.
    """
    company = db.query(Company).filter(
        Company.email == req.email.lower().strip()
    ).first()

    if not company or not verify_password(req.password, company.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if not company.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    token = create_access_token(data={"sub": company.id})

    return TokenResponse(
        access_token = token,
        company_id   = company.id,
        company_name = company.company_name,
        api_key      = company.api_key,
    )