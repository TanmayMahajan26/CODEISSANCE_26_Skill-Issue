from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from app.db.models.base import Base


class ReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"  # Auto-merge or Manager confirmed merge
    REJECTED = "REJECTED"  # Confirmed separate identities


class ReviewQueueItem(Base):
    """Items requiring Manager review for identity resolution matches in the gray area."""

    __tablename__ = "review_queue"

    id = Column(Integer, primary_key=True, index=True)
    source_record_a_id = Column(Integer, ForeignKey("source_records.id"), nullable=False)
    source_record_b_id = Column(Integer, ForeignKey("source_records.id"), nullable=False)

    match_score = Column(JSONB, nullable=True)  # breakdown of attributes and overall score
    ai_suggestions = Column(JSONB, nullable=True)  # conflict analysis and suggested resolution

    status = Column(SAEnum(ReviewStatus), nullable=False, default=ReviewStatus.PENDING)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
