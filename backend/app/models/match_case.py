"""
MatchCase ORM Model.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Enum, ForeignKey, func, Boolean
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class MatchClassification(str, enum.Enum):
    AUTO_MATCH = "AUTO_MATCH"
    REVIEW = "REVIEW"
    NO_MATCH = "NO_MATCH"


class MatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MatchCase(Base):
    __tablename__ = "match_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), unique=True, index=True)
    record_a_id = Column(Integer, ForeignKey("source_records.id"), nullable=False)
    record_b_id = Column(Integer, ForeignKey("source_records.id"), nullable=False)
    
    match_score = Column(Float, nullable=False)
    classification = Column(Enum(MatchClassification), nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=True)
    primary_discrepancy = Column(String(255), nullable=True)
    
    pan_match = Column(Boolean, default=False)
    name_score = Column(Float, default=0.0)
    mobile_match = Column(Boolean, default=False)
    email_score = Column(Float, default=0.0)
    dob_match = Column(Boolean, default=False)
    city_match = Column(Boolean, default=False)
    
    recommended_action = Column(String(100), nullable=True)
    status = Column(Enum(MatchStatus), default=MatchStatus.PENDING)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<MatchCase {self.case_id} classification={self.classification}>"
