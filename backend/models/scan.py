from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime, timezone
from database import Base


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    SCRAPING = "scraping"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    instagram_username = Column(String(255), nullable=False, index=True)
    status = Column(SAEnum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    celery_task_id = Column(String(255), nullable=True)

    max_posts = Column(Integer, default=50, nullable=False)
    total_posts = Column(Integer, default=0)
    analyzed_posts = Column(Integer, default=0)   # images only (videos skipped)
    suspicious_count = Column(Integer, default=0)
    clean_count = Column(Integer, default=0)
    avg_scan_duration_ms = Column(Float, default=0.0)

    error_message = Column(String(1024), nullable=True)
    report_hash = Column(String(64), nullable=True, index=True)
    pdf_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="scans")
    results = relationship(
        "PostResult",
        back_populates="scan",
        cascade="all, delete-orphan",
        order_by="PostResult.post_index",
    )