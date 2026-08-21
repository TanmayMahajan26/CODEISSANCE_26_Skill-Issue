from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, get_current_active_user
from app.db.models.golden_record import GoldenRecord
from app.db.models.source_record import SourceRecord
from app.db.models.identity_edge import IdentityEdge
from app.db.models.opportunity import Opportunity
from app.db.models.review_queue import ReviewQueueItem, ReviewStatus
from app.db.models.audit import AuditLog
from app.db.models.user import User, UserRole

router = APIRouter()


def _apply_rm_scope(query, model, current_user: User):
    """Apply data-level authorization scoping based on user role."""
    if current_user.role == UserRole.RM:
        # RM sees only their assigned records
        query = query.filter(model.assigned_rm_id == current_user.id)
    elif current_user.role == UserRole.MANAGER:
        # Manager sees all records for their team
        # (all RMs in the same team_id)
        from app.db.models.user import User as UserModel
        team_rm_ids = [u.id for u in
                       Session.object_session(current_user).query(UserModel.id).filter(
                           UserModel.team_id == current_user.team_id
                       ).all()]
        if team_rm_ids:
            query = query.filter(model.assigned_rm_id.in_(team_rm_ids))
    # ADMIN sees everything — no filter
    return query


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Aggregated dashboard statistics for the main dashboard page (RBAC scoped)."""

    # Build scoped queries
    sr_query = db.query(func.count(SourceRecord.id))
    gr_query = db.query(func.count(GoldenRecord.id))
    trv_query = db.query(func.sum(GoldenRecord.total_relationship_value))
    opp_query = db.query(func.count(Opportunity.id))

    if current_user.role == UserRole.RM:
        sr_query = sr_query.filter(SourceRecord.assigned_rm_id == current_user.id)
        gr_query = gr_query.filter(GoldenRecord.assigned_rm_id == current_user.id)
        trv_query = trv_query.filter(GoldenRecord.assigned_rm_id == current_user.id)
        opp_query = opp_query.join(GoldenRecord, Opportunity.golden_record_id == GoldenRecord.id).filter(
            GoldenRecord.assigned_rm_id == current_user.id
        )
    elif current_user.role == UserRole.MANAGER:
        team_rm_ids = [u.id for u in db.query(User.id).filter(User.team_id == current_user.team_id).all()]
        if team_rm_ids:
            sr_query = sr_query.filter(SourceRecord.assigned_rm_id.in_(team_rm_ids))
            gr_query = gr_query.filter(GoldenRecord.assigned_rm_id.in_(team_rm_ids))
            trv_query = trv_query.filter(GoldenRecord.assigned_rm_id.in_(team_rm_ids))
            opp_query = opp_query.join(GoldenRecord, Opportunity.golden_record_id == GoldenRecord.id).filter(
                GoldenRecord.assigned_rm_id.in_(team_rm_ids)
            )

    total_source_records = sr_query.scalar() or 0
    total_golden_records = gr_query.scalar() or 0
    total_edges = db.query(func.count(IdentityEdge.id)).scalar() or 0
    total_opportunities = opp_query.scalar() or 0
    pending_reviews = db.query(func.count(ReviewQueueItem.id)).filter(
        ReviewQueueItem.status == ReviewStatus.PENDING
    ).scalar() or 0

    # Total relationship value
    total_trv = trv_query.scalar() or 0

    # Edge breakdown by match phase
    edge_breakdown = {}
    edge_groups = db.query(
        IdentityEdge.match_phase,
        func.count(IdentityEdge.id)
    ).group_by(IdentityEdge.match_phase).all()
    for phase, count in edge_groups:
        edge_breakdown[phase] = count

    # Opportunity breakdown by status (scoped)
    opp_breakdown = {}
    opp_status_q = db.query(
        Opportunity.status,
        func.count(Opportunity.id)
    )
    if current_user.role == UserRole.RM:
        opp_status_q = opp_status_q.join(GoldenRecord, Opportunity.golden_record_id == GoldenRecord.id).filter(
            GoldenRecord.assigned_rm_id == current_user.id
        )
    elif current_user.role == UserRole.MANAGER:
        team_rm_ids_2 = [u.id for u in db.query(User.id).filter(User.team_id == current_user.team_id).all()]
        if team_rm_ids_2:
            opp_status_q = opp_status_q.join(GoldenRecord, Opportunity.golden_record_id == GoldenRecord.id).filter(
                GoldenRecord.assigned_rm_id.in_(team_rm_ids_2)
            )
    opp_groups = opp_status_q.group_by(Opportunity.status).all()
    for status_val, count in opp_groups:
        status_key = status_val.value if hasattr(status_val, 'value') else str(status_val)
        opp_breakdown[status_key] = count

    # Opportunity breakdown by product category
    product_breakdown = {}
    product_groups = db.query(
        Opportunity.product_category,
        func.count(Opportunity.id)
    ).group_by(Opportunity.product_category).all()
    for cat, count in product_groups:
        product_breakdown[cat or "Unknown"] = count

    # Source system distribution (scoped)
    sys_q = db.query(
        SourceRecord.source_system,
        func.count(SourceRecord.id)
    )
    if current_user.role == UserRole.RM:
        sys_q = sys_q.filter(SourceRecord.assigned_rm_id == current_user.id)
    elif current_user.role == UserRole.MANAGER:
        team_rm_ids_3 = [u.id for u in db.query(User.id).filter(User.team_id == current_user.team_id).all()]
        if team_rm_ids_3:
            sys_q = sys_q.filter(SourceRecord.assigned_rm_id.in_(team_rm_ids_3))
    system_breakdown = {}
    system_groups = sys_q.group_by(SourceRecord.source_system).all()
    for sys_name, count in system_groups:
        system_breakdown[sys_name] = count

    # Recent audit activity count
    recent_audit_count = db.query(func.count(AuditLog.id)).scalar() or 0

    return {
        "overview": {
            "total_source_records": total_source_records,
            "total_golden_records": total_golden_records,
            "total_identity_edges": total_edges,
            "total_opportunities": total_opportunities,
            "pending_reviews": pending_reviews,
            "total_relationship_value": round(total_trv, 2),
            "deduplication_ratio": round(total_source_records / max(total_golden_records, 1), 2),
        },
        "edge_breakdown": edge_breakdown,
        "opportunity_by_status": opp_breakdown,
        "opportunity_by_product": product_breakdown,
        "source_system_distribution": system_breakdown,
        "audit_event_count": recent_audit_count,
    }

