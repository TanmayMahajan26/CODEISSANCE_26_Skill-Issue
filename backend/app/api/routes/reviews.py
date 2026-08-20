"""
Nexus360 — Review Endpoints.

GET  /api/v1/reviews                             List review cases (ADMIN, REVIEWER)
GET  /api/v1/reviews/{id}                        Get review case detail (ADMIN, REVIEWER)
POST /api/v1/reviews/{id}/approve                Approve a review (ADMIN, REVIEWER)
POST /api/v1/reviews/{id}/reject                 Reject a review (ADMIN, REVIEWER)
POST /api/v1/reviews/{id}/manual-merge           Manual merge with custom attribute picks (ADMIN, REVIEWER)
POST /api/v1/reviews/unmerge/{golden_customer_id} Split/unmerge a golden customer (ADMIN only)
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.review_case import ReviewCase, ReviewStatus, ReviewType
from app.models.match_decision import MatchDecision
from app.models.source_record import SourceRecord
from app.models.golden_customer import GoldenCustomer
from app.models.identity_link import IdentityLink, LinkStatus
from app.models.user import User, UserRole
from app.schemas.review import (
    ReviewActionRequest,
    ReviewCaseResponse,
    ReviewCaseDetailResponse,
    ManualMergeRequest,
    SourceRecordSummary,
    MatchDecisionSummary,
    FieldComparisonItem,
    GoldenCustomerSummary,
)
from app.services.review_service import (
    approve_review,
    reject_review,
    manual_merge_review,
    unmerge_golden_customer,
    ReviewConflictError,
)
from app.services.explanation_service import generate_explanation

router = APIRouter(tags=["Reviews"])


@router.get(
    "/reviews",
    response_model=List[ReviewCaseResponse],
    summary="List review cases",
)
async def list_reviews(
    status: Optional[str] = Query(None, description="Filter: PENDING | APPROVED | REJECTED"),
    review_type: Optional[str] = Query(None, description="Filter: LOW_CONFIDENCE_MATCH | ATTRIBUTE_CONFLICT | DUPLICATE_SUSPECT | AI_FLAGGED"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve review cases with optional status and review_type filtering (ADMIN & REVIEWER only)."""
    query = select(ReviewCase).offset(skip).limit(limit)

    if status:
        try:
            status_enum = ReviewStatus(status.upper())
            query = query.where(ReviewCase.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {[s.value for s in ReviewStatus]}",
            )

    if review_type:
        try:
            type_enum = ReviewType(review_type.upper())
            query = query.where(ReviewCase.review_type == type_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid review_type. Must be one of: {[t.value for t in ReviewType]}",
            )

    query = query.order_by(ReviewCase.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/reviews/{review_id}",
    response_model=ReviewCaseDetailResponse,
    summary="Get review case detail with full comparison data",
)
async def get_review_detail(
    review_id: int,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER)),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a single review case with enriched data for the reviewer UI:
    both source records, field-by-field comparison, weighted score breakdown,
    human-readable explanation, and golden customer context.
    """
    review = await db.get(ReviewCase, review_id)
    if not review:
        raise HTTPException(status_code=404, detail=f"Review case {review_id} not found")

    # ── Fetch linked MatchDecision ────────────────────────────────
    decision = await db.get(MatchDecision, review.match_decision_id)
    if not decision:
        raise HTTPException(status_code=500, detail="Linked MatchDecision not found")

    # ── Fetch source records ──────────────────────────────────────
    rec_a = await db.get(SourceRecord, decision.record_a_id)
    rec_b = await db.get(SourceRecord, decision.record_b_id)

    record_a_summary = _build_source_summary(rec_a) if rec_a else None
    record_b_summary = _build_source_summary(rec_b) if rec_b else None

    # ── Build MatchDecision summary ───────────────────────────────
    decision_summary = MatchDecisionSummary(
        id=decision.id,
        record_a_id=decision.record_a_id,
        record_b_id=decision.record_b_id,
        pan_match=decision.pan_match,
        mobile_match=decision.mobile_match,
        email_match=decision.email_match,
        name_similarity=decision.name_similarity,
        name_semantic_similarity=decision.name_semantic_similarity,
        dob_match=decision.dob_match,
        city_similarity=decision.city_similarity,
        segment_match=decision.segment_match,
        final_score=decision.final_score,
        decision=decision.decision.value if decision.decision else "REVIEW",
        reasoning=decision.reasoning,
        ai_explanation=decision.ai_explanation,
        created_at=decision.created_at,
    )

    # ── Generate field comparisons and explanation ─────────────────
    features = {
        "pan_exact": decision.pan_match or 0.0,
        "mobile_exact": decision.mobile_match or 0.0,
        "email_exact": decision.email_match or 0.0,
        "name_similarity": decision.name_similarity or 0.0,
        "name_semantic_similarity": decision.name_semantic_similarity or 0.0,
        "dob_exact": decision.dob_match or 0.0,
        "city_similarity": decision.city_similarity or 0.0,
        "segment_exact": decision.segment_match or 0.0,
    }

    reasoning = decision.reasoning or {}
    score_bkdn = reasoning.get("score_breakdown", {})
    contributions = score_bkdn.get("contributions", {})

    explanation = generate_explanation(
        features=features,
        contributions=contributions,
        final_score=decision.final_score,
        decision=decision.decision.value if decision.decision else "REVIEW",
        reasoning=reasoning,
    )

    field_comparisons = [
        FieldComparisonItem(**fc.to_dict()) for fc in explanation.field_comparisons
    ]

    # ── Fetch golden customer context ─────────────────────────────
    golden_a = await _find_golden_for_record(db, decision.record_a_id) if rec_a else None
    golden_b = await _find_golden_for_record(db, decision.record_b_id) if rec_b else None

    return ReviewCaseDetailResponse(
        id=review.id,
        match_decision_id=review.match_decision_id,
        priority=review.priority.value if review.priority else "MEDIUM",
        status=review.status.value if review.status else "PENDING",
        review_type=review.review_type.value if review.review_type else "LOW_CONFIDENCE_MATCH",
        reviewer=review.reviewer,
        assigned_to=review.assigned_to,
        review_notes=review.review_notes,
        ai_suggestion=review.ai_suggestion,
        source_record_ids=review.source_record_ids,
        created_at=review.created_at,
        resolved_at=review.resolved_at,
        record_a=record_a_summary,
        record_b=record_b_summary,
        match_decision=decision_summary,
        field_comparisons=field_comparisons,
        explanation=explanation.to_dict(),
        golden_customer_a=golden_a,
        golden_customer_b=golden_b,
    )


@router.post(
    "/reviews/{review_id}/approve",
    response_model=ReviewCaseResponse,
    summary="Approve a review case (confirms the match)",
)
async def approve(
    review_id: int,
    body: ReviewActionRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER)),
    db: AsyncSession = Depends(get_db),
):
    """Approve a review case — confirms the two records are the same person and links them."""
    reviewer_identity = current_user.username
    try:
        review = await approve_review(db, review_id, reviewer_identity, body.review_notes)
    except ReviewConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return review


@router.post(
    "/reviews/{review_id}/reject",
    response_model=ReviewCaseResponse,
    summary="Reject a review case (confirms non-match)",
)
async def reject(
    review_id: int,
    body: ReviewActionRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER)),
    db: AsyncSession = Depends(get_db),
):
    """Reject a review case — confirms the two records are different people."""
    reviewer_identity = current_user.username
    try:
        review = await reject_review(db, review_id, reviewer_identity, body.review_notes)
    except ReviewConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return review


@router.post(
    "/reviews/{review_id}/manual-merge",
    response_model=ReviewCaseResponse,
    summary="Manual merge with custom attribute field selection",
)
async def manual_merge(
    review_id: int,
    body: ManualMergeRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.REVIEWER)),
    db: AsyncSession = Depends(get_db),
):
    """Approve review with custom selected attribute values."""
    reviewer_identity = current_user.username
    try:
        review = await manual_merge_review(
            db, review_id, reviewer_identity, body.selected_attributes, body.review_notes
        )
    except ReviewConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return review


@router.post(
    "/reviews/unmerge/{golden_customer_id}",
    summary="Unmerge a golden customer into individual records",
)
async def unmerge(
    golden_customer_id: str = Path(..., description="GOLD-NNNNNN identifier to split"),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Unmerges a golden customer into separate single-record golden customers per PRD §7.4 (ADMIN only)."""
    try:
        new_ids = await unmerge_golden_customer(db, golden_customer_id, actor=current_user.username)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {
        "message": f"Successfully unmerged {golden_customer_id}",
        "golden_customer_id": golden_customer_id,
        "new_golden_customer_ids": new_ids,
    }


