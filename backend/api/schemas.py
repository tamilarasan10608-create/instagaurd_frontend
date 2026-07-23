from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: UUID
    full_name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Scan ──────────────────────────────────────────────────────────────────────

class StartScanRequest(BaseModel):
    instagram_username: str
    max_posts: int = 50

    @field_validator("instagram_username")
    @classmethod
    def strip_at(cls, v):
        return v.lstrip("@").strip()

    @field_validator("max_posts")
    @classmethod
    def clamp_posts(cls, v):
        if v < 1:
            raise ValueError("max_posts must be at least 1")
        if v > 200:
            raise ValueError("max_posts cannot exceed 200")
        return v


class ScanOut(BaseModel):
    id: UUID
    instagram_username: str
    status: str
    max_posts: int
    total_posts: int
    analyzed_posts: int
    suspicious_count: int
    clean_count: int
    avg_scan_duration_ms: float
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    # Chain of Custody
    report_hash: Optional[str] = None   # ← add this
    pdf_hash: Optional[str] = None      # ← add this

    model_config = {"from_attributes": True}
    


class PostResultOut(BaseModel):
    id: UUID
    post_index: int
    instagram_post_url: Optional[str]
    image_url: Optional[str]
    thumbnail_b64: Optional[str]
    is_suspicious: bool
    confidence_score: float
    scan_duration_ms: float
    created_at: datetime

    model_config = {"from_attributes": True}


class ScanDetailOut(ScanOut):
    results: List[PostResultOut] = []
class SealResponse(BaseModel):
    """Returned by POST /api/scans/{id}/seal"""
    scan_id: UUID
    report_hash: str        # SHA-256 of the JSON report payload
    pdf_hash: str           # SHA-256 of the exported PDF bytes
    sealed_at: datetime
    message: str

TokenResponse.model_rebuild()
