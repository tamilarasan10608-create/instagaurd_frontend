from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)   # null for Google OAuth users
    google_id = Column(String(255), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    scans = relationship("Scan", back_populates="user", cascade="all, delete-orphan")
