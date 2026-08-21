"""
SourceRecord ORM Model.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Enum, Numeric, func
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class SourceSystem(str, enum.Enum):
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
    customer_reference = Column(String(100), nullable=True)
    
    full_name = Column(String(255))
    pan = Column(String(20))
    mobile = Column(String(20))
    email = Column(String(255))
    dob = Column(Date)
    city = Column(String(100))
    
    product_type = Column(String(100))
    holding_value = Column(Numeric(15, 2))
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<SourceRecord id={self.id} system={self.source_system}>"
