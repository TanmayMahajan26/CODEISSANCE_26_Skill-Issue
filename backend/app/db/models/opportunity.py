from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from app.db.models.base import Base


class OpportunityStatus(str, enum.Enum):
    NEW = "NEW"
    VIEWED = "VIEWED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    CONVERTED = "CONVERTED"
    DISMISSED = "DISMISSED"


class Opportunity(Base):
    """Explainable product recommendation opportunities for customers."""

    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    golden_record_id = Column(Integer, ForeignKey("golden_records.id"), nullable=False, index=True)
    product_name = Column(String(100), nullable=False)
    product_category = Column(String(100), nullable=False)  # e.g., Mutual Fund, Loan, Insurance
    status = Column(SAEnum(OpportunityStatus), nullable=False, default=OpportunityStatus.NEW)

    # Scores
    score = Column(Float, nullable=False, default=0.0)
    score_breakdown = Column(JSONB, nullable=True)  # breakdown of relationship value, affinity, etc.

    # RAG Explanations
    explanation = Column(String, nullable=True)  # detailed AI reasoning explanation
    insights = Column(JSONB, nullable=True)  # structured key metrics, e.g., value gap, tenure

    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
