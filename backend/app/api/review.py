from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.api.deps import get_db, RoleChecker
from app.db.models.review_queue import ReviewQueueItem, ReviewStatus
from app.db.models.identity_edge import IdentityEdge
from app.db.models.source_record import SourceRecord
from app.db.models.audit import AuditLog
from app.db.models.user import User

router = APIRouter()

manager_admin = RoleChecker(["ADMIN", "MANAGER"])


@router.get("/queue")
def list_review_queue(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(manager_admin),
):
    """List review queue items. Manager/Admin only with team scoping for Managers."""
    from app.db.models.user import UserRole
    from sqlalchemy import or_
    
    query = db.query(ReviewQueueItem)

    if current_user.role == UserRole.MANAGER:
        team_rm_ids = [u.id for u in db.query(User.id).filter(User.team_id == current_user.team_id).all()]
        if team_rm_ids:
            query = query.join(
                SourceRecord,
                or_(
                    ReviewQueueItem.source_record_a_id == SourceRecord.id,
                    ReviewQueueItem.source_record_b_id == SourceRecord.id
                )
            ).filter(SourceRecord.assigned_rm_id.in_(team_rm_ids)).distinct()
        else:
            # Manager with no team members shouldn't see anything
            query = query.filter(ReviewQueueItem.id == -1)

    if status:
        query = query.filter(ReviewQueueItem.status == status)

    total = query.count()
    items = query.order_by(ReviewQueueItem.created_at.desc()).offset(skip).limit(limit).all()

    # Enrich with source record details
    result = []
    for item in items:
        record_a = db.query(SourceRecord).filter(SourceRecord.id == item.source_record_a_id).first()
        record_b = db.query(SourceRecord).filter(SourceRecord.id == item.source_record_b_id).first()

        result.append({
            "id": item.id,
            "status": item.status.value if hasattr(item.status, 'value') else str(item.status),
            "match_score": item.match_score,
            "ai_suggestions": item.ai_suggestions,
            "created_at": str(item.created_at) if item.created_at else None,
            "record_a": {
                "id": record_a.id, "source_system": record_a.source_system,
                "name": record_a.name, "pan": record_a.pan,
                "mobile": record_a.mobile, "email": record_a.email,
                "city": record_a.city,
            } if record_a else None,
            "record_b": {
                "id": record_b.id, "source_system": record_b.source_system,
                "name": record_b.name, "pan": record_b.pan,
                "mobile": record_b.mobile, "email": record_b.email,
                "city": record_b.city,
            } if record_b else None,
        })

    return {"total": total, "items": result}


@router.get("/{review_id}")
def get_review_item(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(manager_admin),
):
    """Get detailed review item with source records."""
    item = db.query(ReviewQueueItem).filter(ReviewQueueItem.id == review_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")

    record_a = db.query(SourceRecord).filter(SourceRecord.id == item.source_record_a_id).first()
    record_b = db.query(SourceRecord).filter(SourceRecord.id == item.source_record_b_id).first()

    return {
        "review_item": item,
        "record_a": record_a,
        "record_b": record_b,
    }


@router.post("/{review_id}/approve")
def approve_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(manager_admin),
):
    """Approve a merge. Updates the review item status and creates audit entry."""
    item = db.query(ReviewQueueItem).filter(ReviewQueueItem.id == review_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")

    if item.status != ReviewStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Item is already {item.status.value}")

    item.status = ReviewStatus.APPROVED
    item.resolved_by_id = current_user.id
    item.resolved_at = datetime.now(timezone.utc)

    # Audit log
    audit = AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        action_type="MERGE_APPROVE",
        entity_type="ReviewQueueItem",
        entity_id=str(review_id),
        description=f"Approved merge of records {item.source_record_a_id} and {item.source_record_b_id}",
    )
    db.add(audit)
    db.commit()

    return {"message": "Merge approved", "review_id": review_id}


@router.post("/{review_id}/reject")
def reject_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(manager_admin),
):
    """Reject a merge. Keeps records separate."""
    item = db.query(ReviewQueueItem).filter(ReviewQueueItem.id == review_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")

    if item.status != ReviewStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Item is already {item.status.value}")

    item.status = ReviewStatus.REJECTED
    item.resolved_by_id = current_user.id
    item.resolved_at = datetime.now(timezone.utc)

    # Audit log
    audit = AuditLog(
        actor_id=current_user.id,
        actor_role=current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        action_type="MERGE_REJECT",
        entity_type="ReviewQueueItem",
        entity_id=str(review_id),
        description=f"Rejected merge of records {item.source_record_a_id} and {item.source_record_b_id}",
    )
    db.add(audit)
    db.commit()

    return {"message": "Merge rejected", "review_id": review_id}
