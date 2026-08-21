"""
GoldenCustomer ORM Model.

The unified, de-duplicated customer record produced by the identity
resolution engine.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Numeric, Enum, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class GoldenCustomerStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    MERGED_INTO = "MERGED_INTO"


class GoldenCustomer(Base):
    __tablename__ = "golden_customers"

    id = Column(Integer, primary_key=True, index=True)
    golden_id = Column(
        String(20), unique=True, nullable=False, index=True
    )
    
    full_name = Column(String(255))
    normalized_name = Column(String(255))
    pan_masked = Column(String(20))
    mobile_masked = Column(String(20))
    email = Column(String(255))
    dob = Column(Date)
    city = Column(String(100))
    
    relationship_value = Column(Numeric(15, 2), default=0.0)
    relationship_manager = Column(String(100), nullable=True)
    
    source_record_ids = Column(JSONB, default=list)
    status = Column(Enum(GoldenCustomerStatus), default=GoldenCustomerStatus.ACTIVE, nullable=False, index=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<GoldenCustomer {self.golden_id} "
            f"name='{self.full_name}'>"
        )
