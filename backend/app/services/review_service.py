"""
Nexus360 — Review Service.

Handles approval, rejection, manual merges, and unmerging of review cases.
Integrates with Audit log and Golden Customer service. Aligned with PRD §7.4.

Fixes applied (per audit):
- MatchDecision.decision updated on approve (→ MATCH) and reject (→ NON_MATCH)
- Concurrency protection via SELECT … FOR UPDATE row-level locking
- Manual merge attribute whitelist — rejects arbitrary setattr injection
- attribute_provenance updated after manual merge overrides
- IdentityLink.ai_explanation populated
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review_case import ReviewCase, ReviewStatus
from app.models.match_decision import MatchDecision, Decision
from app.models.source_record import SourceRecord
from app.models.identity_link import IdentityLink, MatchMethod, LinkStatus
from app.models.golden_customer import GoldenCustomer, GoldenCustomerStatus
from app.models.attribute_history import AttributeHistory
from app.models.audit_log import AuditAction

from app.services.golden_record_service import (
    create_golden_customer,
    link_to_golden,
    find_golden_by_source_record,
    recalculate_golden_customer,
)
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)

# ── Whitelist of canonical attributes reviewers may override ───────
ALLOWED_MERGE_ATTRIBUTES = frozenset({
    "canonical_name",
    "canonical_dob",
    "canonical_mobile",
    "canonical_email",
    "canonical_pan",
    "canonical_city",
    "canonical_segment",
})


class ReviewConflictError(Exception):
    """Raised when a review case has already been processed by another reviewer."""
    pass


# ── Helper: row-level lock + status check ─────────────────────────
async def _get_and_lock_pending_review(
    db: AsyncSession,
    review_id: int,
) -> ReviewCase:
    """
    Atomically fetch and lock a ReviewCase row using SELECT … FOR UPDATE.
    Raises ValueError if not found, ReviewConflictError if not PENDING.
    """
    stmt = (
        select(ReviewCase)
        .where(ReviewCase.id == review_id)
        .with_for_update()
    )
    result = await db.execute(stmt)
    review = result.scalars().first()

    if not review:
        raise ValueError(f"Review case {review_id} not found")

    if review.status != ReviewStatus.PENDING:
        raise ReviewConflictError(
            f"Review {review_id} is already {review.status.value}. "
            f"It may have been processed by another reviewer."
        )

    return review


async def approve_review(
    db: AsyncSession,
    review_id: int,
    reviewer: str,
    notes: str | None = None,
) -> ReviewCase:
    """Approve a review case — marks the pair as a confirmed MATCH."""
    review = await _get_and_lock_pending_review(db, review_id)

    decision = await db.get(MatchDecision, review.match_decision_id)
    rec_a = await db.get(SourceRecord, decision.record_a_id)
    rec_b = await db.get(SourceRecord, decision.record_b_id)

    golden_a = await find_golden_by_source_record(db, rec_a.id)
    golden_b = await find_golden_by_source_record(db, rec_b.id)

    ai_explanation = f"Approved by {reviewer}. Records confirmed as same identity."

    if golden_a:
        link = await link_to_golden(db, rec_b, golden_a, MatchMethod.MANUAL, decision.final_score)
        link.ai_explanation = ai_explanation
        target_golden = golden_a
    elif golden_b:
        link = await link_to_golden(db, rec_a, golden_b, MatchMethod.MANUAL, decision.final_score)
        link.ai_explanation = ai_explanation
        target_golden = golden_b
    else:
        golden = await create_golden_customer(db, rec_a, MatchMethod.MANUAL, confidence=decision.final_score)
        link = await link_to_golden(db, rec_b, golden, MatchMethod.MANUAL, confidence=decision.final_score)
        link.ai_explanation = ai_explanation
        target_golden = golden

    # ── FIX: Update MatchDecision.decision to MATCH ──────────────
    decision.decision = Decision.MATCH

    # ── Update ReviewCase ────────────────────────────────────────
    review.status = ReviewStatus.APPROVED
    review.reviewer = reviewer
    review.review_notes = notes
    review.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await log_action(
        db,
        action=AuditAction.MERGE_APPROVE,
        actor_username=reviewer,
        actor_role="Manager",
        entity_type="ReviewCase",
        entity_id=str(review_id),
        old_value={"decision": "REVIEW"},
        new_value={
            "decision": "MATCH",
            "golden_customer_id": target_golden.golden_customer_id,
            "notes": notes,
        },
    )

    await db.flush()
    logger.info("Review %d approved by %s", review_id, reviewer)
    return review


async def reject_review(
    db: AsyncSession,
    review_id: int,
    reviewer: str,
    notes: str | None = None,
) -> ReviewCase:
    """Reject a review case — the pair is confirmed as NON_MATCH."""
    review = await _get_and_lock_pending_review(db, review_id)

    decision = await db.get(MatchDecision, review.match_decision_id)
    rec_a = await db.get(SourceRecord, decision.record_a_id)
    rec_b = await db.get(SourceRecord, decision.record_b_id)

    golden_a = await find_golden_by_source_record(db, rec_a.id)
    golden_b = await find_golden_by_source_record(db, rec_b.id)

    if not golden_a:
        await create_golden_customer(db, rec_a, MatchMethod.MANUAL, confidence=1.0)
    if not golden_b:
        await create_golden_customer(db, rec_b, MatchMethod.MANUAL, confidence=1.0)

    # ── FIX: Update MatchDecision.decision to NON_MATCH ──────────
    decision.decision = Decision.NON_MATCH

    review.status = ReviewStatus.REJECTED
    review.reviewer = reviewer
    review.review_notes = notes
    review.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await log_action(
        db,
        action=AuditAction.MERGE_REJECT,
        actor_username=reviewer,
        actor_role="Manager",
        entity_type="ReviewCase",
        entity_id=str(review_id),
        old_value={"decision": "REVIEW"},
        new_value={"decision": "NON_MATCH", "notes": notes},
    )

    await db.flush()
    logger.info("Review %d rejected by %s", review_id, reviewer)
    return review


async def manual_merge_review(
    db: AsyncSession,
    review_id: int,
    reviewer: str,
    selected_attributes: Dict[str, Any],
    notes: Optional[str] = None,
) -> ReviewCase:
    """
    Manual merge with custom selected field values per PRD §7.4.

    Only fields in ALLOWED_MERGE_ATTRIBUTES can be overridden.
    Updates attribute_provenance and records AttributeHistory.
    """
    # ── FIX: Validate attribute names against whitelist ───────────
    invalid_keys = set(selected_attributes.keys()) - ALLOWED_MERGE_ATTRIBUTES
    if invalid_keys:
        raise ValueError(
            f"Invalid attribute(s) for manual merge: {sorted(invalid_keys)}. "
            f"Allowed: {sorted(ALLOWED_MERGE_ATTRIBUTES)}"
        )

    review = await approve_review(db, review_id, reviewer, notes)

    decision = await db.get(MatchDecision, review.match_decision_id)
    rec_a = await db.get(SourceRecord, decision.record_a_id)
    golden = await find_golden_by_source_record(db, rec_a.id)

    if golden:
        provenance = dict(golden.attribute_provenance or {})
        now_iso = datetime.now(timezone.utc).isoformat()

        for attr_name, value in selected_attributes.items():
            if value is None:
                continue

            old_val = getattr(golden, attr_name, None)
            old_str = str(old_val) if old_val is not None else None
            new_str = str(value)

            # Apply the override
            setattr(golden, attr_name, value)

            # ── FIX: Update provenance to reflect manual selection ─
            provenance[attr_name] = {
                "value": new_str,
                "source": "MANUAL_MERGE",
                "rule": "MANUAL_MERGE",
                "timestamp": now_iso,
                "reviewer": reviewer,
            }

            # Record change history
            hist = AttributeHistory(
                golden_customer_id=golden.golden_customer_id,
                attribute_name=attr_name,
                old_value=old_str,
                new_value=new_str,
                selected_source="MANUAL_MERGE",
                change_reason=f"Manual selection by {reviewer}: {notes or ''}",
            )
            db.add(hist)

        golden.attribute_provenance = provenance
        await recalculate_golden_customer(db, golden)

    await log_action(
        db,
        action=AuditAction.MANUAL_MERGE,
        actor_username=reviewer,
        actor_role="Admin",
        entity_type="ReviewCase",
        entity_id=str(review_id),
        new_value={"selected_attributes": selected_attributes, "notes": notes},
    )

    return review


async def unmerge_golden_customer(
    db: AsyncSession,
    golden_customer_id: str,
    actor: str = "Admin",
) -> List[str]:
    """
    Unmerges a golden customer into separate single-record golden customers per PRD §7.4.
    Deactivates original golden customer (UNDER_REVIEW) and clears stale active pointers.
    """
    res = await db.execute(select(GoldenCustomer).where(GoldenCustomer.golden_customer_id == golden_customer_id))
    golden = res.scalars().first()

    if not golden:
        raise ValueError(f"Golden customer '{golden_customer_id}' not found")

    links_res = await db.execute(
        select(IdentityLink).where(IdentityLink.golden_customer_id == golden_customer_id)
    )
    links = links_res.scalars().all()

    # Deactivate original golden customer to prevent stale active customer queries
    golden.status = GoldenCustomerStatus.UNDER_REVIEW
    golden.source_record_ids = []
    golden.products_held = []
    golden.total_relationship_value = Decimal("0.0")

    new_golden_ids = []
    for link in links:
        link.status = LinkStatus.NON_MATCH
        src = await db.get(SourceRecord, link.source_record_id)
        if src:
            new_g = await create_golden_customer(db, src, MatchMethod.MANUAL, confidence=1.0)
            new_golden_ids.append(new_g.golden_customer_id)

    await log_action(
        db,
        action=AuditAction.UNMERGE,
        actor_username=actor,
        actor_role="Admin",
        entity_type="GoldenCustomer",
        entity_id=golden_customer_id,
        new_value={"result_golden_ids": new_golden_ids},
    )

    await db.flush()
    logger.info("Unmerged golden customer %s into %s", golden_customer_id, new_golden_ids)
    return new_golden_ids


async def _get_review(db: AsyncSession, review_id: int) -> ReviewCase:
    """Fetch a review case or raise."""
    review = await db.get(ReviewCase, review_id)
    if not review:
        raise ValueError(f"Review case {review_id} not found")
    return review
