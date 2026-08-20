from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from app.db.models.base import Base


class GoldenRecord(Base):
    """Unified customer identity with survivorship-resolved attributes."""

    __tablename__ = "golden_records"

    id = Column(Integer, primary_key=True, index=True)
    pan = Column(String(10), nullable=True, index=True)
    mobile = Column(String(10), nullable=True)
    email = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    dob = Column(String(10), nullable=True)
    city = Column(String(100), nullable=True)
    segment = Column(String(50), nullable=True)

    # Provenance: attribute-level survivorship tracking
    provenance = Column(JSONB, nullable=True)

    # Aggregated financials
    total_relationship_value = Column(Float, default=0.0)
    products_held = Column(JSONB, nullable=True)  # array of product objects
    source_systems = Column(ARRAY(String), nullable=True)
    source_record_count = Column(Integer, default=0)

    # Match metadata
    match_confidence = Column(Float, nullable=True)
    confidence_breakdown = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
