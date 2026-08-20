"""
IdentityLink ORM Model.

Links a source_record to a golden_customer, recording the match
confidence, method, status, and AI explanations.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Enum, ForeignKey, func
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class MatchMethod(str, enum.Enum):
    DETERMINISTIC = "DETERMINISTIC"
    FUZZY = "FUZZY"
    SEMANTIC = "SEMANTIC"
    ML = "ML"
    MANUAL = "MANUAL"


class LinkStatus(str, enum.Enum):
    MATCH = "MATCH"
    REVIEW = "REVIEW"
    NON_MATCH = "NON_MATCH"


class IdentityLink(Base):
    __tablename__ = "identity_links"

    id = Column(Integer, primary_key=True, index=True)
    source_record_id = Column(
        Integer, ForeignKey("source_records.id"), nullable=False, index=True
    )
    golden_customer_id = Column(
        String(20), ForeignKey("golden_customers.golden_customer_id"),
        nullable=False, index=True
    )

    match_confidence = Column(Float)
    match_method = Column(Enum(MatchMethod))
    status = Column(Enum(LinkStatus), nullable=False)
    ai_explanation = Column(String, nullable=True)

    linked_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    source_record = relationship("SourceRecord", back_populates="identity_links")
    golden_customer = relationship("GoldenCustomer", back_populates="identity_links")

    def __repr__(self) -> str:
        return (
            f"<IdentityLink src={self.source_record_id} → "
            f"{self.golden_customer_id} status={self.status}>"
        )
