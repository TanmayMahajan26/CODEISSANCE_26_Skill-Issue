from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Date, Float, Text
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from app.db.models.base import Base


class SourceRecord(Base):
    """Individual customer record from a source financial system."""

    __tablename__ = "source_records"

    id = Column(Integer, primary_key=True, index=True)
    source_system = Column(String(50), nullable=False, index=True)  # Equity, MF, Insurance, Loans, Wealth
    source_id = Column(String(100), nullable=False)

    # Raw fields (pre-normalization stored alongside)
    raw_name = Column(String(255), nullable=True)
    raw_pan = Column(String(20), nullable=True)
    raw_mobile = Column(String(20), nullable=True)
    raw_email = Column(String(255), nullable=True)

    # Normalized fields
    pan = Column(String(10), nullable=True, index=True)
    mobile = Column(String(10), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    name = Column(String(255), nullable=True)
    dob = Column(Date, nullable=True)
    city = Column(String(100), nullable=True)
    segment = Column(String(50), nullable=True)

    # Financial
    account_value = Column(Float, nullable=True)
    products = Column(JSONB, nullable=True)  # list of product names
    metadata_extra = Column(JSONB, nullable=True)

    # Vector embedding (384-dim from all-MiniLM-L6-v2)
    vector_embedding = Column(Vector(384), nullable=True)

    # Lineage
    golden_record_id = Column(Integer, nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
