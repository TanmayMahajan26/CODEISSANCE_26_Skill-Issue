"""
Nexus360 — Config & BRE Endpoints.

GET  /api/v1/config/rules                 List all active rules (ADMIN, REVIEWER, ANALYST)
GET  /api/v1/config/rules/{rule_key}      Get single rule by key (ADMIN, REVIEWER, ANALYST)
PUT  /api/v1/config/rules/{rule_key}      Update a rule (ADMIN only)
POST /api/v1/config/rules/impact-preview   What-If simulator impact preview (ADMIN, REVIEWER, ANALYST)
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import subprocess
import os

from app.api.deps import get_client_ip, require_roles
from app.core.database import get_db
from app.models.audit_log import AuditAction
from app.models.user import User, UserRole
from app.schemas.config import (
    ConfigRuleResponse,
    ConfigRuleUpdateRequest,
    ImpactPreviewRequest,
    ImpactPreviewResponse,
)
from app.services import audit_service, config_service

router = APIRouter(prefix="/config", tags=["Configuration & BRE"])


@router.get(
    "/rules",
    response_model=List[ConfigRuleResponse],
    summary="List all configuration rules",
)
async def list_rules(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all active BRE configuration rules."""
    return await config_service.get_all_rules(db)


@router.get(
    "/rules/{rule_key}",
    response_model=ConfigRuleResponse,
    summary="Get rule by key",
)
async def get_rule(
    rule_key: str = Path(..., description="Unique key of the rule"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single BRE configuration rule."""
    rule = await config_service.get_rule_by_key(db, rule_key)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_key}' not found")
    return rule


@router.put(
    "/rules/{rule_key}",
    response_model=ConfigRuleResponse,
    summary="Update a configuration rule",
)
async def update_rule(
    payload: ConfigRuleUpdateRequest,
    request: Request,
    rule_key: str = Path(..., description="Unique key of the rule"),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Update a BRE configuration rule and log the change to audit trail (ADMIN only)."""
    old_rule = await config_service.get_rule_by_key(db, rule_key)
    if not old_rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_key}' not found")

    old_val = old_rule.rule_value
    updater = current_user.username
    client_ip = get_client_ip(request)

    updated = await config_service.update_rule(
        db, rule_key=rule_key, new_value=payload.rule_value, updated_by=updater
    )

    await audit_service.log_action(
        db,
        action=AuditAction.CONFIG_CHANGE,
        actor_username=updater,
        actor_role=current_user.role.value,
        entity_type="ConfigRule",
        entity_id=rule_key,
        old_value=old_val,
        new_value=payload.rule_value,
        ip_address=client_ip,
    )

    return updated


@router.post(
    "/rules/impact-preview",
    response_model=ImpactPreviewResponse,
    summary="What-If Impact Simulator",
)
async def impact_preview(
    payload: ImpactPreviewRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    """Preview the impact of changing a matching threshold or rule value before applying."""
    return await config_service.preview_impact(db, payload.rule_key, payload.new_value)

@router.post(
    "/reset-demo",
    summary="Reset Demo Data (Hackathon)",
)
async def reset_demo_data():
    """Wipe database and re-seed demo data."""
    try:
        script_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts", "seed_demo_data.py")
        subprocess.run(["python", script_path], check=True)
        return {"message": "Demo data reset successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

