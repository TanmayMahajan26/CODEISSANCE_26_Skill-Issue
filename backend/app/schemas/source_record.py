from datetime import date, datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from decimal import Decimal
from app.models.source_record import SourceSystem

class SourceRecordBase(BaseModel):
    source_system: SourceSystem
    source_record_id: str
    customer_reference: Optional[str] = None
    full_name: Optional[str] = None
    pan: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    dob: Optional[date] = None
    city: Optional[str] = None
    product_type: Optional[str] = None
    holding_value: Optional[Decimal] = None

class SourceRecordResponse(SourceRecordBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
