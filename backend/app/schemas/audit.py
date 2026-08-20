"""
Pydantic schemas for Audit Logs.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    """API response for audit log entry."""
    id: int
    actor_id: Optional[str] = None
    actor_username: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}
