"""
ReviewCase ORM Model.

Captures pairs flagged for human review — tracks status, priority, review_type,
reviewer, AI suggestions, notes, and resolution timestamps.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, Enum, ForeignKey, Text, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReviewPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReviewType(str, enum.Enum):
    LOW_CONFIDENCE_MATCH = "LOW_CONFIDENCE_MATCH"
    ATTRIBUTE_CONFLICT = "ATTRIBUTE_CONFLICT"
    DUPLICATE_SUSPECT = "DUPLICATE_SUSPECT"
    AI_FLAGGED = "AI_FLAGGED"


class ReviewCase(Base):
    __tablename__ = "review_cases"

    id = Column(Integer, primary_key=True, index=True)
    match_decision_id = Column(
        Integer, ForeignKey("match_decisions.id"), nullable=False, unique=True
    )

    priority = Column(Enum(ReviewPriority), default=ReviewPriority.MEDIUM)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, index=True)
    review_type = Column(Enum(ReviewType), default=ReviewType.LOW_CONFIDENCE_MATCH, nullable=False)

    reviewer = Column(String(100))
    assigned_to = Column(String(100))
    review_notes = Column(Text)
    ai_suggestion = Column(Text)

    details = Column(JSONB)
    source_record_ids = Column(JSONB)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime)

    # Relationships
    match_decision = relationship("MatchDecision", back_populates="review_case")

    def __repr__(self) -> str:
        return (
            f"<ReviewCase {self.id} decision={self.match_decision_id} "
            f"type={self.review_type} status={self.status}>"
        )
