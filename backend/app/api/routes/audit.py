"""
Nexus360 — Audit Log Endpoints.

GET /api/v1/audit/logs   List filtered audit trail entries (ADMIN only)
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.audit import AuditLogResponse
from app.services import audit_service

router = APIRouter(prefix="/audit", tags=["Audit Log"])


@router.get(
    "/logs",
    response_model=List[AuditLogResponse],
    summary="List audit trail logs",
)
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    action: Optional[str] = Query(None, description="Filter by action name (e.g. CONFIG_CHANGE, MERGE_APPROVE, LOGIN)"),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve system audit logs (ADMIN only)."""
    return await audit_service.get_audit_logs(db, skip=skip, limit=limit, action=action)
