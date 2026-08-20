"""
MatchDecision ORM Model.

Stores every pairwise matching decision with full feature breakdown,
final score, and explainable reasoning.
Canonical pair ordering (min(a,b), max(a,b)) is enforced for database uniqueness.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Enum, ForeignKey, UniqueConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Decision(str, enum.Enum):
    MATCH = "MATCH"
    REVIEW = "REVIEW"
    NON_MATCH = "NON_MATCH"


class MatchDecision(Base):
    __tablename__ = "match_decisions"
    __table_args__ = (
        UniqueConstraint("record_a_id", "record_b_id", name="uq_match_decisions_canonical_pair"),
        Index("ix_match_decisions_pair", "record_a_id", "record_b_id", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    record_a_id = Column(
        Integer, ForeignKey("source_records.id"), nullable=False, index=True
    )
    record_b_id = Column(
        Integer, ForeignKey("source_records.id"), nullable=False, index=True
    )

    # ── Feature flags / scores ───────────────────────────────────
    pan_match = Column(Float, default=0.0)
    mobile_match = Column(Float, default=0.0)
    email_match = Column(Float, default=0.0)
    name_similarity = Column(Float, default=0.0)
    name_semantic_similarity = Column(Float, default=0.0)
    dob_match = Column(Float, default=0.0)
    city_similarity = Column(Float, default=0.0)
    segment_match = Column(Float, default=0.0)

    final_score = Column(Float, nullable=False)
    decision = Column(Enum(Decision), nullable=False)

    reasoning = Column(JSONB)
    ai_explanation = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    record_a = relationship("SourceRecord", foreign_keys=[record_a_id])
    record_b = relationship("SourceRecord", foreign_keys=[record_b_id])
    review_case = relationship("ReviewCase", back_populates="match_decision", uselist=False)

    def __repr__(self) -> str:
        return (
            f"<MatchDecision {self.id} A={self.record_a_id} B={self.record_b_id} "
            f"score={self.final_score} decision={self.decision}>"
        )
