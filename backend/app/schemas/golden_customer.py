from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from decimal import Decimal
from app.models.golden_customer import GoldenCustomerStatus

class GoldenCustomerBase(BaseModel):
    golden_id: str
    full_name: Optional[str] = None
    normalized_name: Optional[str] = None
    pan_masked: Optional[str] = None
    mobile_masked: Optional[str] = None
    email: Optional[str] = None
    dob: Optional[date] = None
    city: Optional[str] = None
    relationship_value: Optional[Decimal] = None
    relationship_manager: Optional[str] = None
    status: GoldenCustomerStatus
    source_record_ids: List[str] = []

class GoldenCustomerResponse(GoldenCustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GoldenCustomerDetail(GoldenCustomerResponse):
    source_records: List[Any] = []
    opportunities: List[Any] = []
    match_cases: List[Any] = []
