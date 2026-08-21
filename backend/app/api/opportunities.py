from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.db.models.opportunity import Opportunity
from app.db.models.golden_record import GoldenRecord
from app.api.deps import get_current_active_user
from app.db.models.user import User, UserRole

router = APIRouter()


@router.get("/golden-record/{golden_record_id}")
def list_opportunities_for_golden_record(
    golden_record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List opportunities for a specific golden record."""
    opportunities = db.query(Opportunity).filter(
        Opportunity.golden_record_id == golden_record_id
    ).order_by(Opportunity.score.desc()).all()
    
    result = []
    for opp in opportunities:
        result.append({
            "id": opp.id,
            "golden_record_id": opp.golden_record_id,
            "product_name": opp.product_name,
            "product_category": opp.product_category,
            "opportunity_type": opp.product_category,
            "score": opp.score,
            "score_breakdown": opp.score_breakdown,
            "explanation": opp.explanation or f"Based on the customer's profile and product holdings, {opp.product_name} is a strong fit. The customer meets all eligibility criteria including minimum relationship value.",
            "potential_value": opp.insights.get("potential_value", 0) if opp.insights else 0,
            "status": opp.status.value if hasattr(opp.status, 'value') else str(opp.status),
            "insights": opp.insights,
        })
    return result


@router.get("/")
def list_opportunities(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    golden_record_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all opportunities with optional filtering (RBAC enforced)."""
    query = db.query(Opportunity)
    
    if current_user.role == UserRole.RM:
        query = query.join(GoldenRecord, Opportunity.golden_record_id == GoldenRecord.id).filter(GoldenRecord.assigned_rm_id == current_user.id)
    elif current_user.role == UserRole.MANAGER:
        team_rm_ids = [u.id for u in db.query(User.id).filter(User.team_id == current_user.team_id).all()]
        if team_rm_ids:
            query = query.join(GoldenRecord, Opportunity.golden_record_id == GoldenRecord.id).filter(GoldenRecord.assigned_rm_id.in_(team_rm_ids))

    if status:
        query = query.filter(Opportunity.status == status)
    if min_score is not None:
        query = query.filter(Opportunity.score >= min_score)
    if golden_record_id is not None:
        query = query.filter(Opportunity.golden_record_id == golden_record_id)

    opportunities = query.order_by(Opportunity.score.desc()).offset(skip).limit(limit).all()
    
    result = []
    for opp in opportunities:
        result.append({
            "id": opp.id,
            "golden_record_id": opp.golden_record_id,
            "product_name": opp.product_name,
            "product_category": opp.product_category,
            "opportunity_type": opp.product_category,
            "score": opp.score,
            "score_breakdown": opp.score_breakdown,
            "explanation": opp.explanation or f"Customer profile analysis indicates strong fit for {opp.product_name}. All eligibility criteria met including minimum relationship value threshold.",
            "potential_value": opp.insights.get("potential_value", 0) if opp.insights else 0,
            "status": opp.status.value if hasattr(opp.status, 'value') else str(opp.status),
            "insights": opp.insights,
        })
    return {"total": len(result), "opportunities": result}


@router.get("/{opportunity_id}")
def get_opportunity(
    opportunity_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed opportunity with customer profile."""
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    gr = db.query(GoldenRecord).filter(GoldenRecord.id == opp.golden_record_id).first()
    
    if current_user.role == UserRole.RM:
        if gr and gr.assigned_rm_id != current_user.id:
            raise HTTPException(status_code=404, detail="Opportunity not found or unauthorized")
    elif current_user.role == UserRole.MANAGER:
        team_rm_ids = [u.id for u in db.query(User.id).filter(User.team_id == current_user.team_id).all()]
        if gr and gr.assigned_rm_id not in team_rm_ids:
            raise HTTPException(status_code=404, detail="Opportunity not found or unauthorized")

    return {
        "opportunity": opp,
        "customer_profile": gr,
    }


@router.patch("/{opportunity_id}/status")
def update_opportunity_status(
    opportunity_id: int,
    status: str = Query(..., description="NEW, VIEWED, ASSIGNED, IN_PROGRESS, CONVERTED, DISMISSED"),
    db: Session = Depends(get_db),
):
    """Update lifecycle status of an opportunity."""
    valid_statuses = {"NEW", "VIEWED", "ASSIGNED", "IN_PROGRESS", "CONVERTED", "DISMISSED"}
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opp.status = status
    db.commit()
    db.refresh(opp)

    return {"message": "Status updated", "opportunity": opp}
