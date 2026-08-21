"""
VerificationCase ORM Model.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, Enum, ForeignKey, Boolean, func
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class VerificationMethod(str, enum.Enum):
    KOVI_AI_CALL = "KOVI_AI_CALL"
    HUMAN_CALL = "HUMAN_CALL"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class VerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    AI_ELIGIBLE = "AI_ELIGIBLE"
    CALL_QUEUED = "CALL_QUEUED"
    CALL_COMPLETED = "CALL_COMPLETED"
    VERIFIED = "VERIFIED"
    ESCALATED = "ESCALATED"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class VerificationCase(Base):
    __tablename__ = "verification_cases"

    id = Column(Integer, primary_key=True, index=True)
    verification_id = Column(String(50), unique=True, index=True)
    match_case_id = Column(Integer, ForeignKey("match_cases.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("golden_customers.id"), nullable=True)
    
    discrepancy_type = Column(String(255), nullable=True)
    risk_level = Column(String(50), nullable=True)
    verification_method = Column(Enum(VerificationMethod), nullable=True)
    ai_eligible = Column(Boolean, default=False)
    
    status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    assigned_to = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<VerificationCase {self.verification_id} status={self.status}>"
