from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.match_case import MatchClassification, MatchStatus, RiskLevel
from .source_record import SourceRecordResponse

class MatchCaseBase(BaseModel):
    case_id: str
    record_a_id: int
    record_b_id: int
    match_score: float
    classification: MatchClassification
    risk_level: Optional[RiskLevel] = None
    primary_discrepancy: Optional[str] = None
    pan_match: bool = False
    name_score: float = 0.0
    mobile_match: bool = False
    email_score: float = 0.0
    dob_match: bool = False
    city_match: bool = False
    recommended_action: Optional[str] = None
    status: MatchStatus

class MatchCaseResponse(MatchCaseBase):
    id: int
    created_at: datetime
    record_a: Optional[SourceRecordResponse] = None
    record_b: Optional[SourceRecordResponse] = None

    class Config:
        from_attributes = True
