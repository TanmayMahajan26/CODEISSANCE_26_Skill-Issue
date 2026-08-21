from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.verification_case import VerificationMethod, VerificationStatus

class VerificationCaseBase(BaseModel):
    verification_id: str
    match_case_id: Optional[int] = None
    customer_id: Optional[int] = None
    discrepancy_type: Optional[str] = None
    risk_level: Optional[str] = None
    verification_method: Optional[VerificationMethod] = None
    ai_eligible: bool = False
    status: VerificationStatus
    assigned_to: Optional[str] = None

class VerificationCaseResponse(VerificationCaseBase):
    id: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class VerificationResultBase(BaseModel):
    verification_case_id: int
    language_detected: Optional[str] = None
    call_summary: Optional[str] = None
    customer_response: Optional[str] = None
    confidence: Optional[float] = None
    outcome: Optional[str] = None
    recommended_action: Optional[str] = None

class VerificationResultResponse(VerificationResultBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
