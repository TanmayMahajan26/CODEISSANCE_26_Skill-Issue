"""
Nexus360 — Audit Service.

Logs sensitive actions (config changes, merge approvals, rejections, manual merges,
unmerges, ingestion, matching runs) to the audit_logs table.
Aligned with PRD §7.7 / §8.4.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog, AuditAction

logger = logging.getLogger(__name__)


async def log_action(
    db: AsyncSession,
    action: AuditAction,
    actor_username: str = "System",
    actor_role: str = "Admin",
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    old_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = "127.0.0.1",
) -> AuditLog:
    """Log an event to the audit_logs table."""
    audit_entry = AuditLog(
        actor_id=actor_username.lower(),
        actor_username=actor_username,
        actor_role=actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
    )
    db.add(audit_entry)
    await db.flush()
    logger.info(
        "AuditLog: [%s] %s by %s on %s:%s",
        action.value, action, actor_username, entity_type, entity_id
    )
    return audit_entry


async def get_audit_logs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    action: Optional[str] = None,
) -> List[AuditLog]:
    """Retrieve audit logs filtered by action or pagination."""
    query = select(AuditLog).offset(skip).limit(limit).order_by(AuditLog.timestamp.desc())
    if action:
        try:
            action_enum = AuditAction(action.upper())
            query = query.where(AuditLog.action == action_enum)
        except ValueError:
            pass

    res = await db.execute(query)
    return res.scalars().all()
