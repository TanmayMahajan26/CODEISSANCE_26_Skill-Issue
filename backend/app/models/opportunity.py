"""
Opportunity ORM Model.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Enum, ForeignKey, Numeric, func, Text
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class OpportunityType(str, enum.Enum):
    CROSS_SELL = "CROSS_SELL"
    UPSELL = "UPSELL"
    PROTECTION = "PROTECTION"
    RETENTION = "RETENTION"


class OpportunityStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED_WON = "CLOSED_WON"
    CLOSED_LOST = "CLOSED_LOST"


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("golden_customers.id"), nullable=False, index=True)
    
    opportunity_type = Column(Enum(OpportunityType), nullable=False)
    opportunity_name = Column(String(255), nullable=False)
    estimated_value = Column(Numeric(15, 2), nullable=True)
    readiness_score = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)
    
    status = Column(Enum(OpportunityStatus), default=OpportunityStatus.OPEN)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Opportunity {self.id} for customer {self.customer_id}>"
