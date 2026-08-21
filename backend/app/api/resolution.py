from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.api.deps import get_db, RoleChecker, get_current_active_user
from app.db.models.user import User, UserRole
from app.core.masking import mask_pan, mask_email, mask_mobile

from app.services.matching.deterministic import run_deterministic_matching
from app.services.matching.probabilistic import run_probabilistic_matching
from app.services.matching.semantic import run_semantic_matching
from app.services.matching.graph_clustering import run_graph_clustering
from app.services.golden_record_builder import build_golden_records
from app.services.opportunity_engine import generate_opportunities
from app.db.models.golden_record import GoldenRecord

router = APIRouter()

# Role definitions
allow_admin = RoleChecker(["ADMIN"])
allow_all_roles = RoleChecker(["ADMIN", "MANAGER", "RM", "CREDIT_APPROVER"])

@router.post("/run", dependencies=[Depends(allow_admin)])
def run_resolution_pipeline(db: Session = Depends(get_db)):
    """
    Executes the full 3-phase matching and golden record builder pipeline.
    Requires ADMIN privileges.
    """
    from app.db.models.opportunity import Opportunity
    from app.db.models.review_queue import ReviewQueueItem
    from app.db.models.identity_edge import IdentityEdge
    from app.db.models.source_record import SourceRecord

    # Cleanup existing generated data to allow re-runs
    db.query(Opportunity).delete()
    db.query(ReviewQueueItem).delete()
    db.query(IdentityEdge).delete()
    db.query(SourceRecord).update({SourceRecord.golden_record_id: None})
    db.query(GoldenRecord).delete()
    db.commit()

    # 1. Matching Engines (Phase 1, 2, 3 of Entity Resolution)
    det_edges = run_deterministic_matching(db)
    prob_edges = run_probabilistic_matching(db)
    sem_edges = run_semantic_matching(db)
    
    total_edges = det_edges + prob_edges + sem_edges
    
    # 2. Graph Clustering (Transitive Closure)
    clusters = run_graph_clustering(db)
    
    
    # 3. Golden Record Builder (Survivorship)
    golden_created = build_golden_records(db, clusters)
    
    # 4. Opportunity Engine
    opportunities_created = generate_opportunities(db)
    
    return {
        "status": "success",
        "message": "Resolution pipeline completed successfully.",
        "metrics": {
            "edges_created": {
                "deterministic": det_edges,
                "probabilistic": prob_edges,
                "semantic": sem_edges,
                "total": total_edges
            },
            "clusters_found": len(clusters),
            "golden_records_created": golden_created,
            "opportunities_created": opportunities_created
        }
    }

@router.get("/golden-records", dependencies=[Depends(allow_all_roles)])
def get_golden_records(
    skip: int = 0, 
    limit: int = 50, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List golden records with basic info (RBAC enforced)."""
    query = db.query(GoldenRecord)
    
    # Data-level Authorization: RM only sees their assigned records
    if current_user.role == UserRole.RM:
        query = query.filter(GoldenRecord.assigned_rm_id == current_user.id)
        
    records = query.offset(skip).limit(limit).all()
    
    result = []
    for r in records:
        result.append({
            "id": r.id,
            "name": r.name,
            "city": r.city,
            "segment": r.segment,
            "total_relationship_value": r.total_relationship_value,
            "products_held": r.products_held,
            "source_systems": r.source_systems,
            "source_record_count": r.source_record_count,
            "match_confidence": r.match_confidence,
            "confidence_breakdown": r.confidence_breakdown,
            "created_at": r.created_at,
            "updated_at": r.updated_at
        })
    return result

@router.get("/golden-records/{record_id}", dependencies=[Depends(allow_all_roles)])
def get_golden_record(
    record_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed golden record including provenance and source records."""
    query = db.query(GoldenRecord).options(joinedload(GoldenRecord.source_records)).filter(GoldenRecord.id == record_id)
    
    if current_user.role == UserRole.RM:
        query = query.filter(GoldenRecord.assigned_rm_id == current_user.id)
        
    record = query.first()
    if not record:
        raise HTTPException(status_code=404, detail="Golden Record not found or unauthorized")
    
    source_records_list = []
    for sr in record.source_records:
        source_records_list.append({
            "id": sr.id,
            "source_system": sr.source_system,
            "name": sr.name,
            "dob": sr.dob,
            "pan": mask_pan(sr.pan, current_user.role),
            "email": mask_email(sr.email, current_user.role),
            "mobile": mask_mobile(sr.mobile, current_user.role),
            "city": sr.city,
            "segment": sr.segment,
            "account_value": sr.account_value,
            "products": sr.products,
        })
        
    return {
        "id": record.id,
        "name": record.name,
        "pan": mask_pan(record.pan, current_user.role),
        "mobile": mask_mobile(record.mobile, current_user.role),
        "email": mask_email(record.email, current_user.role),
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
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "source_records": source_records_list
    }


@router.get("/edges", dependencies=[Depends(allow_all_roles)])
def get_identity_edges(
    skip: int = 0, 
    limit: int = 200, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get identity edges for graph visualization with RBAC scoping."""
    from app.db.models.identity_edge import IdentityEdge
    from app.db.models.source_record import SourceRecord
    from sqlalchemy import or_

    query = db.query(IdentityEdge)

    if current_user.role == UserRole.RM:
        # RM can only see edges if they own at least one of the connected source records
        query = query.join(
            SourceRecord,
            or_(
                IdentityEdge.source_record_a_id == SourceRecord.id,
                IdentityEdge.source_record_b_id == SourceRecord.id
            )
        ).filter(SourceRecord.assigned_rm_id == current_user.id).distinct()
    elif current_user.role == UserRole.MANAGER:
        # Manager can only see edges if team members own at least one source record
        team_rm_ids = [u.id for u in db.query(User.id).filter(User.team_id == current_user.team_id).all()]
        if team_rm_ids:
            query = query.join(
                SourceRecord,
                or_(
                    IdentityEdge.source_record_a_id == SourceRecord.id,
                    IdentityEdge.source_record_b_id == SourceRecord.id
                )
            ).filter(SourceRecord.assigned_rm_id.in_(team_rm_ids)).distinct()

    edges = query.offset(skip).limit(limit).all()
    
    result = []
    for e in edges:
        result.append({
            "id": e.id,
            "source_a_id": e.source_record_a_id,
            "source_b_id": e.source_record_b_id,
            "match_phase": e.match_phase,
            "confidence_score": e.confidence,
        })
    return result