# ── Helper functions ─────────────────────────────────────────────


def _build_source_summary(rec: SourceRecord) -> SourceRecordSummary:
    """Build a SourceRecordSummary from an ORM model."""
    return SourceRecordSummary(
        id=rec.id,
        source_system=rec.source_system.value if rec.source_system else None,
        source_record_id=rec.source_record_id,
        original_name=rec.original_name,
        normalized_name=rec.normalized_name,
        original_dob=rec.original_dob,
        normalized_dob=rec.normalized_dob,
        original_mobile=rec.original_mobile,
        normalized_mobile=rec.normalized_mobile,
        original_email=rec.original_email,
        normalized_email=rec.normalized_email,
        original_pan=rec.original_pan,
        normalized_pan=rec.normalized_pan,
        original_city=rec.original_city,
        normalized_city=rec.normalized_city,
        segment=rec.segment,
        product_type=rec.product_type,
        balance_aum=float(rec.balance_aum) if rec.balance_aum is not None else None,
        relationship_value=float(rec.relationship_value) if rec.relationship_value is not None else None,
    )


async def _find_golden_for_record(
    db: AsyncSession, source_record_id: int
) -> Optional[GoldenCustomerSummary]:
    """Find golden customer linked to a source record and return summary."""
    result = await db.execute(
        select(IdentityLink)
        .where(IdentityLink.source_record_id == source_record_id)
        .where(IdentityLink.status == LinkStatus.MATCH)
    )
    link = result.scalars().first()
    if not link:
        return None

    golden_result = await db.execute(
        select(GoldenCustomer)
        .where(GoldenCustomer.golden_customer_id == link.golden_customer_id)
    )
    golden = golden_result.scalars().first()
    if not golden:
        return None

    return GoldenCustomerSummary(
        golden_customer_id=golden.golden_customer_id,
        canonical_name=golden.canonical_name,
        status=golden.status.value if golden.status else "ACTIVE",
        source_record_ids=golden.source_record_ids or [],
    )
