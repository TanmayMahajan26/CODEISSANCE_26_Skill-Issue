"""
Opportunity ORM Model.

Stores generated cross-sell/upsell/retention recommendations for golden customers.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Numeric, DateTime, Enum, ForeignKey, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class OpportunityType(str, enum.Enum):
    CROSS_SELL = "CROSS_SELL"
    UPSELL = "UPSELL"
    RETENTION = "RETENTION"
    PROTECTION = "PROTECTION"


class OpportunityStatus(str, enum.Enum):
    NEW = "NEW"
    VIEWED = "VIEWED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    CONVERTED = "CONVERTED"
    DISMISSED = "DISMISSED"


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    golden_customer_id = Column(
        String(20), ForeignKey("golden_customers.golden_customer_id"),
        nullable=False, index=True
    )
    opportunity_type = Column(Enum(OpportunityType), nullable=False)
    product_recommended = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)
    score_breakdown = Column(JSONB)
    ai_reasoning = Column(String)
    potential_value = Column(Numeric(15, 2))
    eligibility_met = Column(JSONB)
    status = Column(Enum(OpportunityStatus), default=OpportunityStatus.NEW, nullable=False, index=True)
    assigned_rm_id = Column(String(100))

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    golden_customer = relationship("GoldenCustomer", back_populates="opportunities")

    def __repr__(self) -> str:
        return (
            f"<Opportunity id={self.id} customer={self.golden_customer_id} "
            f"product='{self.product_recommended}' score={self.score}>"
        )
