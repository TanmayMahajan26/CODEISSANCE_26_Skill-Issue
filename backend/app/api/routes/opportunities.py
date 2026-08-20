"""
Nexus360 — Next-Best-Opportunity Endpoints.

GET   /api/v1/opportunities             List cross-sell/upsell opportunities (ADMIN, RM, ANALYST)
GET   /api/v1/opportunities/dashboard   Aggregated opportunity dashboard metrics (ADMIN, RM, ANALYST)
GET   /api/v1/opportunities/{id}        Opportunity detail with AI reasoning (ADMIN, RM, ANALYST)
PATCH /api/v1/opportunities/{id}/status Update status of an opportunity (ADMIN, RM)
POST  /api/v1/opportunities/generate    Re-generate all opportunities across golden records (ADMIN only)
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.opportunity import Opportunity
from app.models.user import User, UserRole
from app.schemas.opportunity import (
    OpportunityResponse,
    OpportunityStatusUpdateRequest,
    OpportunityDashboardResponse,
)
from app.services import opportunity_service

router = APIRouter(prefix="/opportunities", tags=["Next-Best-Opportunity Engine"])


@router.get(
    "",
    response_model=List[OpportunityResponse],
    summary="List opportunities",
)
async def list_opportunities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None, description="Filter: NEW | VIEWED | ASSIGNED | IN_PROGRESS | CONVERTED | DISMISSED"),
    rm_id: Optional[str] = Query(None, description="Filter by assigned Relationship Manager ID"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RELATIONSHIP_MANAGER, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve cross-sell and upsell opportunities."""
    return await opportunity_service.list_opportunities(
        db, skip=skip, limit=limit, status=status, rm_id=rm_id
    )


@router.get(
    "/dashboard",
    response_model=OpportunityDashboardResponse,
    summary="Get aggregated opportunity dashboard",
)
async def get_opportunity_dashboard(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RELATIONSHIP_MANAGER, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve aggregated opportunity metrics, status funnels, and potential relationship values."""
    return await opportunity_service.get_opportunity_dashboard(db)


@router.get(
    "/{opportunity_id}",
    response_model=OpportunityResponse,
    summary="Get single opportunity detail",
)
async def get_opportunity(
    opportunity_id: int = Path(..., description="ID of the opportunity"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RELATIONSHIP_MANAGER, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details and AI reasoning for a single opportunity."""
    opp = await db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")
    return opp


@router.patch(
    "/{opportunity_id}/status",
    response_model=OpportunityResponse,
    summary="Update opportunity status",
)
async def update_opportunity_status(
    payload: OpportunityStatusUpdateRequest,
    opportunity_id: int = Path(..., description="ID of the opportunity"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RELATIONSHIP_MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    """Update opportunity status and record actor identity in audit trail (ADMIN & RM only)."""
    try:
        updated = await opportunity_service.update_opportunity_status(
            db,
            opportunity_id=opportunity_id,
            new_status=payload.status,
            assigned_rm_id=payload.assigned_rm_id,
            actor=current_user.username,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return updated


@router.post(
    "/generate",
    summary="Re-generate all opportunities",
)
async def generate_opportunities(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Trigger Next-Best-Opportunity product gap analysis across all golden records (ADMIN only)."""
    total = await opportunity_service.generate_all_opportunities(db)
    return {
        "message": "Opportunities generated successfully",
        "total_opportunities_created": total,
    }
