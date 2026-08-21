"""
VerificationResult ORM Model.
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Float, Text, func
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, index=True)
    verification_case_id = Column(Integer, ForeignKey("verification_cases.id"), nullable=False, unique=True)
    
    language_detected = Column(String(50), nullable=True)
    call_summary = Column(Text, nullable=True)
    customer_response = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    outcome = Column(String(100), nullable=True)
    recommended_action = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<VerificationResult for case {self.verification_case_id} outcome={self.outcome}>"
