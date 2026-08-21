from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, RoleChecker
from app.db.models.audit import AuditLog
from app.db.models.user import User

router = APIRouter()

admin_manager = RoleChecker(["ADMIN", "MANAGER"])


@router.get("/logs")
def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    action_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    actor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_manager),
):
    """List audit logs with optional filtering. Admin/Manager only."""
    query = db.query(AuditLog)

    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)

    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

    return {"total": total, "logs": logs}


@router.get("/logs/export")
def export_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["ADMIN"])),
):
    """Export audit logs as JSON (CSV export can be added later). Admin only."""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1000).all()

    export_data = []
    for log in logs:
        export_data.append({
            "id": log.id,
            "actor_id": log.actor_id,
            "actor_role": log.actor_role,
            "action_type": log.action_type,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "description": log.description,
            "timestamp": str(log.timestamp) if log.timestamp else None,
        })

    return {"total": len(export_data), "logs": export_data}
