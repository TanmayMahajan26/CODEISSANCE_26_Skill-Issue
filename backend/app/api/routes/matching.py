"""
Nexus360 — Matching Endpoints.

POST /api/v1/matching/run               Trigger full matching pipeline (ADMIN only)
POST /api/v1/matching/run-incremental   Trigger incremental matching pipeline (ADMIN only)
GET  /api/v1/matching/stats             Get matching statistics & Data Quality Scorecard (ADMIN, REVIEWER, ANALYST)
GET  /api/v1/matching/decisions         List match decisions (ADMIN, REVIEWER, ANALYST)
GET  /api/v1/matching/decisions/{id}    Get a specific match decision (ADMIN, REVIEWER, ANALYST)
"""

from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, require_roles
from app.core.database import get_db
from app.models.audit_log import AuditAction
from app.models.golden_customer import GoldenCustomer
from app.models.match_decision import Decision, MatchDecision
from app.models.review_case import ReviewCase, ReviewStatus, VerificationClassification
from app.models.source_record import SourceRecord, SourceSystem
from app.models.user import User, UserRole
from app.schemas.matching import MatchDecisionResponse, MatchRunResponse, MatchingStatsResponse
from app.services.audit_service import log_action
from app.services.matching_service import run_matching_pipeline

router = APIRouter(tags=["Matching"])


@router.post(
    "/matching/run",
    response_model=MatchRunResponse,
    summary="Run the identity resolution matching pipeline",
)
async def run_matching(
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the full matching pipeline (ADMIN only):
    blocking → deterministic → fuzzy → scoring → decision → golden customer.
    """
    client_ip = get_client_ip(request)
    try:
        stats = await run_matching_pipeline(db)
        await log_action(
            db,
            action=AuditAction.MATCHING_RUN,
            actor_username=current_user.username,
            actor_role=current_user.role.value,
            entity_type="MatchingPipeline",
            entity_id="FULL_RUN",
            new_value=stats,
            ip_address=client_ip,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Matching failed: {exc}")

    return MatchRunResponse(
        message="Matching pipeline completed successfully",
        **stats,
    )


@router.post(
    "/matching/run-incremental",
    response_model=MatchRunResponse,
    summary="Run incremental identity resolution matching pipeline",
)
async def run_incremental_matching(
    request: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Execute incremental matching pipeline for newly added source records (ADMIN only)."""
    client_ip = get_client_ip(request)
    try:
        stats = await run_matching_pipeline(db)
        await log_action(
            db,
            action=AuditAction.MATCHING_RUN,
            actor_username=current_user.username,
            actor_role=current_user.role.value,
            entity_type="MatchingPipeline",
            entity_id="INCREMENTAL_RUN",
            new_value=stats,
            ip_address=client_ip,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Incremental matching failed: {exc}")

    return MatchRunResponse(
        message="Incremental matching completed successfully",
        **stats,
    )


@router.get(
    "/matching/stats",
    response_model=MatchingStatsResponse,
    summary="Get Data Quality Scorecard & matching statistics",
)
async def get_matching_stats(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    """Returns Data Quality Scorecard and match stats per PRD §7.3 / §9.2 Screen 2."""
    res_src = await db.execute(select(func.count(SourceRecord.id)))
    total_src = res_src.scalar() or 0

    res_gold = await db.execute(select(func.count(GoldenCustomer.id)))
    total_gold = res_gold.scalar() or 0

    res_eval = await db.execute(select(func.count(MatchDecision.id)))
    total_eval = res_eval.scalar() or 0

    res_match = await db.execute(
        select(func.count(MatchDecision.id)).where(MatchDecision.decision == Decision.MATCH)
    )
    total_matches = res_match.scalar() or 0

    res_rev = await db.execute(
        select(func.count(ReviewCase.id)).where(ReviewCase.status == ReviewStatus.PENDING)
    )
    total_rev = res_rev.scalar() or 0

    res_non = await db.execute(
        select(func.count(MatchDecision.id)).where(MatchDecision.decision == Decision.NON_MATCH)
    )
    total_non = res_non.scalar() or 0

    match_rate = round((total_matches / total_eval * 100), 2) if total_eval > 0 else 0.0

    # Per source-system stats
    by_sys: Dict[str, Dict[str, Any]] = {}
    for sys_enum in SourceSystem:
        sys_res = await db.execute(
            select(func.count(SourceRecord.id)).where(SourceRecord.source_system == sys_enum)
        )
        count = sys_res.scalar() or 0
        
        pan_res = await db.execute(
            select(func.count(SourceRecord.id))
            .where(SourceRecord.source_system == sys_enum)
            .where(SourceRecord.normalized_pan != None)
        )
        missing_pan = pan_res.scalar() or 0
        pan_completeness = round(((count - missing_pan) / count * 100), 1) if count > 0 else 100.0

        by_sys[sys_enum.value] = {
            "total_records": count,
            "missing_pan_count": missing_pan,
            "pan_completeness_pct": pan_completeness,
        }

    res_ai_eligible = await db.execute(
        select(func.count(ReviewCase.id)).where(ReviewCase.verification_classification == VerificationClassification.AI_VERIFICATION_ELIGIBLE)
    )
    total_ai_eligible = res_ai_eligible.scalar() or 0

    res_human_req = await db.execute(
        select(func.count(ReviewCase.id)).where(ReviewCase.verification_classification == VerificationClassification.HUMAN_VERIFICATION_REQUIRED)
    )
    total_human_req = res_human_req.scalar() or 0

    return MatchingStatsResponse(
        total_source_records=total_src,
        total_golden_records=total_gold,
        match_rate_pct=match_rate,
        total_pairs_evaluated=total_eval,
        total_matches=total_matches,
        total_reviews_pending=total_rev,
        total_non_matches=total_non,
        ai_eligible=total_ai_eligible,
        human_required=total_human_req,
        by_source_system=by_sys,
    )


@router.get(
    "/matching/decisions",
    response_model=List[MatchDecisionResponse],
    summary="List all match decisions",
)
async def list_decisions(
    decision: Optional[str] = Query(None, description="Filter: MATCH | REVIEW | NON_MATCH"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve match decisions with optional filtering by decision type."""
    query = select(MatchDecision).offset(skip).limit(limit)

    if decision:
        try:
            dec_enum = Decision(decision.upper())
            query = query.where(MatchDecision.decision == dec_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid decision filter. Must be one of: {[d.value for d in Decision]}",
            )

    query = query.order_by(MatchDecision.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/matching/decisions/{decision_id}",
    response_model=MatchDecisionResponse,
    summary="Get a specific match decision",
)
async def get_decision(
    decision_id: int,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER, UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single match decision by its ID."""
    decision = await db.get(MatchDecision, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Match decision not found")
    return decision
