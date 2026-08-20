"""
Pydantic schemas for Golden Customer.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class GoldenCustomerResponse(BaseModel):
    """API response for a golden customer record."""
    id: int
    golden_customer_id: str
    canonical_name: Optional[str] = None
    canonical_dob: Optional[date] = None
    canonical_mobile: Optional[str] = None
    canonical_email: Optional[str] = None
    canonical_pan: Optional[str] = None
    canonical_city: Optional[str] = None
    canonical_segment: Optional[str] = None
    total_relationship_value: Optional[Decimal] = Decimal("0.0")
    products_held: List[Dict[str, Any]] = []
    source_record_ids: List[int] = []
    attribute_provenance: Dict[str, Any] = {}
    match_confidence: float = 1.0
    version: int = 1
    status: str = "ACTIVE"
    merged_into_id: Optional[str] = None
    assigned_rm_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GoldenCustomerDetail(GoldenCustomerResponse):
    """Extended response including linked source records."""
    linked_sources: List[Dict[str, Any]] = []


class AttributeHistoryResponse(BaseModel):
    """API response for an attribute change record."""
    id: int
    golden_customer_id: str
    attribute_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    selected_source: Optional[str] = None
    change_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
