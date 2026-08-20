from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from app.db.models.base import Base


class IdentityEdge(Base):
    """Edge connecting two source records with match confidence."""

    __tablename__ = "identity_edges"

    id = Column(Integer, primary_key=True, index=True)
    source_record_a_id = Column(Integer, ForeignKey("source_records.id"), nullable=False, index=True)
    source_record_b_id = Column(Integer, ForeignKey("source_records.id"), nullable=False, index=True)
    golden_record_id = Column(Integer, ForeignKey("golden_records.id"), nullable=True, index=True)

    match_phase = Column(String(30), nullable=False)  # deterministic, probabilistic, semantic
    confidence = Column(Float, nullable=False)
    confidence_breakdown = Column(JSONB, nullable=True)  # waterfall scores per attribute

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
