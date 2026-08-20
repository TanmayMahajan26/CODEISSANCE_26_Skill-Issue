"""
GoldenCustomer ORM Model.

The unified, de-duplicated customer record produced by the identity
resolution engine. golden_customer_id follows the pattern GOLD-NNNNNN.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Float, Numeric, Enum, Sequence, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class GoldenCustomerStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    MERGED_INTO = "MERGED_INTO"


# Sequence for generating the numeric portion of GOLD-NNNNNN
golden_seq = Sequence("golden_customer_seq", start=1, increment=1)


class GoldenCustomer(Base):
    __tablename__ = "golden_customers"

    id = Column(Integer, primary_key=True, index=True)
    golden_customer_id = Column(
        String(20), unique=True, nullable=False, index=True
    )

    # ── Canonical (best-known) attributes ────────────────────────
    canonical_name = Column(String(255))
    canonical_dob = Column(Date)
    canonical_mobile = Column(String(15))
    canonical_email = Column(String(255))
    canonical_pan = Column(String(10))
    canonical_city = Column(String(100))
    canonical_segment = Column(String(50))

    # ── Consolidated Financials & Provenance ──────────────────────
    total_relationship_value = Column(Numeric(15, 2), default=0.0)
    products_held = Column(JSONB, default=list)
    source_record_ids = Column(JSONB, default=list)
    attribute_provenance = Column(JSONB, default=dict)
    match_confidence = Column(Float, default=1.0)
    version = Column(Integer, default=1, nullable=False)
    status = Column(Enum(GoldenCustomerStatus), default=GoldenCustomerStatus.ACTIVE, nullable=False, index=True)
    merged_into_id = Column(String(20), nullable=True)
    assigned_rm_id = Column(String(100), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    identity_links = relationship("IdentityLink", back_populates="golden_customer")
    attribute_history = relationship("AttributeHistory", back_populates="golden_customer")
    opportunities = relationship("Opportunity", back_populates="golden_customer")

    def __repr__(self) -> str:
        return (
            f"<GoldenCustomer {self.golden_customer_id} "
            f"name='{self.canonical_name}'>"
        )
