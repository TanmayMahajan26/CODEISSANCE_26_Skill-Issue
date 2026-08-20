"""
Pydantic schemas for BRE Configuration Rules and Impact Preview.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ConfigRuleResponse(BaseModel):
    """API response for a config rule."""
    id: int
    category: str
    rule_key: str
    rule_value: Dict[str, Any]
    description: Optional[str] = None
    is_active: bool
    version: int
    updated_by: Optional[str] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConfigRuleUpdateRequest(BaseModel):
    """Payload for updating a config rule."""
    rule_value: Dict[str, Any]
    updated_by: str = "Admin"


class ImpactPreviewRequest(BaseModel):
    """Payload for previewing impact of rule changes."""
    rule_key: str
    new_value: Dict[str, Any]


class ImpactPreviewResponse(BaseModel):
    """API response for What-If impact preview."""
    rule_key: str
    current_auto_merges: Optional[int] = None
    projected_auto_merges: Optional[int] = None
    net_auto_merge_change: Optional[int] = None
    current_pending_reviews: Optional[int] = None
    projected_pending_reviews: Optional[int] = None
    net_review_change: Optional[int] = None
    total_decisions_evaluated: int
