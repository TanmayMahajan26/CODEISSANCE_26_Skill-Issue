"""
Pydantic schemas for Opportunities.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional, List

from pydantic import BaseModel


class OpportunityResponse(BaseModel):
    """API response for an opportunity recommendation."""
    id: int
    golden_customer_id: str
    opportunity_type: str
    product_recommended: str
    score: float
    score_breakdown: Optional[Dict[str, Any]] = None
    ai_reasoning: Optional[str] = None
    potential_value: Optional[Decimal] = Decimal("0.0")
    eligibility_met: Optional[Dict[str, Any]] = None
    status: str
    assigned_rm_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OpportunityStatusUpdateRequest(BaseModel):
    """Payload for updating opportunity status."""
    status: str  # NEW | VIEWED | ASSIGNED | IN_PROGRESS | CONVERTED | DISMISSED
    assigned_rm_id: Optional[str] = None


class OpportunityDashboardResponse(BaseModel):
    """Aggregated dashboard metrics for opportunities."""
    total_opportunities: int
    total_potential_value: Decimal
    by_type: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    by_product: Dict[str, int] = {}
