"""
Pydantic schemas for Source Records.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional, List

from pydantic import BaseModel, Field


class SourceRecordBase(BaseModel):
    """Fields shared by creation and response schemas."""
    source_system: str
    source_record_id: str
    original_name: Optional[str] = None
    original_dob: Optional[date] = None
    original_mobile: Optional[str] = None
    original_email: Optional[str] = None
    original_pan: Optional[str] = None
    original_city: Optional[str] = None
    segment: Optional[str] = None
    product_type: Optional[str] = None
    balance_aum: Optional[Decimal] = None
    relationship_value: Optional[Decimal] = None
    last_activity_date: Optional[date] = None
    rm_id: Optional[str] = None


class SourceRecordCreate(SourceRecordBase):
    """Used when creating a source record via ingestion."""
    raw_data: Optional[Dict[str, Any]] = None


class SourceRecordResponse(SourceRecordBase):
    """Returned from the API."""
    id: int
    normalized_name: Optional[str] = None
    normalized_dob: Optional[date] = None
    normalized_mobile: Optional[str] = None
    normalized_email: Optional[str] = None
    normalized_pan: Optional[str] = None
    normalized_city: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    ingested_at: datetime

    model_config = {"from_attributes": True}


class IngestionResponse(BaseModel):
    """Response returned after a CSV ingestion."""
    message: str
    records_ingested: int
    source_system: str
    errors: List[str] = Field(default_factory=list)
