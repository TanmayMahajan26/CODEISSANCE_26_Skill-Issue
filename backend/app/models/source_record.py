"""
SourceRecord ORM Model.

Stores original incoming records from all 5 business systems.
Preserves both the original and normalized field values.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Enum, Numeric, Text, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class SourceSystem(str, enum.Enum):
    """Allowed source business systems."""
    EQUITY = "EQUITY"
    MUTUAL_FUND = "MUTUAL_FUND"
    INSURANCE = "INSURANCE"
    LOAN = "LOAN"
    WEALTH = "WEALTH"


class SourceRecord(Base):
    __tablename__ = "source_records"

    id = Column(Integer, primary_key=True, index=True)
    source_system = Column(Enum(SourceSystem), nullable=False, index=True)
    source_record_id = Column(String(100), nullable=False, index=True)

    # ── Original values (never overwritten) ──────────────────────
    original_name = Column(String(255))
    original_dob = Column(Date)
    original_mobile = Column(String(20))
    original_email = Column(String(255))
    original_pan = Column(String(20))
    original_city = Column(String(100))

    # ── Normalized values (computed on ingest) ───────────────────
    normalized_name = Column(String(255), index=True)
    normalized_dob = Column(Date, index=True)
    normalized_mobile = Column(String(15), index=True)
    normalized_email = Column(String(255), index=True)
    normalized_pan = Column(String(10), index=True)
    normalized_city = Column(String(100))

    # ── Business & Financial attributes ──────────────────────────
    segment = Column(String(50))
    product_type = Column(String(100))
    balance_aum = Column(Numeric(15, 2))
    relationship_value = Column(Numeric(15, 2))
    last_activity_date = Column(Date)
    rm_id = Column(String(100))
    name_embedding = Column(JSONB)

    # ── Raw payload ──────────────────────────────────────────────
    raw_data = Column(JSONB)

    ingested_at = Column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    identity_links = relationship("IdentityLink", back_populates="source_record")

    def __repr__(self) -> str:
        return (
            f"<SourceRecord id={self.id} system={self.source_system} "
            f"name='{self.original_name}'>"
        )
