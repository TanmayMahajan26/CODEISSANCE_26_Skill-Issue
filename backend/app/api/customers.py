from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.db.session import get_db
from app.db.models.golden_record import GoldenRecord
from app.db.models.opportunity import Opportunity
from app.db.models.source_record import SourceRecord
from app.db.models.user import User, UserRole
from app.api.deps import get_current_active_user

router = APIRouter()


@router.get("/")
def list_customers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    city: Optional[str] = None,
    segment: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all Golden Records with optional search/filter and RBAC scoping."""
    query = db.query(GoldenRecord)

    # Apply data-level authorization
    if current_user.role == UserRole.RM:
        query = query.filter(GoldenRecord.assigned_rm_id == current_user.id)
    elif current_user.role == UserRole.MANAGER:
        team_rm_ids = [u.id for u in db.query(User.id).filter(User.team_id == current_user.team_id).all()]
        if team_rm_ids:
            query = query.filter(GoldenRecord.assigned_rm_id.in_(team_rm_ids))

    if search:
        query = query.filter(GoldenRecord.name.ilike(f"%{search}%"))
    if city:
        query = query.filter(GoldenRecord.city.ilike(f"%{city}%"))
    if segment:
        query = query.filter(GoldenRecord.segment == segment)

    total = query.count()
    records = query.offset(skip).limit(limit).all()
    return {"total": total, "customers": records}


@router.get("/{golden_id}")
def get_customer(
    golden_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Customer 360 view: Golden Record + source lineage + opportunities.
    """
    query = db.query(GoldenRecord).options(joinedload(GoldenRecord.source_records)).filter(GoldenRecord.id == golden_id)
    
    # Apply data-level authorization
    if current_user.role == UserRole.RM:
        query = query.filter(GoldenRecord.assigned_rm_id == current_user.id)
    elif current_user.role == UserRole.MANAGER:
        team_rm_ids = [u.id for u in db.query(User.id).filter(User.team_id == current_user.team_id).all()]
        if team_rm_ids:
            query = query.filter(GoldenRecord.assigned_rm_id.in_(team_rm_ids))

    record = query.first()

    if not record:
        raise HTTPException(status_code=404, detail="Customer not found or unauthorized")

    opportunities = db.query(Opportunity).filter(
        Opportunity.golden_record_id == golden_id
    ).order_by(Opportunity.score.desc()).all()

    # Build source lineage with raw vs normalized comparison
    source_lineage = []
    for sr in record.source_records:
        source_lineage.append({
            "id": sr.id,
            "source_system": sr.source_system,
            "source_id": sr.source_id,
            "raw_name": sr.raw_name,
            "raw_pan": sr.raw_pan,
            "raw_mobile": sr.raw_mobile,
            "raw_email": sr.raw_email,
            "name": sr.name,
            "pan": sr.pan,
            "mobile": sr.mobile,
            "email": sr.email,
            "dob": str(sr.dob) if sr.dob else None,
            "city": sr.city,
            "segment": sr.segment,
            "account_value": sr.account_value,
            "products": sr.products,
        })

    return {
        "golden_record": {
            "id": record.id,
            "name": record.name,
            "pan": record.pan,
            "mobile": record.mobile,
            "email": record.email,
            "dob": str(record.dob) if record.dob else None,
            "city": record.city,
            "segment": record.segment,
            "total_relationship_value": record.total_relationship_value,
            "products_held": record.products_held,
            "source_systems": record.source_systems,
            "source_record_count": record.source_record_count,
            "match_confidence": record.match_confidence,
            "confidence_breakdown": record.confidence_breakdown,
            "provenance": record.provenance,
            "created_at": str(record.created_at) if record.created_at else None,
        },
        "source_lineage": source_lineage,
        "opportunities": opportunities,
    }
